from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Customer, Account
from backend.schemas import LoginRequest, Token, PersonaInfo
from backend.security import (
    verify_password, create_access_token, get_current_user_payload,
    mask_account_number, mask_pan, mask_phone
)

router = APIRouter(prefix="/auth", tags=["Authentication & Personas"])

@router.post("/login", response_model=Token)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == creds.username).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password."
        )

    customer = user.customer
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "customer_id": customer.id if customer else None,
        "customer_name": f"{customer.first_name} {customer.last_name}" if customer else user.username
    }
    token = create_access_token(token_data)

    return Token(
        access_token=token,
        token_type="bearer",
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "customer_id": customer.id if customer else None,
            "name": f"{customer.first_name} {customer.last_name}" if customer else user.username,
            "email": user.email
        }
    )

@router.get("/me")
def get_me(payload: Dict[str, Any] = Depends(get_current_user_payload), db: Session = Depends(get_db)):
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    customer = user.customer
    accounts = []
    if customer:
        for acc in customer.accounts:
            accounts.append({
                "id": acc.id,
                "account_number": acc.account_number,
                "masked_account_number": mask_account_number(acc.account_number),
                "account_type": acc.account_type,
                "balance": acc.balance,
                "currency": acc.currency
            })

    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "customer": {
            "id": customer.id,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "full_name": f"{customer.first_name} {customer.last_name}",
            "email": customer.email,
            "phone": mask_phone(customer.phone),
            "pan": mask_pan(customer.pan_card),
            "monthly_income": customer.monthly_income,
            "credit_score": customer.credit_score,
            "risk_profile": customer.risk_profile,
            "accounts": accounts
        } if customer else None
    }

@router.get("/personas", response_model=List[PersonaInfo])
def list_personas(db: Session = Depends(get_db)):
    """List available demo personas for quick switching in the UI."""
    users = db.query(User).filter(User.customer_id.isnot(None)).all()
    personas: List[PersonaInfo] = []
    
    for u in users:
        cust = u.customer
        acc = cust.accounts[0] if cust.accounts else None
        
        persona_type = "Salaried"
        if cust.monthly_income >= 150000:
            persona_type = "Executive / High Net Worth"
        elif cust.monthly_income <= 30000:
            persona_type = "Student / Young Career"
        elif "Design" in (cust.employer or ""):
            persona_type = "Freelancer"

        personas.append(PersonaInfo(
            id=u.id,
            name=f"{cust.first_name} {cust.last_name}",
            username=u.username,
            role=u.role,
            persona_type=persona_type,
            monthly_income=cust.monthly_income,
            credit_score=cust.credit_score,
            account_number=mask_account_number(acc.account_number) if acc else "N/A",
            balance=acc.balance if acc else 0.0
        ))
    return personas

@router.post("/switch-persona/{user_id}", response_model=Token)
def switch_persona(user_id: int, db: Session = Depends(get_db)):
    """Instantly switch to a demo persona for testing without password prompt."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Persona not found")

    customer = user.customer
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "customer_id": customer.id if customer else None,
        "customer_name": f"{customer.first_name} {customer.last_name}" if customer else user.username
    }
    token = create_access_token(token_data)

    return Token(
        access_token=token,
        token_type="bearer",
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "customer_id": customer.id if customer else None,
            "name": f"{customer.first_name} {customer.last_name}" if customer else user.username,
            "email": user.email
        }
    )
