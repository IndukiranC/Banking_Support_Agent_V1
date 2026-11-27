from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import LoanResultObject
from backend.security import get_current_user_payload
from backend.services.loan_service import LoanService
from backend.models import Customer

router = APIRouter(prefix="/loans", tags=["Loan & Mortgage Navigator"])

@router.get("/calculate", response_model=LoanResultObject)
def calculate_loan(
    principal: float = Query(4000000.0, description="Principal amount in INR"),
    rate: float = Query(8.5, description="Annual interest rate in %"),
    tenure_months: int = Query(240, description="Tenure in months"),
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id") or 1
    cust = db.query(Customer).filter(Customer.id == customer_id).first()
    income = cust.monthly_income if cust else 125000.0

    return LoanService.calculate_loan_package(
        principal=principal,
        annual_rate_pct=rate,
        tenure_months=tenure_months,
        monthly_income=income
    )

@router.get("/amortisation-schedule")
def get_amortisation_schedule(
    principal: float = Query(4000000.0),
    rate: float = Query(8.5),
    tenure_months: int = Query(240),
    limit: Optional[int] = Query(36, description="Limit rows returned for chart display")
):
    return LoanService.generate_amortisation_schedule(
        principal=principal,
        annual_rate_pct=rate,
        tenure_months=tenure_months,
        limit_months=limit
    )

@router.get("/prepayment-whatif")
def prepayment_whatif(
    principal: float = Query(4000000.0),
    rate: float = Query(8.5),
    tenure_months: int = Query(240),
    prepayment_amount: float = Query(200000.0),
    prepayment_month: int = Query(12)
):
    return LoanService.calculate_prepayment_impact(
        principal=principal,
        annual_rate_pct=rate,
        tenure_months=tenure_months,
        prepayment_amount=prepayment_amount,
        prepayment_month=prepayment_month
    )

@router.get("/balance-transfer")
def balance_transfer_comparison(
    principal: float = Query(3500000.0),
    current_rate: float = Query(9.0),
    new_rate: float = Query(8.35),
    tenure_months: int = Query(220),
    fee_pct: float = Query(0.5)
):
    return LoanService.calculate_balance_transfer(
        outstanding_principal=principal,
        current_rate_pct=current_rate,
        new_rate_pct=new_rate,
        remaining_tenure_months=tenure_months,
        processing_fee_pct=fee_pct
    )
