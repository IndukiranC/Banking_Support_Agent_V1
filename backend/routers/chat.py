import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Conversation, Message
from backend.schemas import ChatMessageRequest, ChatMessageResponse
from backend.security import get_current_user_payload
from backend.orchestrator import ConversationOrchestrator

router = APIRouter(prefix="/chat", tags=["AI Banking Chat"])

@router.post("/message", response_model=ChatMessageResponse)
def send_chat_message(
    req: ChatMessageRequest,
    request: Request,
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id")
    if not customer_id:
        customer_id = 1 # Fallback for demo staff

    client_ip = request.client.host if request.client else "127.0.0.1"

    response = ConversationOrchestrator.process_turn(
        db=db,
        customer_id=customer_id,
        user_text=req.message,
        conversation_id=req.conversation_id,
        context_slots=req.context_slots,
        client_ip=client_ip
    )

    # Persist conversation and messages
    conv = None
    if req.conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
    if not conv:
        conv = Conversation(customer_id=customer_id, title=req.message[:30] + "...")
        db.add(conv)
        db.commit()
        db.refresh(conv)

    response.conversation_id = conv.id

    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=req.message
    )
    asst_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=response.reply,
        intent=response.intent,
        result_object=response.result_object,
        verification_status=response.verification.status,
        calculation_details=response.calculation_notes.model_dump() if response.calculation_notes else None,
        latency_ms=response.latency_ms
    )
    db.add(user_msg)
    db.add(asst_msg)
    db.commit()

    return response

@router.post("/stream")
async def stream_chat_message(
    req: ChatMessageRequest,
    request: Request,
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events (SSE) streaming endpoint.
    Streams words/tokens for lightning-fast perception, then closes with final JSON payload.
    """
    customer_id = payload.get("customer_id") or 1
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Compute turn synchronously using deterministic verifier pipeline
    response = ConversationOrchestrator.process_turn(
        db=db,
        customer_id=customer_id,
        user_text=req.message,
        conversation_id=req.conversation_id,
        context_slots=req.context_slots,
        client_ip=client_ip
    )

    async def event_generator():
        # Stream reply in tokens/chunks
        words = response.reply.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            data = json.dumps({"token": chunk})
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.015) # Smooth streaming cadence

        # Send final metadata event
        final_payload = {
            "done": True,
            "response": response.model_dump()
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/history")
def get_chat_history(
    conversation_id: Optional[int] = None,
    payload: Dict[str, Any] = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    customer_id = payload.get("customer_id") or 1
    query = db.query(Message).join(Conversation).filter(Conversation.customer_id == customer_id)
    if conversation_id:
        query = query.filter(Message.conversation_id == conversation_id)
    
    messages = query.order_by(Message.created_at.asc()).limit(50).all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "intent": m.intent,
            "result_object": m.result_object,
            "verification_status": m.verification_status,
            "calculation_notes": m.calculation_details,
            "latency_ms": m.latency_ms,
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ]
