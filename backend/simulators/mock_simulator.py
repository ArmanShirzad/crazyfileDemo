import asyncio
import sqlite3
import json
import math
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class DroneStatus(Enum):
    IDLE = "idle"
    TAKING_OFF = "takingOff"
    FLYING = "flying"
    LANDING = "landing"
    ERROR = "error"

@dataclass
class DroneState:
    id: str
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    battery: float = 100.0
    status: DroneStatus = DroneStatus.IDLE
    target_x: float = 0.0
    target_y: float = 0.0
    target_z: float = 0.0
    takeoff_height: float = 0.0
    takeoff_start: float = 0.0
    takeoff_duration: float = 0.0
    land_start: float = 0.0
    last_update: float = 0.0

class DroneSimulator:
    def __init__(self):
        self.drones: Dict[str, DroneState] = {}
        self.running = False
        self.tick_rate = 20  # 20 Hz
        self.dt = 1.0 / self.tick_rate
        self.safety_radius = 0.3
        self.max_speed = 1.0
        self.max_height = 1.0
        self.workspace_bounds = 2.0  # 2x2x1 meter workspace
        
        # Physics constants
        self.gravity = 9.81
        self.max_acceleration = 2.0
        self.battery_drain_rate = 0.1  # % per second
        
        # Noise parameters
        self.position_noise_std = 0.01
        self.velocity_noise_std = 0.005
        
        self._task = None

    async def start(self):
        """Start the simulation loop"""
        self.running = True
        self._task = asyncio.create_task(self._simulation_loop())

    async def stop(self):
        """Stop the simulation loop"""
        self.running = False
        if self._task:
            await self._task

    async def _simulation_loop(self):
        """Main simulation loop running at 20Hz"""
        while self.running:
            start_time = time.time()
            
            # Update all drones
            await self._update_drones()
            
            # Log current states
            await self._log_states()
            
            # Sleep to maintain tick rate
            elapsed = time.time() - start_time
            sleep_time = max(0, self.dt - elapsed)
            await asyncio.sleep(sleep_time)

    async def _update_drones(self):
        """Update physics for all drones"""
        current_time = time.time()
        
        for drone in self.drones.values():
            # Update battery
            drone.battery = max(0, drone.battery - self.battery_drain_rate * self.dt)
            
            # Handle different states
            if drone.status == DroneStatus.TAKING_OFF:
                await self._update_takeoff(drone, current_time)
            elif drone.status == DroneStatus.FLYING:
                await self._update_flying(drone, current_time)
            elif drone.status == DroneStatus.LANDING:
                await self._update_landing(drone, current_time)
            
            # Apply noise to sensors
            drone.x += random.gauss(0, self.position_noise_std)
            drone.y += random.gauss(0, self.position_noise_std)
            drone.z += random.gauss(0, self.position_noise_std)
            drone.vx += random.gauss(0, self.velocity_noise_std)
            drone.vy += random.gauss(0, self.velocity_noise_std)
            drone.vz += random.gauss(0, self.velocity_noise_std)
            
            # Check for errors
            if drone.battery <= 0:
                drone.status = DroneStatus.ERROR
            elif (abs(drone.x) > self.workspace_bounds or 
                  abs(drone.y) > self.workspace_bounds or 
                  drone.z > self.max_height):
                drone.status = DroneStatus.ERROR
            
            drone.last_update = current_time

    async def _update_takeoff(self, drone: DroneState, current_time: float):
        """Update drone during takeoff phase"""
        elapsed = current_time - drone.takeoff_start
        
        if elapsed >= drone.takeoff_duration:
            # Takeoff complete
            drone.z = drone.takeoff_height
            drone.vz = 0.0
            drone.status = DroneStatus.FLYING
        else:
            # Smooth takeoff with acceleration
            progress = elapsed / drone.takeoff_duration
            target_z = drone.takeoff_height * progress
            
            # Simple PID-like control
            error = target_z - drone.z
            drone.vz = min(self.max_speed, max(-self.max_speed, error * 2.0))
            drone.z += drone.vz * self.dt

    async def _update_flying(self, drone: DroneState, current_time: float):
        """Update drone during flight"""
        # Move towards target position
        dx = drone.target_x - drone.x
        dy = drone.target_y - drone.y
        dz = drone.target_z - drone.z
        
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        
        if distance > 0.05:  # 5cm threshold
            # Normalize direction and apply speed limit
            speed_factor = min(1.0, distance / 0.1)  # Slow down when close
            target_speed = self.max_speed * speed_factor
            
            drone.vx = (dx / distance) * target_speed
            drone.vy = (dy / distance) * target_speed
            drone.vz = (dz / distance) * target_speed
            
            # Update position
            drone.x += drone.vx * self.dt
            drone.y += drone.vy * self.dt
            drone.z += drone.vz * self.dt
        else:
            # Close enough to target
            drone.vx = 0.0
            drone.vy = 0.0
            drone.vz = 0.0

    async def _update_landing(self, drone: DroneState, current_time: float):
        """Update drone during landing"""
        # Move towards ground
        target_z = 0.0
        dz = target_z - drone.z
        
        if abs(dz) > 0.05:
            drone.vz = min(self.max_speed, max(-self.max_speed, dz * 2.0))
            drone.z += drone.vz * self.dt
        else:
            # Landing complete
            drone.z = 0.0
            drone.vz = 0.0
            drone.status = DroneStatus.IDLE

    async def _log_states(self):
        """Log current states to database"""
        if not self.drones:
            return
        
        conn = sqlite3.connect('swarm_logs.db')
        cursor = conn.cursor()
        
        current_time = time.time()
        
        for drone in self.drones.values():
            cursor.execute('''
                INSERT INTO samples (runId, droneId, t, x, y, z, vx, vy, vz, battery, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                getattr(drone, 'run_id', 'default'),
                drone.id,
                current_time,
                drone.x,
                drone.y,
                drone.z,
                drone.vx,
                drone.vy,
                drone.vz,
                drone.battery,
                drone.status.value
            ))
        
        conn.commit()
        conn.close()

    async def create_swarm(self, count: int, run_id: str) -> List[str]:
        """Create a new swarm of drones"""
        drone_ids = []
        
        for i in range(count):
            drone_id = f"d{i+1}"
            drone = DroneState(id=drone_id)
            drone.run_id = run_id
            self.drones[drone_id] = drone
            drone_ids.append(drone_id)
        
        # Log the run
        conn = sqlite3.connect('swarm_logs.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO runs (id, name, startedAt, status)
            VALUES (?, ?, ?, ?)
        ''', (run_id, f"Swarm of {count} drones", datetime.now().isoformat(), "running"))
        conn.commit()
        conn.close()
        
        return drone_ids

    async def get_all_states(self) -> Dict[str, Any]:
        """Get current states of all drones"""
        return {
            drone_id: {
                "id": drone.id,
                "x": drone.x,
                "y": drone.y,
                "z": drone.z,
                "vx": drone.vx,
                "vy": drone.vy,
                "vz": drone.vz,
                "battery": drone.battery,
                "status": drone.status.value
            }
            for drone_id, drone in self.drones.items()
        }

    async def get_drone_state(self, drone_id: str) -> Optional[Dict[str, Any]]:
        """Get state of a specific drone"""
        if drone_id not in self.drones:
            return None
        
        drone = self.drones[drone_id]
        return {
            "id": drone.id,
            "x": drone.x,
            "y": drone.y,
            "z": drone.z,
            "vx": drone.vx,
            "vy": drone.vy,
            "vz": drone.vz,
            "battery": drone.battery,
            "status": drone.status.value
        }

    async def takeoff(self, drone_id: str, height: float, duration: float) -> bool:
        """Command drone to takeoff"""
        if drone_id not in self.drones:
            return False
        
        drone = self.drones[drone_id]
        if drone.status != DroneStatus.IDLE:
            return False
        
        drone.status = DroneStatus.TAKING_OFF
        drone.takeoff_height = height
        drone.takeoff_duration = duration
        drone.takeoff_start = time.time()
        
        return True

    async def goto(self, drone_id: str, x: float, y: float, z: float, speed: float) -> bool:
        """Command drone to move to position"""
        if drone_id not in self.drones:
            return False
        
        drone = self.drones[drone_id]
        if drone.status not in [DroneStatus.FLYING, DroneStatus.TAKING_OFF]:
            return False
        
        drone.target_x = x
        drone.target_y = y
        drone.target_z = z
        
        return True

    async def land(self, drone_id: str) -> bool:
        """Command drone to land"""
        if drone_id not in self.drones:
            return False
        
        drone = self.drones[drone_id]
        if drone.status not in [DroneStatus.FLYING, DroneStatus.TAKING_OFF]:
            return False
        
        drone.status = DroneStatus.LANDING
        drone.land_start = time.time()
        
        return True

    async def set_formation(self, formation: str, parameters: Dict[str, Any]) -> bool:
        """Set formation for all flying drones"""
        flying_drones = [d for d in self.drones.values() if d.status == DroneStatus.FLYING]
        
        if not flying_drones:
            return False
        
        positions = self._calculate_formation_positions(formation, len(flying_drones), parameters)
        
        for i, drone in enumerate(flying_drones):
            if i < len(positions):
                drone.target_x = positions[i][0]
                drone.target_y = positions[i][1]
                drone.target_z = positions[i][2]
        
        return True

    def _calculate_formation_positions(self, formation: str, count: int, parameters: Dict[str, Any]) -> List[Tuple[float, float, float]]:
        """Calculate positions for different formations"""
        positions = []
        
        if formation == "line":
            spacing = parameters.get("spacing", 0.5)
            for i in range(count):
                x = (i - (count-1)/2) * spacing
                positions.append((x, 0.0, 0.6))
        
        elif formation == "circle":
            radius = parameters.get("radius", 1.0)
            height = parameters.get("height", 0.6)
            for i in range(count):
                angle = 2 * math.pi * i / count
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                positions.append((x, y, height))
        
        elif formation == "grid":
            cols = int(math.ceil(math.sqrt(count)))
            spacing = parameters.get("spacing", 0.5)
            height = parameters.get("height", 0.6)
            for i in range(count):
                row = i // cols
                col = i % cols
                x = (col - (cols-1)/2) * spacing
                y = (row - (count//cols-1)/2) * spacing
                positions.append((x, y, height))
        
        elif formation == "vshape":
            spacing = parameters.get("spacing", 0.5)
            height = parameters.get("height", 0.6)
            for i in range(count):
                if i == 0:
                    positions.append((0.0, 0.0, height))
                else:
                    side = 1 if i % 2 == 1 else -1
                    row = (i + 1) // 2
                    x = row * spacing
                    y = side * row * spacing * 0.5
                    positions.append((x, y, height))
        
        return positions

    async def run_experiment(self, scenario: str, num_drones: int, duration: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run an automated experiment scenario"""
        if scenario == "circular_formation":
            return await self._run_circular_formation(num_drones, duration, parameters)
        elif scenario == "figure_eight":
            return await self._run_figure_eight(num_drones, duration, parameters)
        elif scenario == "takeoff_hover_land":
            return await self._run_takeoff_hover_land(num_drones, duration, parameters)
        else:
            return {"error": f"Unknown scenario: {scenario}"}

    async def _run_circular_formation(self, num_drones: int, duration: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run circular formation experiment"""
        radius = parameters.get("radius", 1.0)
        height = parameters.get("height", 0.5)
        
        # Create swarm
        run_id = f"circular_{int(time.time())}"
        drone_ids = await self.create_swarm(num_drones, run_id)
        
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
            "runId": run_id,
            "duration": duration,
            "success": True
        }

    async def _run_figure_eight(self, num_drones: int, duration: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run figure-8 trajectory experiment"""
        # For now, just move first drone in figure-8 pattern
        if num_drones < 1:
            return {"error": "Need at least 1 drone for figure-8"}
        
        run_id = f"figure8_{int(time.time())}"
        drone_ids = await self.create_swarm(num_drones, run_id)
        
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
            "runId": run_id,
            "duration": duration,
            "success": True
        }

    async def _run_takeoff_hover_land(self, num_drones: int, duration: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run takeoff-hover-land experiment"""
        height = parameters.get("height", 0.6)
        
        run_id = f"hover_{int(time.time())}"
        drone_ids = await self.create_swarm(num_drones, run_id)
        
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
            "runId": run_id,
            "duration": duration,
            "success": True
        }

    async def emergency_stop(self):
        """Emergency stop all drones"""
        for drone in self.drones.values():
            drone.vx = 0.0
            drone.vy = 0.0
            drone.vz = 0.0
            drone.status = DroneStatus.IDLE

    async def reset(self):
        """Reset simulation state"""
        self.drones.clear()
        
        # Clear database
        conn = sqlite3.connect('swarm_logs.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM samples')
        cursor.execute('DELETE FROM runs')
        conn.commit()
        conn.close()
