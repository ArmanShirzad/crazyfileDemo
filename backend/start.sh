#!/bin/bash

# Crazyflie Swarm Demo Startup Script
# This script sets up and runs the backend with proper dependencies

echo "Starting Crazyflie Swarm Demo Backend..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found. Please run this script from the backend directory."
    exit 1
fi

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

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "No .env file found, using default environment variables..."
    # Set default environment variables
    export BACKEND=mock
    export LOG_LEVEL=info
    export MAX_DRONES=10
    export SIMULATION_SPEED=1.0
    export BEARER_TOKEN=demo-token
fi

# Start the server
echo "Starting FastAPI server..."
echo "Backend will be available at: http://localhost:8000"
echo "Health check: http://localhost:8000/health"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
