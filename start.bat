@echo off
echo ==========================================================
echo   Starting Verifiable Banking Agent (10/10 Solution)
echo   AI Engine: Ollama Llama 3.1 8B (http://localhost:11434)
echo   Financial Authority: Python Decimal Engine
echo ==========================================================

python -m backend.seeder

start "Banking Agent Backend" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
start "Banking Agent Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Services launched:
echo   -> Backend API:  http://localhost:8000
echo   -> Frontend App: http://localhost:5173
