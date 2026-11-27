import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models import Transaction, Customer, Account
from backend.schemas import SpendingResultObject, CalculationNotes
from backend.config import format_inr

class SpendingService:
    """
    Deterministic Spending & Cash-Flow Engine.
    Computes all totals, breakdowns, MoM variance, subscriptions, and forecasts.
    """

    CATEGORIES = [
        "Food & Dining", "Shopping", "Housing & Rent", "Utilities",
        "Transportation", "Entertainment", "Healthcare", "Investments", "Miscellaneous"
    ]

    CATEGORY_KEYWORDS = {
        "Food & Dining": ["swiggy", "zomato", "restaurant", "cafe", "starbucks", "mcdonald", "food", "dining", "domino", "blinkit", "zepto", "instamart"],
        "Shopping": ["amazon", "flipkart", "myntra", "zara", "retail", "croma", "reliance digital", "clothing", "h&m"],
        "Housing & Rent": ["rent", "maintenance", "society", "housing", "landlord"],
        "Utilities": ["electricity", "bescom", "tneb", "mahavitaran", "broadband", "airtel", "jio", "water bill", "gas", "cylinder"],
        "Transportation": ["uber", "ola", "metro", "petrol", "fuel", "hpcl", "bpcl", "fastag", "railway", "irctc"],
        "Entertainment": ["netflix", "prime video", "hotstar", "spotify", "bookmyshow", "pvr", "cinema", "gaming"],
        "Healthcare": ["apollo", "pharmacy", "1mg", "hospital", "clinic", "medplus", "doctor"],
        "Investments": ["zerodha", "groww", "sip", "mutual fund", "ppf", "nps", "etmoney"]
    }

    @classmethod
    def categorize_merchant(cls, merchant_name: str, description: Optional[str] = None) -> str:
        """Deterministic keyword categorizer."""
        text = f"{merchant_name} {description or ''}".lower()
        for cat, keywords in cls.CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return cat
        return "Miscellaneous"

    @classmethod
    def get_spending_summary(
        cls,
        db: Session,
        customer_id: int,
        category: Optional[str] = None,
        period: str = "current_month",
        reference_date: Optional[datetime.datetime] = None
    ) -> SpendingResultObject:
        ref = reference_date or datetime.datetime(2026, 11, 21)
        
        # Calculate window dates
        if period == "last_month":
            first_of_curr = datetime.datetime(ref.year, ref.month, 1)
            last_of_prev = first_of_curr - datetime.timedelta(days=1)
            start_date = datetime.datetime(last_of_prev.year, last_of_prev.month, 1)
            end_date = datetime.datetime(last_of_prev.year, last_of_prev.month, last_of_prev.day, 23, 59, 59)
            prev_start = datetime.datetime(start_date.year, start_date.month - 1 if start_date.month > 1 else 12, 1)
            prev_end = start_date - datetime.timedelta(seconds=1)
            window_label = f"1–{last_of_prev.day} {start_date.strftime('%b %Y')}"
        else: # default current_month
            start_date = datetime.datetime(ref.year, ref.month, 1)
            end_date = ref
            # compare to same day of previous month
            prev_month = ref.month - 1 if ref.month > 1 else 12
            prev_year = ref.year if ref.month > 1 else ref.year - 1
            prev_start = datetime.datetime(prev_year, prev_month, 1)
            prev_day = min(ref.day, 28)
            prev_end = datetime.datetime(prev_year, prev_month, prev_day, 23, 59, 59)
            window_label = f"1–{ref.day} {ref.strftime('%b %Y')}"

        query = db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= start_date,
            Transaction.timestamp <= end_date
        )

        filter_applied = {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }

        target_category = None
        if category and category.lower() not in ["all", "any", "total", "everything"]:
            # Fuzzy match category
            for standard_cat in cls.CATEGORIES:
                if category.lower() in standard_cat.lower() or standard_cat.lower() in category.lower():
                    target_category = standard_cat
                    break
            if not target_category:
                target_category = category.title()
            query = query.filter(Transaction.category.ilike(f"%{target_category}%"))
            filter_applied["category"] = target_category

        curr_txs = query.all()
        total_spent = sum(t.amount for t in curr_txs)
        tx_count = len(curr_txs)
        tx_ids = [t.id for t in curr_txs]

        # Prior month query for MoM calculation
        prev_query = db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= prev_start,
            Transaction.timestamp <= prev_end
        )
        if target_category:
            prev_query = prev_query.filter(Transaction.category.ilike(f"%{target_category}%"))
        prev_txs = prev_query.all()
        prev_spent = sum(t.amount for t in prev_txs)

        mom_change = ((total_spent - prev_spent) / prev_spent * 100.0) if prev_spent > 0 else 0.0

        # Top merchants breakdown
        merchant_map: Dict[str, float] = {}
        for t in curr_txs:
            merchant_map[t.merchant_name] = merchant_map.get(t.merchant_name, 0.0) + t.amount

        sorted_merchants = sorted(merchant_map.items(), key=lambda x: x[1], reverse=True)
        top_merchants = [
            {"name": name, "amount": round(amt, 2), "formatted_amount": format_inr(amt)}
            for name, amt in sorted_merchants[:5]
        ]

        # Category breakdown for all debits in the window
        all_curr_query = db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= start_date,
            Transaction.timestamp <= end_date
        )
        all_txs = all_curr_query.all()
        cat_map: Dict[str, float] = {}
        for t in all_txs:
            cat_map[t.category] = cat_map.get(t.category, 0.0) + t.amount
        total_all = sum(cat_map.values()) or 1.0

        category_breakdown = [
            {
                "category": cat,
                "amount": round(amt, 2),
                "formatted_amount": format_inr(amt),
                "percentage": round((amt / total_all) * 100, 1)
            }
            for cat, amt in sorted(cat_map.items(), key=lambda x: x[1], reverse=True)
        ]

        # Recurring items detection
        recurring_query = db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.is_recurring == True,
            Transaction.timestamp >= start_date
        ).all()
        recurring_items = [
            {
                "merchant": t.merchant_name,
                "category": t.category,
                "amount": round(t.amount, 2),
                "formatted_amount": format_inr(t.amount)
            }
            for t in recurring_query
        ]

        # Savings levers / opportunities
        savings_opportunities = []
        if total_spent > prev_spent and prev_spent > 0:
            savings_opportunities.append(f"Spending in {target_category or 'total'} is up by {abs(mom_change):.1f}% compared to last month.")
        if top_merchants:
            top_m = top_merchants[0]
            savings_opportunities.append(f"Top merchant is {top_m['name']} accounting for {top_m['formatted_amount']}.")
        if target_category and "food" in target_category.lower():
            dining_cut = total_spent * 0.20
            savings_opportunities.append(f"Trimming food deliveries by 20% would save {format_inr(dining_cut)} per month.")
        elif target_category and "shopping" in target_category.lower():
            shop_cut = total_spent * 0.15
            savings_opportunities.append(f"Adopting a 48-hour pause rule for non-essential shopping can save ~{format_inr(shop_cut)} monthly.")
        else:
            savings_opportunities.append("Review recurring digital subscriptions to eliminate underutilized services.")

        calc_notes = CalculationNotes(
            formula="SUM(Transaction.amount) WHERE customer_id = :id AND type = 'debit' AND timestamp BETWEEN :start AND :end",
            data_window=window_label,
            transaction_count=tx_count,
            filters_applied=filter_applied,
            breakdown={"total_spent": round(total_spent, 2), "prev_month_spent": round(prev_spent, 2), "mom_pct": round(mom_change, 2)},
            source_transaction_ids=tx_ids[:25],
            calculation_summary=f"Computed from {tx_count} verified transactions totaling {format_inr(total_spent)}."
        )

        return SpendingResultObject(
            customer_id=customer_id,
            category=target_category or "All Categories",
            period=period,
            data_window=window_label,
            total_spent=round(total_spent, 2),
            formatted_total_spent=format_inr(total_spent),
            transaction_count=tx_count,
            last_month_spent=round(prev_spent, 2),
            formatted_last_month_spent=format_inr(prev_spent),
            month_over_month_change_pct=round(mom_change, 1),
            top_merchants=top_merchants,
            category_breakdown=category_breakdown,
            recurring_items=recurring_items,
            savings_opportunities=savings_opportunities,
            calculation_notes=calc_notes
        )

    @classmethod
    def get_cashflow_forecast(cls, db: Session, customer_id: int) -> Dict[str, Any]:
        """Deterministic run-rate and cash-flow projection for remainder of month."""
        ref = datetime.datetime(2026, 11, 21)
        start_of_month = datetime.datetime(ref.year, ref.month, 1)
        days_passed = ref.day
        days_in_month = 30 # Nov has 30 days
        days_remaining = days_in_month - days_passed

        txs = db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= start_of_month,
            Transaction.timestamp <= ref
        ).all()
        spent_so_far = sum(t.amount for t in txs)
        daily_burn_rate = spent_so_far / max(days_passed, 1)
        projected_remaining_spend = daily_burn_rate * days_remaining
        projected_total = spent_so_far + projected_remaining_spend

        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        income = customer.monthly_income if customer else 75000.0
        projected_savings = income - projected_total

    @classmethod
    def check_repeated_transfer(
        cls,
        db: Session,
        customer_id: int,
        recipient_name: str,
        amount: float,
        window_hours: int = 72
    ) -> Dict[str, Any]:
        """
        Feature: Repeated transaction advisory.
        Alerts customer if they are transferring to the same person recently,
        BUT does NOT restrict or block them.
        """
        now = datetime.datetime.utcnow()
        cutoff = now - datetime.timedelta(hours=window_hours)
        clean_name = recipient_name.strip().lower()

        recent_matches = db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= cutoff,
            Transaction.merchant_name.ilike(f"%{clean_name}%")
        ).order_by(Transaction.timestamp.desc()).all()

        if recent_matches:
            last_tx = recent_matches[0]
            diff = now - last_tx.timestamp
            if diff.total_seconds() < 3600:
                time_ago = f"{int(diff.total_seconds() // 60)} minutes ago"
            elif diff.total_seconds() < 86400:
                time_ago = f"{int(diff.total_seconds() // 3600)} hours ago"
            else:
                time_ago = f"{int(diff.days)} day(s) ago"

            is_exact_amount = abs(last_tx.amount - amount) < 1.0

            return {
                "is_repeated": True,
                "is_restricted": False,  # CRITICAL: Never restricts the user!
                "alert_level": "WARNING",
                "message": (
                    f"⚠️ Repeated Transaction Alert: You already sent {format_inr(last_tx.amount)} "
                    f"to '{last_tx.merchant_name}' {time_ago}. "
                    f"{'Notice: The amount matches exactly.' if is_exact_amount else ''} "
                    "You may proceed if this transfer is intentional."
                ),
                "prior_transaction": {
                    "id": last_tx.id,
                    "recipient": last_tx.merchant_name,
                    "amount": last_tx.amount,
                    "formatted_amount": format_inr(last_tx.amount),
                    "timestamp": last_tx.timestamp.strftime("%d %b %Y, %I:%M %p"),
                    "time_ago": time_ago,
                    "channel": last_tx.channel
                }
            }

        return {
            "is_repeated": False,
            "is_restricted": False,
            "alert_level": "CLEAR",
            "message": "No recent duplicate payments detected for this recipient."
        }

    @classmethod
    def execute_transfer(
        cls,
        db: Session,
        customer_id: int,
        recipient_name: str,
        amount: float,
        channel: str = "UPI",
        category: str = "Transfers"
    ) -> Dict[str, Any]:
        """Execute transfer and record transaction deterministically."""
        account = db.query(Account).filter(Account.customer_id == customer_id).first()
        if not account:
            return {"success": False, "error": "No source account found."}

        if account.balance < amount:
            return {"success": False, "error": f"Insufficient funds. Available balance: {format_inr(account.balance)}"}

        now = datetime.datetime.utcnow()
        account.balance -= amount

        tx = Transaction(
            account_id=account.id,
            customer_id=customer_id,
            amount=round(amount, 2),
            transaction_type="debit",
            category=category,
            merchant_name=recipient_name,
            description=f"Transfer to {recipient_name} via {channel}",
            timestamp=now,
            channel=channel,
            device_id="authorized-mobile-app",
            location_city="Bengaluru",
            is_flagged_fraud=False
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        db.refresh(account)

        return {
            "success": True,
            "transaction_id": tx.id,
            "recipient": recipient_name,
            "amount": amount,
            "formatted_amount": format_inr(amount),
            "new_balance": account.balance,
            "formatted_balance": format_inr(account.balance),
            "timestamp": now.strftime("%d %b %Y, %I:%M %p"),
            "channel": channel
        }
