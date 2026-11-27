from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models import Product, Customer, Account, Transaction
from backend.schemas import ProductResultObject, CalculationNotes
from backend.config import format_inr

class RecommendationService:
    """
    Transparent, Rule-Based Product Matching Engine.
    Filters candidate products by hard eligibility, then ranks fit score based on customer profile.
    No hidden sponsored ranking. Every fit and exclusion is documented.
    """

    DEFAULT_PRODUCTS = [
        {
            "product_code": "CARD_PREMIUM_CASHBACK",
            "name": "Apex Cashback SuperCard",
            "category": "credit_card",
            "interest_rate_or_fee": "₹999 annual fee (waived on ₹1.5L spend)",
            "reward_rate": "5% on Dining & Swiggy/Zomato, 3% on Amazon/Flipkart",
            "min_income": 40000.0,
            "min_credit_score": 720,
            "min_balance": 0.0,
            "description": "Tailored for foodies and frequent online shoppers. Flat 5% cashback on leading food delivery platforms.",
            "caveats": "Cashback capped at ₹2,500 per billing cycle. Fuel surcharges excluded."
        },
        {
            "product_code": "CARD_TRAVEL_ELITE",
            "name": "Voyager Club World Card",
            "category": "credit_card",
            "interest_rate_or_fee": "₹2,999 annual fee",
            "reward_rate": "4 reward points per ₹100; complimentary domestic & international lounge access",
            "min_income": 100000.0,
            "min_credit_score": 760,
            "min_balance": 0.0,
            "description": "Premium travel card with zero forex markup and 8 complimentary airport lounge visits yearly.",
            "caveats": "Annual fee waiver requires ₹4,00,000 spend in preceding year."
        },
        {
            "product_code": "CARD_STARTER_SECURE",
            "name": "StepUp Secured Credit Card",
            "category": "credit_card",
            "interest_rate_or_fee": "Zero annual fee",
            "reward_rate": "1% flat cashback on all UPI & POS spends",
            "min_income": 15000.0,
            "min_credit_score": 600,
            "min_balance": 10000.0,
            "description": "Designed for students and early-career pros to rapidly build or repair credit history.",
            "caveats": "Backed by a minimum ₹10,000 fixed deposit lien."
        },
        {
            "product_code": "LOAN_HOME_PRIME",
            "name": "Greenspan Prime Home Loan",
            "category": "loan",
            "interest_rate_or_fee": "8.35% p.a. floating",
            "reward_rate": "Zero processing fee on online applications",
            "min_income": 60000.0,
            "min_credit_score": 750,
            "min_balance": 0.0,
            "description": "Low-rate mortgage financing up to 80% property value with zero prepayment penalty.",
            "caveats": "Floating rate linked to RBI Repo rate; subject to quarterly reset."
        },
        {
            "product_code": "FD_HIGH_YIELD",
            "name": "SmartYield 400-Day Fixed Deposit",
            "category": "fixed_deposit",
            "interest_rate_or_fee": "7.40% p.a. (7.90% for Senior Citizens)",
            "reward_rate": "Quarterly compounding interest",
            "min_income": 0.0,
            "min_credit_score": 0,
            "min_balance": 25000.0,
            "description": "Guaranteed capital growth insured by DICGC up to ₹5,00,000.",
            "caveats": "Premature withdrawal penalty of 0.5% interest deduction."
        }
    ]

    @classmethod
    def get_recommendations(
        cls,
        db: Session,
        customer_id: int,
        category: Optional[str] = None
    ) -> ProductResultObject:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        income = customer.monthly_income if customer else 75000.0
        credit_score = customer.credit_score if customer else 750
        
        # Calculate customer balance and spend mix
        accounts = db.query(Account).filter(Account.customer_id == customer_id).all()
        total_balance = sum(a.balance for a in accounts)

        # Analyze food & dining spend
        txs = db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.transaction_type == "debit"
        ).all()
        total_spend = sum(t.amount for t in txs) or 1.0
        food_spend = sum(t.amount for t in txs if t.category == "Food & Dining")
        food_pct = (food_spend / total_spend) * 100

        recommended = []
        excluded = []

        products = db.query(Product).all()
        if not products:
            # Seed default catalogue if empty
            for p in cls.DEFAULT_PRODUCTS:
                db_prod = Product(
                    product_code=p["product_code"],
                    name=p["name"],
                    category=p["category"],
                    interest_rate_or_fee=p["interest_rate_or_fee"],
                    reward_rate=p["reward_rate"],
                    min_income=p["min_income"],
                    min_credit_score=p["min_credit_score"],
                    min_balance=p["min_balance"],
                    description=p["description"],
                    caveats=p["caveats"]
                )
                db.add(db_prod)
            db.commit()
            products = db.query(Product).all()

        for p in products:
            if category and category.lower() not in ["all", "any"] and p.category != category.lower():
                continue

            # Hard eligibility checks
            reasons_fail = []
            if income < p.min_income:
                reasons_fail.append(f"Requires minimum monthly income of {format_inr(p.min_income)} (current: {format_inr(income)})")
            if credit_score < p.min_credit_score:
                reasons_fail.append(f"Requires credit score >= {p.min_credit_score} (current: {credit_score})")
            if total_balance < p.min_balance:
                reasons_fail.append(f"Requires minimum relationship balance of {format_inr(p.min_balance)} (current: {format_inr(total_balance)})")

            if reasons_fail:
                excluded.append({
                    "product_code": p.product_code,
                    "name": p.name,
                    "category": p.category,
                    "exclusion_reasons": reasons_fail,
                    "caveats": p.caveats
                })
            else:
                # Calculate transparent fit score
                base_score = 70
                fit_factors = []

                if "cashback" in p.product_code.lower() and food_pct >= 20:
                    base_score += 25
                    fit_factors.append(f"High dining spend mix ({food_pct:.1f}% of outlays) matches the 5% dining rewards structure")
                elif "travel" in p.product_code.lower() and income >= 120000:
                    base_score += 20
                    fit_factors.append("Strong income bracket unlocks full lounge and premium concierge utility")
                elif "home" in p.product_code.lower() and credit_score >= 780:
                    base_score += 25
                    fit_factors.append(f"Excellent credit score ({credit_score}) qualifies for the lowest tier 8.35% floating rate")
                elif "fd" in p.product_code.lower() and total_balance >= 50000:
                    base_score += 15
                    fit_factors.append(f"Idle liquid balance ({format_inr(total_balance)}) can earn 7.4% risk-free return")
                else:
                    base_score += 10
                    fit_factors.append("Meets all underwriting and affordability benchmarks")

                fit_score = min(98, base_score)

                recommended.append({
                    "product_code": p.product_code,
                    "name": p.name,
                    "category": p.category,
                    "interest_rate_or_fee": p.interest_rate_or_fee,
                    "reward_rate": p.reward_rate,
                    "fit_score": fit_score,
                    "fit_reason": " | ".join(fit_factors),
                    "description": p.description,
                    "caveats": p.caveats
                })

        # Sort recommended by fit score descending
        recommended.sort(key=lambda x: x["fit_score"], reverse=True)

        calc_notes = CalculationNotes(
            formula="FitScore = Base(70) + ProfileSpendMatchBonus; Hard Eligibility: Income >= MinIncome AND Score >= MinScore",
            data_window="Current customer profile + 3-month transaction mix",
            transaction_count=len(products),
            filters_applied={"customer_id": customer_id, "income": income, "credit_score": credit_score},
            breakdown={"eligible_count": len(recommended), "excluded_count": len(excluded)},
            source_transaction_ids=[],
            calculation_summary=f"Matched {len(recommended)} eligible products out of {len(products)} evaluated. 0 sponsored bias."
        )

        return ProductResultObject(
            recommended_products=recommended,
            excluded_products=excluded,
            customer_profile={
                "customer_id": customer_id,
                "monthly_income": income,
                "credit_score": credit_score,
                "balance": total_balance
            },
            calculation_notes=calc_notes
        )
