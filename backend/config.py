import os

# Auto-load .env if present
if os.path.exists(".env"):
    try:
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass

class Settings:
    PROJECT_NAME: str = "Verifiable Banking Agent"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # AI Constraints: Ollama is the AI API (supports local or Ollama cloud key)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:latest")
    OLLAMA_KEEP_ALIVE: str = os.getenv("OLLAMA_KEEP_ALIVE", "1h")
    OLLAMA_CONTEXT_SIZE: int = 4096
    OLLAMA_TEMPERATURE: float = 0.1
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/banking.db")
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "banking-super-secret-key-change-in-prod-78901234")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours for demo
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Financial formatting
    CURRENCY_SYMBOL: str = "₹"
    CURRENCY_CODE: str = "INR"

settings = Settings()

def format_inr(amount: float | int) -> str:
    """Format a number into Indian Rupee numbering format (Lakhs, Crores)."""
    try:
        val = float(amount)
        is_negative = val < 0
        val = abs(val)
        
        # Round to 2 decimals
        cents = f"{val:.2f}".split(".")[1]
        int_part = str(int(val))
        
        if len(int_part) <= 3:
            res = int_part
        else:
            last_three = int_part[-3:]
            remaining = int_part[:-3]
            groups = []
            while len(remaining) > 2:
                groups.insert(0, remaining[-2:])
                remaining = remaining[:-2]
            if remaining:
                groups.insert(0, remaining)
            res = ",".join(groups) + "," + last_three
            
        formatted = f"₹{res}" if cents == "00" else f"₹{res}.{cents}"
        return f"-{formatted}" if is_negative else formatted
    except Exception:
        return f"₹{amount}"
