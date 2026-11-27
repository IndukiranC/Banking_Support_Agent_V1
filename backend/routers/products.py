from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import ProductResultObject
from backend.security import get_current_user_payload
from backend.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/products", tags=["Smart Product Recommendations"])

@router.get("/recommendations", response_model=ProductResultObject)
def get_recommendations(
    category: Optional[str] = Query(None),
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id") or 1
    return RecommendationService.get_recommendations(
        db=db,
        customer_id=customer_id,
        category=category
    )
