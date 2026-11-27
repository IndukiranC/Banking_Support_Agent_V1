from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import GuidanceResultObject
from backend.security import get_current_user_payload
from backend.services.guidance_service import GuidanceService

router = APIRouter(prefix="/guidance", tags=["Personalised Financial Guidance"])

@router.get("/plan", response_model=GuidanceResultObject)
def get_guidance_plan(
    dining_cut: float = Query(0.0, description="What-if reduction % for dining"),
    shopping_cut: float = Query(0.0, description="What-if reduction % for shopping"),
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id") or 1
    return GuidanceService.calculate_budget_guidance(
        db=db,
        customer_id=customer_id,
        dining_reduction_pct=dining_cut,
        shopping_reduction_pct=shopping_cut
    )
