#!/bin/bash
# Startup script for Railway deployment

echo "Starting Crazyflie Swarm Demo Backend..."

# Navigate to backend directory
cd /app/backend

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in /app/backend/"
    ls -la /app/backend/
    exit 1
fi

# Check if uvicorn is available
if ! command -v uvicorn &> /dev/null; then
    echo "ERROR: uvicorn not found"
    exit 1
fi

echo "Starting uvicorn server..."
uvicorn main:app --host 0.0.0.0 --port $PORT
