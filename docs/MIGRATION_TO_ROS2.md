# Migration to ROS 2 and Crazyswarm2

This guide covers migrating the Crazyflie Swarm Demo from the mock simulator to production ROS 2 and Crazyswarm2 integration.

## Overview

The migration involves replacing the mock simulator backend with a ROS 2 adapter that interfaces with Crazyswarm2, while maintaining the same REST API contract and frontend interface.

## Prerequisites

### Hardware Requirements
- Crazyflie 2.1 drones (minimum 2, recommended 4+)
- Crazyradio PA USB dongles (one per drone)
- Computer with Ubuntu 20.04+ or ROS 2 Humble
- Adequate workspace (minimum 3x3 meters)

### Software Requirements
- ROS 2 Humble
- Python 3.10+
- Crazyswarm2
- Crazyflie client tools
- Docker (optional)

## Step 1: Environment Setup

### Install ROS 2 Humble
```bash
# Add ROS 2 repository
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Install ROS 2
sudo apt update
sudo apt upgrade -y
sudo apt install ros-humble-desktop python3-argcomplete python3-colcon-common-extensions python3-rosdep python3-vcstool -y

# Initialize rosdep
sudo rosdep init
rosdep update

# Source ROS 2
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Install Crazyswarm2
```bash
# Create workspace
mkdir -p ~/crazyflie_ws/src
cd ~/crazyflie_ws/src

# Clone Crazyswarm2
git clone https://github.com/USC-ACTLab/crazyswarm2.git
cd crazyswarm2

# Install dependencies
rosdep install --from-paths . -r -y

# Build
cd ~/crazyflie_ws
colcon build

# Source workspace
echo "source ~/crazyflie_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Install Crazyflie Tools
```bash
# Install Python dependencies
pip3 install cflib crazyflie-lib-python

# Install client tools
pip3 install cfclient

# Install firmware build tools
sudo apt install stm32flash
```

## Step 2: Hardware Setup

### Flash Firmware
```bash
# Navigate to firmware directory
cd /path/to/crazyflie-swarm-demo/firmware

# Build firmware
./build.sh

# Flash to each drone
./flash.sh /dev/ttyUSB0
```

### Configure Radio Channels
```bash
# Scan for drones
cfclient --scan

# Configure each drone with unique address
# Edit each drone's configuration to use different radio channels
```

### Test Individual Drones
```bash
# Test single drone
cfclient --connect

# Verify basic functionality:
# - Takeoff
# - Hover
# - Land
# - Emergency stop
```

## Step 3: Implement ROS 2 Adapter

