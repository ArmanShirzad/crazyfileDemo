import os
import asyncio
import sqlite3
import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from simulators.mock_simulator import DroneSimulator
from algorithms.trajectory_planner import SimpleCollisionAvoidance

# Configuration
BACKEND = os.getenv("BACKEND", "mock")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
MAX_DRONES = int(os.getenv("MAX_DRONES", "10"))
SIMULATION_SPEED = float(os.getenv("SIMULATION_SPEED", "1.0"))
BEARER_TOKEN = os.getenv("BEARER_TOKEN", "demo-token")

# Initialize FastAPI app
app = FastAPI(
    title="Crazyflie Swarm Demo API",
    description="Mock simulator for Crazyflie swarm control",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)  # Make bearer token optional

# Global simulator instance
simulator = None
planner = SimpleCollisionAvoidance()

# Database setup
def init_db():
    conn = sqlite3.connect('swarm_logs.db')
    cursor = conn.cursor()
    
    # Create runs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            name TEXT,
            startedAt TEXT,
            endedAt TEXT,
            status TEXT
        )
    ''')
    
    # Create samples table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            runId TEXT,
            droneId TEXT,
            t REAL,
            x REAL,
            y REAL,
            z REAL,
            vx REAL,
            vy REAL,
            vz REAL,
            battery REAL,
            status TEXT,
            FOREIGN KEY (runId) REFERENCES runs (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Authentication
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header required")
    if credentials.credentials != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

# Optional auth for read-only endpoints
def optional_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if credentials and credentials.credentials != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials if credentials else None

# Pydantic models
class CreateSwarmRequest(BaseModel):
    count: int

class TakeoffRequest(BaseModel):
    height: float = 0.6
    duration: float = 2.0

class GotoRequest(BaseModel):
    x: float
    y: float
    z: float
    speed: float = 0.5

class FormationRequest(BaseModel):
    formation: str  # "line", "circle", "grid", "vshape"
    parameters: Dict[str, Any] = {}

class ExperimentRequest(BaseModel):
    scenario: str
    numDrones: int
    duration: int
    parameters: Dict[str, Any] = {}

class AlgorithmValidationRequest(BaseModel):
    algorithm: str
    testCases: List[Dict[str, Any]]

# Startup event
@app.on_event("startup")
async def startup_event():
    global simulator
    init_db()
    
    if BACKEND == "mock":
        simulator = DroneSimulator()
        await simulator.start()
    else:
        # TODO: Initialize ROS 2 adapter
        raise NotImplementedError("ROS 2 backend not implemented yet")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    global simulator
    if simulator:
        await simulator.stop()

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "backend": BACKEND}

# Drone management endpoints
@app.post("/drones/create")
async def create_swarm(request: CreateSwarmRequest, token: str = Depends(verify_token)):
    if request.count > MAX_DRONES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_DRONES} drones allowed")
    
    if not simulator:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    drone_ids = await simulator.create_swarm(request.count, run_id)
    
    return {"runId": run_id, "drones": drone_ids}

@app.get("/drones")
async def get_drones(token: Optional[str] = Depends(optional_auth)):
    if not simulator:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    return await simulator.get_all_states()

@app.post("/drones/{drone_id}/takeoff")
async def takeoff(drone_id: str, request: TakeoffRequest, token: str = Depends(verify_token)):
    if not simulator:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    # Bounds checking
    if request.height > 1.0:
        raise HTTPException(status_code=400, detail="Height must be <= 1.0m")
    
    success = await simulator.takeoff(drone_id, request.height, request.duration)
    if not success:
        raise HTTPException(status_code=400, detail="Takeoff failed")
    
    return {"ok": True}

@app.post("/drones/{drone_id}/goto")
async def goto(drone_id: str, request: GotoRequest, token: str = Depends(verify_token)):
    if not simulator:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    # Bounds checking
    if abs(request.x) > 1.0 or abs(request.y) > 1.0 or request.z > 1.0:
        raise HTTPException(status_code=400, detail="Position out of bounds")
    
    if request.speed > 1.0:
        raise HTTPException(status_code=400, detail="Speed must be <= 1.0 m/s")
    
    success = await simulator.goto(drone_id, request.x, request.y, request.z, request.speed)
    if not success:
        raise HTTPException(status_code=400, detail="Goto failed")
    
    return {"ok": True}

@app.post("/drones/{drone_id}/land")
async def land(drone_id: str, token: str = Depends(verify_token)):
    if not simulator:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    success = await simulator.land(drone_id)
    if not success:
        raise HTTPException(status_code=400, detail="Land failed")
    
    return {"ok": True}

@app.get("/drones/{drone_id}/state")
async def get_drone_state(drone_id: str, token: Optional[str] = Depends(optional_auth)):
    if not simulator:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    state = await simulator.get_drone_state(drone_id)
    if not state:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    return state

# Swarm operations
@app.post("/swarm/formation")
async def set_formation(request: FormationRequest, token: str = Depends(verify_token)):
    if not simulator:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    success = await simulator.set_formation(request.formation, request.parameters)
    if not success:
        raise HTTPException(status_code=400, detail="Formation failed")
    
    return {"ok": True}

# Experiments
@app.post("/experiments/run")
async def run_experiment(request: ExperimentRequest, token: str = Depends(verify_token)):
    if not simulator:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    result = await simulator.run_experiment(
        request.scenario,
        request.numDrones,
        request.duration,
        request.parameters
    )
    
    return result

# Logging and data export
@app.get("/logs")
async def get_logs(
    runId: str = Query(...),
    format: str = Query("json", regex="^(json|csv)$"),
    token: Optional[str] = Depends(optional_auth)
):
    conn = sqlite3.connect('swarm_logs.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t, x, y, z, vx, vy, vz, battery, status, droneId
        FROM samples 
        WHERE runId = ? 
        ORDER BY t, droneId
    ''', (runId,))
    
    samples = cursor.fetchall()
    conn.close()
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['t', 'x', 'y', 'z', 'vx', 'vy', 'vz', 'battery', 'status', 'droneId'])
        writer.writerows(samples)
        
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={runId}.csv"}
        )
    else:
        return {
            "samples": [
                {
                    "t": row[0],
                    "x": row[1],
                    "y": row[2],
                    "z": row[3],
                    "vx": row[4],
                    "vy": row[5],
                    "vz": row[6],
                    "battery": row[7],
                    "status": row[8],
                    "droneId": row[9]
                }
                for row in samples
            ]
        }

