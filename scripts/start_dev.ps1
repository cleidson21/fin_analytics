Write-Host "Starting FIN Analytics Dev Environment..."

# Start Backend
Start-Process -NoNewWindow -FilePath "uvicorn" -ArgumentList "backend.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"

# Start Frontend
Set-Location frontend-dev
npm run dev
