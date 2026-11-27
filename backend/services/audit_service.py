import hashlib
import json
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models import AuditLogEntry
from backend.security import mask_pii_in_text

class AuditService:
    """
    Append-Only Cryptographically Hash-Chained Audit Log.
    Provides verifiable, tamper-evident audit trails for all operations.
    """

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    @classmethod
    def _compute_entry_hash(
        cls,
        prev_hash: str,
        timestamp_iso: str,
        action_type: str,
        customer_id: Optional[int],
        intent: Optional[str],
        services_invoked: List[str],
        verification_status: Optional[str]
    ) -> str:
        payload = f"{prev_hash}|{timestamp_iso}|{action_type}|{customer_id}|{intent}|{sorted(services_invoked)}|{verification_status}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def log_event(
        cls,
        db: Session,
        request_id: str,
        action_type: str,
        customer_id: Optional[int] = None,
        user_id: Optional[int] = None,
        intent: Optional[str] = None,
        services_invoked: Optional[List[str]] = None,
        verification_status: Optional[str] = None,
        client_ip: str = "127.0.0.1",
        notes: Optional[str] = None
    ) -> AuditLogEntry:
        # Get the latest entry to link the hash chain
        last_entry = db.query(AuditLogEntry).order_by(AuditLogEntry.id.desc()).first()
        prev_hash = last_entry.curr_hash if last_entry else cls.GENESIS_HASH

        now = datetime.datetime.utcnow()
        services = services_invoked or []
        curr_hash = cls._compute_entry_hash(
            prev_hash=prev_hash,
            timestamp_iso=now.isoformat(),
            action_type=action_type,
            customer_id=customer_id,
            intent=intent,
            services_invoked=services,
            verification_status=verification_status
        )

        masked_notes = mask_pii_in_text(notes) if notes else None

        entry = AuditLogEntry(
            request_id=request_id,
            timestamp=now,
            customer_id=customer_id,
            user_id=user_id,
            action_type=action_type,
            intent=intent,
            services_invoked=services,
            verification_status=verification_status,
            prev_hash=prev_hash,
            curr_hash=curr_hash,
            client_ip=client_ip,
            notes=masked_notes
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @classmethod
    def verify_chain_integrity(cls, db: Session) -> Dict[str, Any]:
        """
        Verify the entire hash chain from genesis to tip.
        Returns whether the audit trail has remained tamper-proof.
        """
        entries = db.query(AuditLogEntry).order_by(AuditLogEntry.id.asc()).all()
        if not entries:
            return {"valid": True, "total_entries": 0, "status": "EMPTY_CHAIN"}

        expected_prev = cls.GENESIS_HASH
        for idx, entry in enumerate(entries):
            if entry.prev_hash != expected_prev:
                return {
                    "valid": False,
                    "failed_at_id": entry.id,
                    "reason": f"Chain broken at entry #{entry.id}: prev_hash mismatch. Expected {expected_prev}, found {entry.prev_hash}.",
                    "total_entries": len(entries)
                }

            recomputed_hash = cls._compute_entry_hash(
                prev_hash=entry.prev_hash,
                timestamp_iso=entry.timestamp.isoformat(),
                action_type=entry.action_type,
                customer_id=entry.customer_id,
                intent=entry.intent,
                services_invoked=entry.services_invoked or [],
                verification_status=entry.verification_status
            )

            if entry.curr_hash != recomputed_hash:
                return {
                    "valid": False,
                    "failed_at_id": entry.id,
                    "reason": f"Cryptographic integrity failed at entry #{entry.id}: recomputed hash does not match stored hash.",
                    "total_entries": len(entries)
                }

            expected_prev = entry.curr_hash

        return {
            "valid": True,
            "total_entries": len(entries),
            "latest_hash": entries[-1].curr_hash,
            "status": "CHAIN_INTEGRITY_VERIFIED_TAMPER_PROOF"
        }
