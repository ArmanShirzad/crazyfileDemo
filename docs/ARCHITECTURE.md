# Crazyflie Swarm Demo - Architecture Documentation

## Overview

The Crazyflie Swarm Demo implements a two-phase architecture designed to demonstrate first-week capabilities for IMRCLab while providing a clear migration path to production systems.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Web UI)                        │
├─────────────────────────────────────────────────────────────────┤
│  Three.js Visualization  │  Control Panel  │  Charts & Results  │
│  - 3D Drone Display      │  - Swarm Control│  - Position Charts  │
│  - Camera Controls       │  - Formation    │  - Battery Levels   │
│  - Real-time Updates     │  - Experiments  │  - Data Export      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP/REST API
                                │
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
├─────────────────────────────────────────────────────────────────┤
│  REST API Endpoints  │  Simulator Layer  │  Algorithm Layer     │
│  - /drones/create    │  - Mock Simulator │  - Collision Avoid   │
│  - /drones/takeoff   │  - ROS2 Adapter   │  - Path Planning     │
│  - /swarm/formation  │  - State Machine  │  - Validation        │
│  - /experiments/run  │  - Physics Engine │  - Metrics           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ Configuration Switch
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    Simulator Backends                          │
├─────────────────────────────────────────────────────────────────┤
│  Phase 1: Mock Simulator    │  Phase 2: ROS 2 Integration      │
│  - Pure Python              │  - Crazyswarm2 Adapter          │
│  - 20Hz Physics Loop        │  - ROS 2 Services/Actions       │
│  - SQLite Logging           │  - Real Hardware Control         │
│  - Gaussian Noise           │  - Gazebo Simulation            │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Mock Simulator (Current)

### Backend Components

#### FastAPI Application (`main.py`)
- **Purpose**: REST API server with authentication and CORS
- **Key Features**:
  - Bearer token authentication
  - Rate limiting and bounds checking
  - Emergency stop functionality
  - Health check endpoint

#### Mock Simulator (`simulators/mock_simulator.py`)
- **Purpose**: Pure Python physics simulation
- **Key Features**:
  - 20Hz simulation loop
  - Simple physics with acceleration limits
  - Battery drain simulation (~7 minutes)
  - Gaussian noise on sensors
  - Collision detection
  - Formation calculations

#### Trajectory Planner (`algorithms/trajectory_planner.py`)
- **Purpose**: Path planning with collision avoidance
- **Key Features**:
  - Straight-line path planning
  - Midpoint detour around obstacles
  - Safety radius enforcement
  - Path validation and metrics

### Frontend Components

#### Three.js Visualization (`js/visualization.js`)
- **Purpose**: 3D real-time visualization
- **Key Features**:
  - Drone models as colored cubes
  - Real-time position updates
  - Trail visualization
  - Camera controls (orbit, zoom, pan)
  - Status-based coloring

#### API Client (`js/api.js`)
- **Purpose**: Backend communication
- **Key Features**:
  - Automatic environment detection
  - Bearer token management
  - Error handling
  - Request/response formatting

#### Experiment Manager (`js/experiments.js`)
- **Purpose**: Experiment execution and data visualization
- **Key Features**:
  - Chart.js integration
  - Real-time data updates
  - CSV/JSON export
  - Metrics calculation

### Data Flow

1. **User Input**: Frontend captures user actions (takeoff, goto, formations)
2. **API Request**: JavaScript sends HTTP requests to FastAPI backend
3. **Authentication**: Backend validates bearer token
4. **Simulation**: Mock simulator updates drone states at 20Hz
5. **Database**: SQLite stores trajectory samples
6. **Response**: Backend returns success/failure status
7. **Visualization**: Frontend updates 3D display and charts
8. **Export**: Users can download trajectory data

## Phase 2: ROS 2 Integration (Future)

### Migration Strategy

#### Backend Swap
- **Configuration**: `BACKEND` environment variable switches between mock and ROS 2
- **Interface**: Same REST API endpoints maintained
- **Adapter Pattern**: `CrazySwarm2Adapter` implements same interface as `DroneSimulator`

