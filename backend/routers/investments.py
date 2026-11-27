from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import InvestmentResultObject
from backend.security import get_current_user_payload
from backend.services.investment_service import InvestmentService

router = APIRouter(prefix="/investments", tags=["Investment Awareness"])

@router.get("/portfolio", response_model=InvestmentResultObject)
def get_investment_portfolio(
    sip_monthly: Optional[float] = Query(None),
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id") or 1
    return InvestmentService.get_investment_portfolio(
        db=db,
        customer_id=customer_id,
        sip_monthly=sip_monthly
    )

@router.get("/sip-calculator")
def calculate_sip(
    monthly_investment: float = Query(10000.0),
    expected_return_pct: float = Query(12.0),
    tenure_years: int = Query(10)
):
    return InvestmentService.calculate_sip(
        monthly_investment=monthly_investment,
        expected_annual_return_pct=expected_return_pct,
        tenure_years=tenure_years
    )
