import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import Base, engine
from backend.seeder import seed_database
from backend.ollama_client import OllamaClient
from backend.routers import (
    auth, chat, spending, loans, fraud, guidance,
    products, investments, knowledge, audit, quality
)

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Banking Conversation Agent",
    description="A local-first, verifiable, auditable AI banking assistant powered by Llama 3.1 8B via Ollama and deterministic Python financial services.",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Timing & Audit Middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response

# Auto-seed on startup
@app.on_event("startup")
def on_startup():
    try:
        seed_database()
    except Exception as e:
        print(f"Startup seeding warning: {e}")

# Health Check Endpoint
@app.get("/health", tags=["System Health"])
@app.get("/api/v1/health", tags=["System Health"])
def health_check():
    ollama = OllamaClient.get_instance()
    ollama_info = ollama.get_model_info()

    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": "sqlite_connected" if "sqlite" in settings.DATABASE_URL else "postgresql_connected",
        "ai_engine": {
            "type": "Ollama (Strictly Local)",
            "ollama_available": ollama_info.get("available", False),
            "base_url": ollama_info.get("base_url"),
            "target_model": ollama_info.get("target_model"),
            "is_target_installed": ollama_info.get("is_target_installed", False),
            "installed_models": ollama_info.get("installed_models", [])
        },
        "financial_authority": "Deterministic Python (Decimal arithmetic)",
        "security_policy": "Zero-trust LLM with Output Verifier"
    }

# Mount API v1 Routers
api_v1 = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=api_v1)
app.include_router(chat.router, prefix=api_v1)
app.include_router(spending.router, prefix=api_v1)
app.include_router(loans.router, prefix=api_v1)
app.include_router(fraud.router, prefix=api_v1)
app.include_router(guidance.router, prefix=api_v1)
app.include_router(products.router, prefix=api_v1)
app.include_router(investments.router, prefix=api_v1)
app.include_router(knowledge.router, prefix=api_v1)
app.include_router(audit.router, prefix=api_v1)
app.include_router(quality.router, prefix=api_v1)

# Serve built frontend static files if available
import os
from fastapi.staticfiles import StaticFiles

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