### Create ROS 2 Node
```python
# backend/simulators/ros2_simulator.py
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from crazyswarm2_msgs.action import Takeoff, Land, GoTo
from crazyswarm2_msgs.srv import SetFormation
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
import asyncio
from typing import Dict, List, Optional, Any

class CrazySwarm2Adapter(Node):
    def __init__(self):
        super().__init__('crazyflie_swarm_adapter')
        
        # Create callback group for concurrent operations
        self.callback_group = ReentrantCallbackGroup()
        
        # Initialize action clients
        self.takeoff_clients = {}
        self.land_clients = {}
        self.goto_clients = {}
        
        # Initialize service clients
        self.formation_client = self.create_client(
            SetFormation, 
            'set_formation',
            callback_group=self.callback_group
        )
        
        # State subscribers
        self.pose_subscribers = {}
        self.state_subscribers = {}
        
        # Drone states
        self.drones = {}
        self.drone_states = {}
        
        self.get_logger().info('CrazySwarm2 adapter initialized')

    async def start(self):
        """Initialize ROS 2 node and connect to swarm"""
        rclpy.init()
        self.get_logger().info('Starting CrazySwarm2 adapter')
        self.running = True
        
        # Start ROS 2 executor in background
        self.executor = rclpy.executors.MultiThreadedExecutor()
        self.executor.add_node(self)
        
        # Start executor in background thread
        self.executor_thread = threading.Thread(target=self.executor.spin)
        self.executor_thread.daemon = True
        self.executor_thread.start()

    async def stop(self):
        """Shutdown ROS 2 node"""
        self.running = False
        if hasattr(self, 'executor'):
            self.executor.shutdown()
        rclpy.shutdown()

    async def create_swarm(self, count: int, run_id: str) -> List[str]:
        """Create swarm connection to real drones"""
        drone_ids = []
        
        # Discover available drones
        available_drones = await self.discover_drones()
        
        if len(available_drones) < count:
            raise Exception(f"Only {len(available_drones)} drones available, requested {count}")
        
        # Connect to requested number of drones
        for i in range(count):
            drone_id = available_drones[i]
            await self.connect_drone(drone_id)
            drone_ids.append(drone_id)
        
        return drone_ids

    async def discover_drones(self) -> List[str]:
        """Discover available Crazyflie drones"""
        # Use Crazyswarm2 discovery service
        discovery_client = self.create_client(
            'crazyswarm2/discover_drones',
            callback_group=self.callback_group
        )
        
        # Wait for service
        if not discovery_client.wait_for_service(timeout_sec=5.0):
            raise Exception("Discovery service not available")
        
        # Call discovery service
        request = String()
        future = discovery_client.call_async(request)
        
        # Wait for response
        rclpy.spin_until_future_complete(self, future)
        
        if future.result() is not None:
            response = future.result()
            return response.data.split(',')
        else:
            raise Exception("Failed to discover drones")

    async def connect_drone(self, drone_id: str):
        """Connect to a specific drone"""
        # Create action clients for this drone
        self.takeoff_clients[drone_id] = ActionClient(
            self, Takeoff, f'{drone_id}/takeoff',
            callback_group=self.callback_group
        )
        
        self.land_clients[drone_id] = ActionClient(
            self, Land, f'{drone_id}/land',
            callback_group=self.callback_group
        )
        
        self.goto_clients[drone_id] = ActionClient(
            self, GoTo, f'{drone_id}/goto',
            callback_group=self.callback_group
        )
        
        # Create pose subscriber
        self.pose_subscribers[drone_id] = self.create_subscription(
            PoseStamped,
            f'{drone_id}/pose',
            lambda msg, did=drone_id: self.pose_callback(msg, did),
            10,
            callback_group=self.callback_group
        )
        
        # Initialize drone state
        self.drone_states[drone_id] = {
            'id': drone_id,
            'x': 0.0, 'y': 0.0, 'z': 0.0,
            'vx': 0.0, 'vy': 0.0, 'vz': 0.0,
            'battery': 100.0,
            'status': 'idle'
        }
        
        self.get_logger().info(f'Connected to drone {drone_id}')

    def pose_callback(self, msg: PoseStamped, drone_id: str):
        """Update drone pose from ROS 2 topic"""
        if drone_id in self.drone_states:
            self.drone_states[drone_id]['x'] = msg.pose.position.x
            self.drone_states[drone_id]['y'] = msg.pose.position.y
            self.drone_states[drone_id]['z'] = msg.pose.position.z
            
            # Calculate velocity (simplified)
            # In production, you'd use proper velocity estimation
            self.drone_states[drone_id]['vx'] = 0.0
            self.drone_states[drone_id]['vy'] = 0.0
            self.drone_states[drone_id]['vz'] = 0.0

    async def takeoff(self, drone_id: str, height: float, duration: float) -> bool:
        """Send takeoff command to real drone"""
        if drone_id not in self.takeoff_clients:
            return False
        
        try:
            # Create takeoff goal
            goal = Takeoff.Goal()
            goal.height = height
            goal.duration = duration
            
            # Send goal
            future = self.takeoff_clients[drone_id].send_goal_async(goal)
            rclpy.spin_until_future_complete(self, future)
            
            goal_handle = future.result()
            if not goal_handle.accepted:
                return False
            
            # Wait for result
            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, result_future)
            
            result = result_future.result().result
            return result.success
            
        except Exception as e:
            self.get_logger().error(f'Takeoff failed for {drone_id}: {e}')
            return False

    async def goto(self, drone_id: str, x: float, y: float, z: float, speed: float) -> bool:
        """Send goto command to real drone"""
        if drone_id not in self.goto_clients:
            return False
        
        try:
            # Create goto goal
            goal = GoTo.Goal()
            goal.goal.position.x = x
            goal.goal.position.y = y
            goal.goal.position.z = z
            goal.duration = 0.0  # Let Crazyswarm2 calculate duration
            
            # Send goal
            future = self.goto_clients[drone_id].send_goal_async(goal)
            rclpy.spin_until_future_complete(self, future)
            
            goal_handle = future.result()
            if not goal_handle.accepted:
                return False
            
            return True
            
        except Exception as e:
            self.get_logger().error(f'Goto failed for {drone_id}: {e}')
            return False

    async def land(self, drone_id: str) -> bool:
        """Send land command to real drone"""
        if drone_id not in self.land_clients:
            return False
        
        try:
            # Create land goal
            goal = Land.Goal()
            
            # Send goal
            future = self.land_clients[drone_id].send_goal_async(goal)
            rclpy.spin_until_future_complete(self, future)
            
            goal_handle = future.result()
            if not goal_handle.accepted:
                return False
            
            # Wait for result
            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, result_future)
            
            result = result_future.result().result
            return result.success
            
        except Exception as e:
            self.get_logger().error(f'Land failed for {drone_id}: {e}')
            return False

    async def set_formation(self, formation: str, parameters: Dict[str, Any]) -> bool:
        """Set formation using Crazyswarm2 formation controller"""
        try:
            # Create formation request
            request = SetFormation.Request()
            request.formation = formation
            request.parameters = str(parameters)
            
            # Call service
            future = self.formation_client.call_async(request)
            rclpy.spin_until_future_complete(self, future)
            
            response = future.result()
            return response.success
            
        except Exception as e:
            self.get_logger().error(f'Formation failed: {e}')
            return False

    async def get_all_states(self) -> Dict[str, Any]:
        """Get states from real drones via ROS 2 topics"""
        return self.drone_states.copy()

    async def get_drone_state(self, drone_id: str) -> Optional[Dict[str, Any]]:
        """Get state of specific drone"""
        return self.drone_states.get(drone_id)

    async def emergency_stop(self):
        """Emergency stop all drones"""
        # Use Crazyswarm2 emergency stop service
        emergency_client = self.create_client(
            'crazyswarm2/emergency_stop',
            callback_group=self.callback_group
        )
        
        if emergency_client.wait_for_service(timeout_sec=1.0):
            request = String()
            future = emergency_client.call_async(request)
            rclpy.spin_until_future_complete(self, future)

    async def reset(self):
        """Reset swarm state"""
        self.drones.clear()
        self.drone_states.clear()
        
        # Clear action clients
        for client in self.takeoff_clients.values():
            client.destroy()
        for client in self.land_clients.values():
            client.destroy()
        for client in self.goto_clients.values():
            client.destroy()
        
        self.takeoff_clients.clear()
        self.land_clients.clear()
        self.goto_clients.clear()

    async def run_experiment(self, scenario: str, num_drones: int, duration: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run experiment with real drones"""
        try:
            # Create swarm
            run_id = f"{scenario}_{int(time.time())}"
            drone_ids = await self.create_swarm(num_drones, run_id)
            
            # Execute scenario
            if scenario == "circular_formation":
                return await self._run_circular_formation(drone_ids, duration, parameters)
            elif scenario == "figure_eight":
                return await self._run_figure_eight(drone_ids, duration, parameters)
            elif scenario == "takeoff_hover_land":
                return await self._run_takeoff_hover_land(drone_ids, duration, parameters)
            else:
                return {"error": f"Unknown scenario: {scenario}"}
                
        except Exception as e:
            return {"error": str(e)}

    async def _run_circular_formation(self, drone_ids: List[str], duration: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run circular formation experiment with real drones"""
        radius = parameters.get("radius", 1.0)
        height = parameters.get("height", 0.5)
        
        # Takeoff all drones
        for drone_id in drone_ids:
            await self.takeoff(drone_id, height, 2.0)
        
        await asyncio.sleep(3)  # Wait for takeoff
        
        # Set circular formation
        await self.set_formation("circle", {"radius": radius, "height": height})
        
        # Let it run for specified duration
        await asyncio.sleep(duration)
        
        # Land all drones
        for drone_id in drone_ids:
            await self.land(drone_id)
        
        return {
            "scenario": "circular_formation",
            "runId": f"circular_{int(time.time())}",
            "duration": duration,
            "success": True
        }

    async def _run_figure_eight(self, drone_ids: List[str], duration: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run figure-8 trajectory experiment with real drones"""
        if len(drone_ids) < 1:
            return {"error": "Need at least 1 drone for figure-8"}
        
        # Takeoff first drone
        await self.takeoff(drone_ids[0], 0.6, 2.0)
        await asyncio.sleep(3)
        
        # Simple figure-8 waypoints
        waypoints = [
            (0.0, 0.0, 0.6),
            (1.0, 0.5, 0.6),
            (0.0, 1.0, 0.6),
            (-1.0, 0.5, 0.6),
            (0.0, 0.0, 0.6)
        ]
        
        for waypoint in waypoints:
            await self.goto(drone_ids[0], waypoint[0], waypoint[1], waypoint[2], 0.5)
            await asyncio.sleep(duration / len(waypoints))
        
        # Land
        await self.land(drone_ids[0])
        
        return {
            "scenario": "figure_eight",
            "runId": f"figure8_{int(time.time())}",
            "duration": duration,
            "success": True
        }

    async def _run_takeoff_hover_land(self, drone_ids: List[str], duration: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run takeoff-hover-land experiment with real drones"""
        height = parameters.get("height", 0.6)
        
        # Takeoff all
        for drone_id in drone_ids:
            await self.takeoff(drone_id, height, 2.0)
        
        await asyncio.sleep(3)
        
        # Hover for duration
        await asyncio.sleep(duration)
        
        # Land all
        for drone_id in drone_ids:
            await self.land(drone_id)
        
        return {
            "scenario": "takeoff_hover_land",
            "runId": f"hover_{int(time.time())}",
            "duration": duration,
            "success": True
        }
```

