Write-Host "Starting FIN Analytics Dev Environment..."

# Start Backend
Start-Process -NoNewWindow -FilePath ".\.venv\Scripts\uvicorn.exe" -ArgumentList "backend.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"

# Start Frontend (Legacy Next.js)
Set-Location frontend
npm run dev
