from typing import Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import FraudResultObject
from backend.security import get_current_user_payload
from backend.services.fraud_service import FraudService

router = APIRouter(prefix="/fraud", tags=["Fraud Monitoring & Alert Centre"])

class ReviewFeedbackRequest(BaseModel):
    feedback: str # "THIS_WAS_ME" or "THIS_WAS_NOT_ME"

@router.get("/summary", response_model=FraudResultObject)
def get_fraud_summary(
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id") or 1
    return FraudService.get_fraud_summary(db=db, customer_id=customer_id)

@router.post("/review/{alert_id}")
def review_fraud_alert(
    alert_id: int,
    req: ReviewFeedbackRequest,
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    if req.feedback not in ["THIS_WAS_ME", "THIS_WAS_NOT_ME"]:
        raise HTTPException(status_code=400, detail="Feedback must be 'THIS_WAS_ME' or 'THIS_WAS_NOT_ME'")

    res = FraudService.record_feedback(db=db, alert_id=alert_id, feedback=req.feedback)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error"))
    return res

@router.post("/simulate")
def simulate_fraud_anomaly(
    scenario: str = Query("outlier", description="Scenario: 'outlier', 'velocity', 'structuring'"),
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id") or 1
    return FraudService.inject_synthetic_anomaly(db=db, customer_id=customer_id, scenario=scenario)
