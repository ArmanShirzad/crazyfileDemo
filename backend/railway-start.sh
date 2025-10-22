#!/bin/bash

# Railway deployment script for Crazyflie Swarm Demo Backend

echo "Starting Railway deployment..."

# Navigate to backend directory
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Set environment variables for Railway
export BACKEND=mock
export LOG_LEVEL=info
export MAX_DRONES=10
export SIMULATION_SPEED=1.0
export BEARER_TOKEN=demo-token
export API_HOST=0.0.0.0
export API_PORT=${PORT:-8000}

# Start the server
echo "Starting FastAPI server on port ${API_PORT}..."
python main.py