# Emergency stop
@app.post("/emergency/stop")
async def emergency_stop(token: str = Depends(verify_token)):
    if not simulator:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    await simulator.emergency_stop()
    return {"ok": True}

# Reset simulation
@app.delete("/drones")
async def reset_simulation(token: str = Depends(verify_token)):
    if not simulator:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    
    await simulator.reset()
    return {"ok": True}

# Algorithm validation
@app.post("/validate/algorithm")
async def validate_algorithm(request: AlgorithmValidationRequest, token: str = Depends(verify_token)):
    if request.algorithm != "simple_collision_avoidance":
        raise HTTPException(status_code=400, detail="Unknown algorithm")
    
    results = []
    for test_case in request.testCases:
        start = test_case["start"]
        goal = test_case["goal"]
        obstacles = test_case.get("obstacles", [])
        
        import time
        start_time = time.time()
        path = planner.plan_path(start, goal, obstacles)
        planning_time = (time.time() - start_time) * 1000  # ms
        
        # Calculate metrics
        path_length = 0
        if len(path) > 1:
            for i in range(1, len(path)):
                dx = path[i][0] - path[i-1][0]
                dy = path[i][1] - path[i-1][1]
                dz = path[i][2] - path[i-1][2]
                path_length += (dx**2 + dy**2 + dz**2)**0.5
        
        results.append({
            "testCase": test_case,
            "path": path,
            "planningTimeMs": planning_time,
            "pathLengthM": path_length,
            "success": len(path) > 0
        })
    
    return {"results": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