#### ROS 2 Components
- **Node**: Python ROS 2 node with service/action clients
- **Services**: Map REST calls to Crazyswarm2 services
- **Topics**: Subscribe to drone state topics
- **Actions**: Handle long-running operations (takeoff, goto, land)

#### Hardware Integration
- **Real Drones**: Connect to actual Crazyflie hardware
- **Simulation**: Optional Gazebo integration
- **Communication**: Radio or USB connection

### Migration Steps

1. **Environment Setup**:
   ```bash
   export BACKEND=crazyswarm2
   ```

2. **Dependencies**:
   ```bash
   pip install rclpy crazyflie-lib-python
   ```

3. **Configuration**:
   - Update `ros2_simulator.py` with actual ROS 2 implementation
   - Configure Crazyswarm2 parameters
   - Set up hardware connections

4. **Testing**:
   - Single drone functionality
   - Swarm coordination
   - Performance validation

## Data Models

### Drone State
```python
{
    "id": "d1",
    "x": 0.0, "y": 0.0, "z": 0.6,
    "vx": 0.0, "vy": 0.0, "vz": 0.0,
    "battery": 85.2,
    "status": "flying"
}
```

### Experiment Result
```python
{
    "scenario": "circular_formation",
    "runId": "run_20231201_143022",
    "duration": 30,
    "success": True,
    "metrics": {
        "pathLength": 12.5,
        "flightTime": 30.0,
        "minSeparation": 0.3,
        "numDrones": 4
    }
}
```

### Trajectory Sample
```python
{
    "t": 1.5,
    "x": 0.1, "y": 0.2, "z": 0.6,
    "vx": 0.05, "vy": 0.1, "vz": 0.0,
    "battery": 84.8,
    "status": "flying",
    "droneId": "d1"
}
```

## Security Considerations

### Authentication
- Bearer token required for write operations
- Read operations (state, logs) are open for demo purposes
- Token validation on every request

### Input Validation
- Bounds checking on all position inputs
- Rate limiting on command endpoints
- Emergency stop always available

### Safety Features
- Workspace bounds enforcement
- Speed and acceleration limits
- Battery monitoring
- Collision detection

## Performance Characteristics

### Simulation Performance
- **Tick Rate**: 20Hz (50ms intervals)
- **Update Rate**: 10Hz client polling
- **Memory Usage**: ~50MB for 10 drones
- **CPU Usage**: ~10% on modern hardware

### Network Performance
- **API Response Time**: <100ms typical
- **WebSocket Alternative**: Could be added for real-time updates
- **Data Export**: CSV/JSON generation <1s for typical experiments

### Scalability
- **Max Drones**: 10 (configurable)
- **Concurrent Users**: 100+ (stateless design)
- **Database Size**: ~1MB per hour of simulation

## Deployment Architecture

### Development
```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
python -m http.server 3000
```

### Production
- **Backend**: Railway (containerized)
- **Frontend**: GitHub Pages (static)
- **Database**: SQLite (embedded)
- **Monitoring**: Health check endpoint

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Future Enhancements

### Phase 3: Advanced Features
- **Machine Learning**: Neural network path planning
- **Computer Vision**: Obstacle detection and avoidance
- **Advanced Formations**: Dynamic formations, leader-follower
- **Multi-Agent**: Distributed decision making

### Phase 4: Production Scale
- **Microservices**: Split into specialized services
- **Message Queues**: Redis/RabbitMQ for async processing
- **Distributed Simulation**: Multiple simulation nodes
- **Real-time Analytics**: Stream processing with Apache Kafka

## Troubleshooting

### Common Issues
1. **Connection Problems**: Check CORS settings and API URL
2. **Performance Issues**: Reduce tick rate or drone count
3. **Memory Leaks**: Restart simulation periodically
4. **Visualization Lag**: Reduce trail length or update frequency

### Debug Tools
- **Backend Logs**: FastAPI automatic logging
- **Browser Console**: JavaScript error tracking
- **Network Tab**: API request/response inspection
- **Database**: SQLite browser for data inspection

## Conclusion

This architecture provides a solid foundation for demonstrating swarm capabilities while maintaining flexibility for future enhancements. The clear separation between simulation and control layers enables easy migration to production systems without disrupting the user interface or API contracts.
