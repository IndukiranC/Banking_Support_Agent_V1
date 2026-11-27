from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models import Customer, HoldingSimulated
from backend.schemas import InvestmentResultObject, CalculationNotes
from backend.config import format_inr

class InvestmentService:
    """
    Investment Awareness & Educational Portfolio Engine.
    Strictly educational: Provides asset allocation models, SIP calculators, and portfolio tracking.
    Enforces SEBI/regulatory policy: Never gives buy/sell/hold calls or guarantees returns.
    """

    EDUCATIONAL_DISCLAIMER = (
        "Educational & Illustrative Information Only. Antigravity Banking Agent does not provide certified "
        "investment advice, portfolio management, or buy/sell recommendations. Securities investments are "
        "subject to market risks. Please consult a SEBI-registered financial advisor before investing."
    )

    RISK_ALLOCATIONS = {
        "Conservative": {
            "Equity (Index Funds / Large Cap)": 0.20,
            "Debt (Bonds / Fixed Income)": 0.50,
            "Gold / Precious Metals": 0.15,
            "Liquid / Emergency Cash": 0.15
        },
        "Moderate": {
            "Equity (Index Funds / Large Cap)": 0.50,
            "Debt (Bonds / Fixed Income)": 0.30,
            "Gold / Precious Metals": 0.10,
            "Liquid / Emergency Cash": 0.10
        },
        "Aggressive": {
            "Equity (Index Funds / Large Cap)": 0.70,
            "Debt (Bonds / Fixed Income)": 0.15,
            "Gold / Precious Metals": 0.10,
            "Liquid / Emergency Cash": 0.05
        }
    }

    @classmethod
    def calculate_sip(
        cls,
        monthly_investment: float,
        expected_annual_return_pct: float,
        tenure_years: int
    ) -> Dict[str, Any]:
        """
        Standard Systematic Investment Plan (SIP) Compound Return Formula:
        M = P * [ (1 + i)^n - 1 ] * (1 + i) / i
        where:
        P = Monthly contribution
        i = Monthly rate = r / 12 / 100
        n = Total months = years * 12
        """
        P = float(monthly_investment)
        r = float(expected_annual_return_pct)
        n = tenure_years * 12
        i = r / 12.0 / 100.0

        if i == 0:
            maturity_val = P * n
        else:
            maturity_val = P * (((1.0 + i) ** n - 1.0) / i) * (1.0 + i)

        invested_capital = P * n
        wealth_gain = maturity_val - invested_capital

        return {
            "monthly_sip": P,
            "formatted_sip": format_inr(P),
            "expected_return_pct": r,
            "tenure_years": tenure_years,
            "total_months": n,
            "invested_capital": round(invested_capital, 2),
            "formatted_invested": format_inr(invested_capital),
            "wealth_gain": round(wealth_gain, 2),
            "formatted_gain": format_inr(wealth_gain),
            "maturity_value": round(maturity_val, 2),
            "formatted_maturity": format_inr(maturity_val)
        }

    @classmethod
    def get_investment_portfolio(
        cls,
        db: Session,
        customer_id: int,
        sip_monthly: Optional[float] = None
    ) -> InvestmentResultObject:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        profile = customer.risk_profile if customer else "Moderate"
        allocations = cls.RISK_ALLOCATIONS.get(profile, cls.RISK_ALLOCATIONS["Moderate"])

        holdings = db.query(HoldingSimulated).filter(HoldingSimulated.customer_id == customer_id).all()
        holdings_data = [
            {
                "id": h.id,
                "asset_type": h.asset_type,
                "asset_name": h.asset_name,
                "invested_amount": h.invested_amount,
                "formatted_invested": format_inr(h.invested_amount),
                "current_value": h.current_value,
                "formatted_current": format_inr(h.current_value),
                "return_pct": h.return_pct
            }
            for h in holdings
        ]

        total_invested = sum(h.invested_amount for h in holdings)
        total_value = sum(h.current_value for h in holdings)

        sip_calc = None
        if sip_monthly and sip_monthly > 0:
            sip_calc = cls.calculate_sip(sip_monthly, 12.0, 10)

        calc_notes = CalculationNotes(
            formula="M = P * [ (1+i)^n - 1 ] * (1+i) / i; Benchmark Asset Mix keyed to Risk Profile",
            data_window="Current simulated holdings & 10-year compounding horizon",
            transaction_count=len(holdings),
            filters_applied={"customer_id": customer_id, "risk_profile": profile},
            breakdown={"total_invested": total_invested, "current_value": total_value, "unrealized_gain": round(total_value - total_invested, 2)},
            source_transaction_ids=[],
            calculation_summary=f"Profile assessed as {profile}. Model asset mix: {allocations}. Zero stock-picking bias."
        )

        return InvestmentResultObject(
            risk_profile=profile,
            recommended_allocation=allocations,
            current_holdings=holdings_data,
            sip_simulation=sip_calc,
            disclaimer=cls.EDUCATIONAL_DISCLAIMER,
            calculation_notes=calc_notes
        )
