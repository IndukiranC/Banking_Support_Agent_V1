import io
import csv
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import SpendingResultObject, CheckTransferRequest, ExecuteTransferRequest
from backend.security import get_current_user_payload
from backend.services.spending_service import SpendingService
from backend.models import Transaction

router = APIRouter(prefix="/spending", tags=["Spending Insights"])

@router.get("/summary", response_model=SpendingResultObject)
def get_spending_summary(
    category: Optional[str] = Query(None),
    period: str = Query("current_month"),
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id") or 1
    return SpendingService.get_spending_summary(
        db=db,
        customer_id=customer_id,
        category=category,
        period=period
    )

@router.get("/forecast")
def get_cashflow_forecast(
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id") or 1
    return SpendingService.get_cashflow_forecast(db=db, customer_id=customer_id)

@router.get("/export-csv")
def export_transactions_csv(
    period: str = Query("current_month"),
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id") or 1
    txs = db.query(Transaction).filter(
        Transaction.customer_id == customer_id
    ).order_by(Transaction.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Transaction ID", "Date", "Merchant", "Category", "Amount (INR)", "Type", "Channel", "Flagged Fraud"])

    for t in txs:
        writer.writerow([
            t.id,
            t.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            t.merchant_name,
            t.category,
            f"{t.amount:.2f}",
            t.transaction_type,
            t.channel,
            "YES" if t.is_flagged_fraud else "NO"
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=banking_statement_{period}.csv"}
    )

@router.post("/check-transfer")
def check_transfer(
    req: CheckTransferRequest,
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id") or 1
    return SpendingService.check_repeated_transfer(
        db=db,
        customer_id=customer_id,
        recipient_name=req.recipient_name,
        amount=req.amount,
        window_hours=req.window_hours or 72
    )

@router.post("/execute-transfer")
def execute_transfer(
    req: ExecuteTransferRequest,
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id") or 1
    return SpendingService.execute_transfer(
        db=db,
        customer_id=customer_id,
        recipient_name=req.recipient_name,
        amount=req.amount,
        channel=req.channel or "UPI",
        category=req.category or "Transfers"
    )
