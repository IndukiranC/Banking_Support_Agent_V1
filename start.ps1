Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting Verifiable Banking Agent (10/10 Solution)" -ForegroundColor Green
Write-Host "  AI Engine: Ollama Llama 3.1 8B (http://localhost:11434)" -ForegroundColor Yellow
Write-Host "  Financial Authority: Python Decimal Engine" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Seed database if not existing
python -m backend.seeder

# 2. Start FastAPI Backend on Port 8000
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

# 3. Start Vite Frontend on Port 5173
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`nServices launched successfully:" -ForegroundColor Green
Write-Host "  -> Backend API:  http://localhost:8000 (Docs at http://localhost:8000/docs)" -ForegroundColor White
Write-Host "  -> Frontend App: http://localhost:5173" -ForegroundColor White
Write-Host "  -> Ollama Model: llama3.1:latest" -ForegroundColor White
