from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import AuditLogEntry
from backend.security import get_current_user_payload
from backend.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Tamper-Evident Audit Trail"])

@router.get("/logs")
def get_audit_logs(
    limit: int = Query(50, le=200),
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    role = payload.get("role", "customer")
    customer_id = payload.get("customer_id")

    query = db.query(AuditLogEntry)
    # If not admin or analyst, restrict strictly to customer's own events
    if role not in ["admin", "analyst"]:
        query = query.filter(AuditLogEntry.customer_id == customer_id)

    entries = query.order_by(AuditLogEntry.id.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "request_id": e.request_id,
            "timestamp": e.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "action_type": e.action_type,
            "customer_id": e.customer_id,
            "intent": e.intent,
            "services_invoked": e.services_invoked,
            "verification_status": e.verification_status,
            "prev_hash": e.prev_hash,
            "curr_hash": e.curr_hash,
            "client_ip": e.client_ip,
            "notes": e.notes
        }
        for e in entries
    ]

@router.get("/verify-chain")
def verify_audit_chain(db: Session = Depends(get_db)):
    """Cryptographically verifies that no audit log entry has been inserted, modified, or deleted."""
    return AuditService.verify_chain_integrity(db)