## Step 4: Update Backend Configuration

### Modify main.py
```python
# In backend/main.py, update the startup event
@app.on_event("startup")
async def startup_event():
    global simulator
    
    if BACKEND == "mock":
        from simulators.mock_simulator import DroneSimulator
        simulator = DroneSimulator()
        await simulator.start()
    elif BACKEND == "crazyswarm2":
        from simulators.ros2_simulator import CrazySwarm2Adapter
        simulator = CrazySwarm2Adapter()
        await simulator.start()
    else:
        raise ValueError(f"Unknown backend: {BACKEND}")
```

### Update Environment Variables
```bash
# Set backend to ROS 2
export BACKEND=crazyswarm2

# Optional: Set ROS 2 specific variables
export ROS_DOMAIN_ID=0
export ROS_DISCOVERY_SERVER=""
```

## Step 5: Testing and Validation

### Test Individual Components
```bash
# Test ROS 2 node
ros2 run crazyflie_swarm_demo ros2_simulator

# Test Crazyswarm2 services
ros2 service list | grep crazyswarm2

# Test drone connection
ros2 topic echo /cf1/pose
```

### Test API Integration
```bash
# Start backend with ROS 2
cd backend
BACKEND=crazyswarm2 uvicorn main:app --host 0.0.0.0 --port 8000

# Test API endpoints
curl -H "Authorization: Bearer demo-token" \
     -H "Content-Type: application/json" \
     -d '{"count": 2}' \
     http://localhost:8000/drones/create
```

