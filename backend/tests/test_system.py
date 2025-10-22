import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from backend.algorithms.trajectory_planner import SimpleCollisionAvoidance
from backend.simulators.mock_simulator import DroneSimulator, DroneState, DroneStatus

class TestSimpleCollisionAvoidance:
    """Test cases for the SimpleCollisionAvoidance trajectory planner"""
    
    def setup_method(self):
        self.planner = SimpleCollisionAvoidance(safety_radius=0.3)
    
    def test_straight_line_path_clear(self):
        """Test planning a straight line when path is clear"""
        start = [0.0, 0.0, 0.5]
        goal = [2.0, 0.0, 0.5]
        obstacles = []
        
        path = self.planner.plan_path(start, goal, obstacles)
        
        assert len(path) == 2
        assert path[0] == (0.0, 0.0, 0.5)
        assert path[1] == (2.0, 0.0, 0.5)
    
    def test_detour_around_obstacle(self):
        """Test planning a detour around a single obstacle"""
        start = [0.0, 0.0, 0.5]
        goal = [2.0, 0.0, 0.5]
        obstacles = [[1.0, 0.0, 0.5]]  # Obstacle in the middle
        
        path = self.planner.plan_path(start, goal, obstacles)
        
        assert len(path) >= 3  # Should have at least start, detour, goal
        assert path[0] == (0.0, 0.0, 0.5)
        assert path[-1] == (2.0, 0.0, 0.5)
        
        # Check that detour point is not too close to obstacle
        for point in path[1:-1]:
            dx = point[0] - obstacles[0][0]
            dy = point[1] - obstacles[0][1]
            dz = point[2] - obstacles[0][2]
            distance = (dx**2 + dy**2 + dz**2)**0.5
            assert distance >= self.planner.safety_radius
    
    def test_multiple_obstacles(self):
        """Test planning around multiple obstacles"""
        start = [0.0, 0.0, 0.5]
        goal = [3.0, 0.0, 0.5]
        obstacles = [[1.0, 0.0, 0.5], [2.0, 0.0, 0.5]]
        
        path = self.planner.plan_path(start, goal, obstacles)
        
        assert len(path) >= 3
        assert path[0] == (0.0, 0.0, 0.5)
        assert path[-1] == (3.0, 0.0, 0.5)
    
    def test_path_validation_success(self):
        """Test path validation for a valid path"""
        path = [(0.0, 0.0, 0.5), (1.0, 0.0, 0.5), (2.0, 0.0, 0.5)]
        obstacles = []
        
        result = self.planner.validate_path(path, obstacles)
        
        assert result["valid"] == True
        assert result["success"] == True
        assert result["pathLength"] > 0
        assert result["minSeparation"] == float('inf')
    
    def test_path_validation_collision(self):
        """Test path validation detects collision"""
        path = [(0.0, 0.0, 0.5), (1.0, 0.0, 0.5), (2.0, 0.0, 0.5)]
        obstacles = [[1.0, 0.0, 0.5]]  # Obstacle on path
        
        result = self.planner.validate_path(path, obstacles)
        
        assert result["valid"] == False
        assert result["success"] == False
        assert result["minSeparation"] < self.planner.safety_radius
    
    def test_empty_path_validation(self):
        """Test validation of empty path"""
        path = []
        obstacles = []
        
        result = self.planner.validate_path(path, obstacles)
        
        assert result["valid"] == False
        assert result["reason"] == "Path too short"
        assert result["success"] == False
    
    def test_safety_radius_enforcement(self):
        """Test that safety radius is properly enforced"""
        start = [0.0, 0.0, 0.5]
        goal = [1.0, 0.0, 0.5]
        obstacles = [[0.5, 0.0, 0.5]]  # Obstacle at midpoint
        
        path = self.planner.plan_path(start, goal, obstacles)
        
        # Check all detour points maintain safety radius
        for point in path[1:-1]:
            dx = point[0] - obstacles[0][0]
            dy = point[1] - obstacles[0][1]
            dz = point[2] - obstacles[0][2]
            distance = (dx**2 + dy**2 + dz**2)**0.5
            assert distance >= self.planner.safety_radius

