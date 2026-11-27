import re
import datetime
import secrets
from typing import Optional, Dict, Any, List
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.config import settings

ph = PasswordHasher()
security_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hash password using Argon2id."""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

# PII Masking Utilities
def mask_account_number(acc_num: Optional[str]) -> str:
    if not acc_num:
        return "XXXX-0000"
    clean = re.sub(r'[^0-9A-Za-z]', '', str(acc_num))
    if len(clean) <= 4:
        return f"XXXX-{clean}"
    return f"XXXX-XXXX-{clean[-4:]}"

def mask_pan(pan: Optional[str]) -> str:
    if not pan or len(pan) < 5:
        return "XXXXX0000X"
    return f"XXXXX{pan[5:9]}{pan[9]}" if len(pan) >= 10 else f"XXXXX{pan[-4:]}"

def mask_phone(phone: Optional[str]) -> str:
    if not phone or len(phone) < 4:
        return "+91-XXXXX-0000"
    return f"+91-XXXXX-{phone[-4:]}"

def mask_pii_in_text(text: str) -> str:
    """Mask account numbers, 10-digit phone numbers, and PAN cards in text logs."""
    # Mask 10-16 digit account/card numbers
    text = re.sub(r'\b(?:\d[ -]*?){12,16}\b', lambda m: mask_account_number(m.group(0)), text)
    # Mask Indian PAN (e.g. ABCDE1234F)
    text = re.sub(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', lambda m: mask_pan(m.group(0)), text)
    # Mask 10-digit mobile numbers
    text = re.sub(r'\b(?:\+91|91)?[6-9]\d{9}\b', lambda m: mask_phone(m.group(0)), text)
    return text

# Sensitive Action Confirmation Token Store
_ACTION_TOKENS: Dict[str, Dict[str, Any]] = {}

def create_action_token(customer_id: int, action_type: str, payload: Dict[str, Any]) -> str:
    token = secrets.token_urlsafe(32)
    _ACTION_TOKENS[token] = {
        "customer_id": customer_id,
        "action_type": action_type,
        "payload": payload,
        "created_at": datetime.datetime.utcnow(),
        "expires_at": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    }
    return token

def verify_action_token(token: str, customer_id: int, action_type: str) -> Optional[Dict[str, Any]]:
    record = _ACTION_TOKENS.get(token)
    if not record:
        return None
    if record["expires_at"] < datetime.datetime.utcnow():
        del _ACTION_TOKENS[token]
        return None
    if record["customer_id"] != customer_id or record["action_type"] != action_type:
        return None
    del _ACTION_TOKENS[token]
    return record["payload"]

# FastAPI Dependency for Auth & RBAC
def get_current_user_payload(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> Dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def require_roles(allowed_roles: List[str]):
    def role_checker(payload: Dict[str, Any] = Depends(get_current_user_payload)) -> Dict[str, Any]:
        role = payload.get("role", "customer")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: role '{role}' is not authorized for this resource.",
            )
        return payload
    return role_checker