### Test Frontend Integration
```bash
# Update frontend API URL
# In frontend/js/api.js, update getBaseURL() to point to your backend

# Test complete system
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

## Step 6: Production Deployment

### Docker Configuration
```dockerfile
# Dockerfile.ros2
FROM ros:humble

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install fastapi uvicorn cflib

# Copy application
WORKDIR /app
COPY backend/ .

# Source ROS 2
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

# Run application
CMD ["bash", "-c", "source /opt/ros/humble/setup.bash && uvicorn main:app --host 0.0.0.0 --port 8000"]
```

### Deployment Script
```bash
#!/bin/bash
# deploy-ros2.sh

# Build Docker image
docker build -f Dockerfile.ros2 -t crazyflie-demo-ros2 .

# Deploy to Railway
railway login
railway init
railway variables set BACKEND=crazyswarm2
railway variables set ROS_DOMAIN_ID=0
railway deploy
```

## Troubleshooting

### Common Issues

1. **ROS 2 Node Not Starting**:
   ```bash
   # Check ROS 2 installation
   ros2 --version
   
   # Source environment
   source /opt/ros/humble/setup.bash
   
   # Check node
   ros2 node list
   ```

2. **Drone Connection Issues**:
   ```bash
   # Check radio connection
   cfclient --scan
   
   # Check ROS 2 topics
   ros2 topic list
   ros2 topic echo /cf1/pose
   ```

3. **Action Client Timeouts**:
   - Increase timeout values
   - Check drone battery levels
   - Verify radio signal strength

4. **Formation Service Errors**:
   - Ensure Crazyswarm2 formation controller is running
   - Check service availability
   - Verify formation parameters

### Debug Tools

```bash
# ROS 2 debugging
ros2 node info /crazyflie_swarm_adapter
ros2 service call /crazyswarm2/discover_drones std_msgs/String

# Crazyswarm2 debugging
ros2 launch crazyswarm2 teleop.launch
ros2 run crazyswarm2_client client

# Network debugging
ros2 topic hz /cf1/pose
ros2 topic bw /cf1/pose
```

## Performance Considerations

### Optimization Tips

1. **Reduce Latency**:
   - Use local ROS 2 domain
   - Optimize message frequencies
   - Implement connection pooling

2. **Improve Reliability**:
   - Add retry logic for failed operations
   - Implement health checks
   - Monitor battery levels

3. **Scale Performance**:
   - Use multiple ROS 2 nodes
   - Implement load balancing
   - Cache frequently accessed data

## Conclusion

This migration guide provides a comprehensive path from the mock simulator to production ROS 2 and Crazyswarm2 integration. The key is maintaining the same API contract while leveraging the full capabilities of the ROS 2 ecosystem for real drone control.

The modular design allows for gradual migration, testing individual components before full integration, and provides fallback options if issues arise during the transition.