class TestDroneSimulator:
    """Test cases for the DroneSimulator state machine and physics"""
    
    def setup_method(self):
        self.simulator = DroneSimulator()
    
    @pytest.mark.asyncio
    async def test_drone_creation(self):
        """Test creating a swarm of drones"""
        run_id = "test_run"
        count = 3
        
        drone_ids = await self.simulator.create_swarm(count, run_id)
        
        assert len(drone_ids) == count
        assert all(id.startswith('d') for id in drone_ids)
        assert len(self.simulator.drones) == count
        
        # Check initial states
        for drone_id in drone_ids:
            drone = self.simulator.drones[drone_id]
            assert drone.status == DroneStatus.IDLE
            assert drone.battery == 100.0
            assert drone.x == 0.0 and drone.y == 0.0 and drone.z == 0.0
    
    @pytest.mark.asyncio
    async def test_takeoff_state_transition(self):
        """Test takeoff state machine transition"""
        run_id = "test_run"
        drone_ids = await self.simulator.create_swarm(1, run_id)
        drone_id = drone_ids[0]
        
        # Start takeoff
        success = await self.simulator.takeoff(drone_id, 0.6, 2.0)
        assert success == True
        
        drone = self.simulator.drones[drone_id]
        assert drone.status == DroneStatus.TAKING_OFF
        assert drone.takeoff_height == 0.6
        assert drone.takeoff_duration == 2.0
    
    @pytest.mark.asyncio
    async def test_goto_command(self):
        """Test goto command sets target position"""
        run_id = "test_run"
        drone_ids = await self.simulator.create_swarm(1, run_id)
        drone_id = drone_ids[0]
        
        # Set drone to flying state first
        drone = self.simulator.drones[drone_id]
        drone.status = DroneStatus.FLYING
        
        # Send goto command
        success = await self.simulator.goto(drone_id, 1.0, 0.5, 0.6, 0.5)
        assert success == True
        
        assert drone.target_x == 1.0
        assert drone.target_y == 0.5
        assert drone.target_z == 0.6
    
    @pytest.mark.asyncio
    async def test_land_command(self):
        """Test land command transitions to landing state"""
        run_id = "test_run"
        drone_ids = await self.simulator.create_swarm(1, run_id)
        drone_id = drone_ids[0]
        
        # Set drone to flying state first
        drone = self.simulator.drones[drone_id]
        drone.status = DroneStatus.FLYING
        
        # Send land command
        success = await self.simulator.land(drone_id)
        assert success == True
        
        assert drone.status == DroneStatus.LANDING
    
    @pytest.mark.asyncio
    async def test_emergency_stop(self):
        """Test emergency stop stops all motion"""
        run_id = "test_run"
        drone_ids = await self.simulator.create_swarm(2, run_id)
        
        # Set drones to flying state
        for drone_id in drone_ids:
            drone = self.simulator.drones[drone_id]
            drone.status = DroneStatus.FLYING
            drone.vx = 0.5
            drone.vy = 0.3
            drone.vz = 0.1
        
        # Emergency stop
        await self.simulator.emergency_stop()
        
        # Check all drones stopped
        for drone_id in drone_ids:
            drone = self.simulator.drones[drone_id]
            assert drone.vx == 0.0
            assert drone.vy == 0.0
            assert drone.vz == 0.0
            assert drone.status == DroneStatus.IDLE
    
    @pytest.mark.asyncio
    async def test_battery_drain(self):
        """Test battery drains over time"""
        run_id = "test_run"
        drone_ids = await self.simulator.create_swarm(1, run_id)
        drone_id = drone_ids[0]
        
        initial_battery = self.simulator.drones[drone_id].battery
        
        # Simulate time passing
        await self.simulator._update_drones()
        
        # Battery should have decreased
        new_battery = self.simulator.drones[drone_id].battery
        assert new_battery < initial_battery
    
    @pytest.mark.asyncio
    async def test_bounds_checking(self):
        """Test workspace bounds enforcement"""
        run_id = "test_run"
        drone_ids = await self.simulator.create_swarm(1, run_id)
        drone_id = drone_ids[0]
        
        drone = self.simulator.drones[drone_id]
        
        # Move drone outside bounds
        drone.x = 3.0  # Outside 2.0m bounds
        drone.status = DroneStatus.FLYING
        
        # Update should detect bounds violation
        await self.simulator._update_drones()
        
        assert drone.status == DroneStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_formation_calculation(self):
        """Test formation position calculations"""
        run_id = "test_run"
        drone_ids = await self.simulator.create_swarm(4, run_id)
        
        # Set drones to flying state
        for drone_id in drone_ids:
            drone = self.simulator.drones[drone_id]
            drone.status = DroneStatus.FLYING
        
        # Test circle formation
        success = await self.simulator.set_formation("circle", {"radius": 1.0, "height": 0.6})
        assert success == True
        
        # Check that targets are set
        positions = []
        for drone_id in drone_ids:
            drone = self.simulator.drones[drone_id]
            positions.append((drone.target_x, drone.target_y, drone.target_z))
        
        # Verify circle formation
        assert len(positions) == 4
        # All positions should be at correct height
        assert all(pos[2] == 0.6 for pos in positions)
    
    @pytest.mark.asyncio
    async def test_experiment_execution(self):
        """Test experiment scenario execution"""
        # Mock time.sleep to avoid actual delays
        with patch('asyncio.sleep'):
            result = await self.simulator.run_experiment(
                "takeoff_hover_land", 
                2, 
                5, 
                {"height": 0.6}
            )
        
        assert result["scenario"] == "takeoff_hover_land"
        assert result["success"] == True
        assert "runId" in result
    
    @pytest.mark.asyncio
    async def test_reset_functionality(self):
        """Test simulation reset clears all state"""
        run_id = "test_run"
        drone_ids = await self.simulator.create_swarm(2, run_id)
        
        # Verify drones exist
        assert len(self.simulator.drones) == 2
        
        # Reset simulation
        await self.simulator.reset()
        
        # Verify drones cleared
        assert len(self.simulator.drones) == 0

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.asyncio
    async def test_planner_integration(self):
        """Test trajectory planner integration with simulator"""
        planner = SimpleCollisionAvoidance()
        simulator = DroneSimulator()
        
        # Create test scenario
        start = [0.0, 0.0, 0.5]
        goal = [2.0, 0.0, 0.5]
        obstacles = [[1.0, 0.0, 0.5]]
        
        # Plan path
        path = planner.plan_path(start, goal, obstacles)
        
        # Validate path
        validation = planner.validate_path(path, obstacles)
        
        assert validation["success"] == True
        assert len(path) >= 3  # Should have detour
    
    @pytest.mark.asyncio
    async def test_state_machine_integration(self):
        """Test complete state machine flow"""
        simulator = DroneSimulator()
        
        # Create drone
        run_id = "integration_test"
        drone_ids = await simulator.create_swarm(1, run_id)
        drone_id = drone_ids[0]
        
        # Test complete flow: idle -> takeoff -> flying -> land -> idle
        assert simulator.drones[drone_id].status == DroneStatus.IDLE
        
        # Takeoff
        await simulator.takeoff(drone_id, 0.6, 1.0)
        assert simulator.drones[drone_id].status == DroneStatus.TAKING_OFF
        
        # Simulate takeoff completion
        drone = simulator.drones[drone_id]
        drone.takeoff_start = time.time() - 2.0  # Simulate 2 seconds ago
        await simulator._update_takeoff(drone, time.time())
        assert drone.status == DroneStatus.FLYING
        
        # Land
        await simulator.land(drone_id)
        assert drone.status == DroneStatus.LANDING
        
        # Simulate landing completion
        drone.z = 0.0
        await simulator._update_landing(drone, time.time())
        assert drone.status == DroneStatus.IDLE

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
