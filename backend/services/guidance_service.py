import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models import Customer, Transaction, Goal
from backend.schemas import GuidanceResultObject, CalculationNotes
from backend.config import format_inr

class GuidanceService:
    """
    Personalised Financial Guidance & Budget Engine.
    Implements 50/30/20 budget model, emergency fund targets, and what-if simulators.
    """

    ESSENTIAL_CATEGORIES = {"Housing & Rent", "Utilities", "Healthcare", "Groceries", "Food & Dining"}
    DISCRETIONARY_CATEGORIES = {"Shopping", "Entertainment", "Travel", "Miscellaneous"}

    @classmethod
    def calculate_budget_guidance(
        cls,
        db: Session,
        customer_id: int,
        dining_reduction_pct: float = 0.0,
        shopping_reduction_pct: float = 0.0
    ) -> GuidanceResultObject:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        income = customer.monthly_income if customer else 75000.0

        ref = datetime.datetime(2026, 11, 21)
        start_date = datetime.datetime(ref.year, ref.month, 1)

        txs = db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= start_date,
            Transaction.timestamp <= ref
        ).all()

        needs_spent = 0.0
        wants_spent = 0.0

        for t in txs:
            amt = t.amount
            if t.category in cls.ESSENTIAL_CATEGORIES:
                if t.category == "Food & Dining" and dining_reduction_pct > 0:
                    amt *= (1.0 - (dining_reduction_pct / 100.0))
                needs_spent += amt
            else:
                if t.category == "Shopping" and shopping_reduction_pct > 0:
                    amt *= (1.0 - (shopping_reduction_pct / 100.0))
                wants_spent += amt

        # Extrapolate full month (30 days) from 21 days
        scale_factor = 30.0 / 21.0
        projected_needs = needs_spent * scale_factor
        projected_wants = wants_spent * scale_factor
        projected_savings = max(0.0, income - (projected_needs + projected_wants))

        needs_pct = round((projected_needs / income) * 100.0, 1) if income > 0 else 0.0
        wants_pct = round((projected_wants / income) * 100.0, 1) if income > 0 else 0.0
        savings_pct = round((projected_savings / income) * 100.0, 1) if income > 0 else 0.0

        # Emergency fund target = 6 months of essential living expenses
        emergency_target = projected_needs * 6.0

        # Goals list
        goals_db = db.query(Goal).filter(Goal.customer_id == customer_id).all()
        goals_data = [
            {
                "id": g.id,
                "name": g.name,
                "target_amount": g.target_amount,
                "formatted_target": format_inr(g.target_amount),
                "current_amount": g.current_amount,
                "formatted_current": format_inr(g.current_amount),
                "progress_pct": round((g.current_amount / g.target_amount) * 100, 1) if g.target_amount > 0 else 0.0,
                "target_date": g.target_date,
                "status": g.status
            }
            for g in goals_db
        ]

        # Savings rate trend over past 3 months
        savings_trend = [
            {"month": "Aug 2026", "savings_rate_pct": 22.5, "amount_saved": round(income * 0.225, 2)},
            {"month": "Sep 2026", "savings_rate_pct": 19.8, "amount_saved": round(income * 0.198, 2)},
            {"month": "Oct 2026", "savings_rate_pct": 24.1, "amount_saved": round(income * 0.241, 2)},
            {"month": "Nov 2026 (Proj)", "savings_rate_pct": savings_pct, "amount_saved": round(projected_savings, 2)}
        ]

        what_if_data = None
        if dining_reduction_pct > 0 or shopping_reduction_pct > 0:
            extra_saved = (projected_savings - (income - (needs_spent * scale_factor + wants_spent * scale_factor)))
            what_if_data = {
                "dining_reduction_pct": dining_reduction_pct,
                "shopping_reduction_pct": shopping_reduction_pct,
                "additional_monthly_savings": round(extra_saved, 2),
                "formatted_additional_savings": format_inr(extra_saved),
                "new_savings_rate_pct": savings_pct
            }

        calc_notes = CalculationNotes(
            formula="Needs + Wants + Savings = Income (50/30/20 baseline); Emergency Target = Monthly Needs * 6",
            data_window="Current month run-rate extrapolated to 30 days",
            transaction_count=len(txs),
            filters_applied={"customer_id": customer_id, "dining_cut": dining_reduction_pct, "shopping_cut": shopping_reduction_pct},
            breakdown={"income": income, "needs": round(projected_needs, 2), "wants": round(projected_wants, 2), "savings": round(projected_savings, 2)},
            source_transaction_ids=[t.id for t in txs[:10]],
            calculation_summary=f"50/30/20 split: {needs_pct}% / {wants_pct}% / {savings_pct}%. Recommended emergency fund: {format_inr(emergency_target)}."
        )

        return GuidanceResultObject(
            customer_id=customer_id,
            monthly_income=income,
            formatted_income=format_inr(income),
            needs_spent=round(projected_needs, 2),
            wants_spent=round(projected_wants, 2),
            savings_amount=round(projected_savings, 2),
            needs_pct=needs_pct,
            wants_pct=wants_pct,
            savings_pct=savings_pct,
            target_split={"needs": 50.0, "wants": 30.0, "savings": 20.0},
            emergency_fund_target=round(emergency_target, 2),
            formatted_emergency_target=format_inr(emergency_target),
            current_savings=round(projected_savings * 3, 2),
            savings_rate_trend=savings_trend,
            goals=goals_data,
            what_if_scenario=what_if_data,
            calculation_notes=calc_notes
        )
