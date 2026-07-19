#!/bin/bash
echo "Starting FIN Analytics Dev Environment..."

# Start Backend in background
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Frontend
cd frontend-dev && npm run dev

# Wait for background process
wait $BACKEND_PID
