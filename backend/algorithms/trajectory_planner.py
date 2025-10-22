import math
from typing import List, Tuple, Dict, Any

class SimpleCollisionAvoidance:
    """
    Simple trajectory planner with basic collision avoidance.
    Uses straight-line paths with midpoint detours around obstacles.
    """
    
    def __init__(self, safety_radius: float = 0.3):
        self.safety_radius = safety_radius
    
    def plan_path(self, start: List[float], goal: List[float], obstacles: List[List[float]]) -> List[Tuple[float, float, float]]:
        """
        Plan a path from start to goal avoiding obstacles.
        
        Args:
            start: [x, y, z] starting position
            goal: [x, y, z] goal position
            obstacles: List of [x, y, z] obstacle positions
            
        Returns:
            List of waypoints as (x, y, z) tuples
        """
        start_point = (start[0], start[1], start[2])
        goal_point = (goal[0], goal[1], goal[2])
        
        # Check if direct path is clear
        if self._is_path_clear(start_point, goal_point, obstacles):
            return [start_point, goal_point]
        
        # Find detour around obstacles
        return self._find_detour_path(start_point, goal_point, obstacles)
    
    def _is_path_clear(self, start: Tuple[float, float, float], 
                      goal: Tuple[float, float, float], 
                      obstacles: List[List[float]]) -> bool:
        """Check if direct path from start to goal is clear of obstacles"""
        
        for obstacle in obstacles:
            obs_point = (obstacle[0], obstacle[1], obstacle[2])
            
            # Calculate distance from line segment to obstacle
            distance = self._point_to_line_distance(start, goal, obs_point)
            
            if distance < self.safety_radius:
                return False
        
        return True
    
    def _point_to_line_distance(self, line_start: Tuple[float, float, float],
                               line_end: Tuple[float, float, float],
                               point: Tuple[float, float, float]) -> float:
        """Calculate minimum distance from point to line segment"""
        
        # Vector from start to end
        line_vec = (line_end[0] - line_start[0], 
                   line_end[1] - line_start[1], 
                   line_end[2] - line_start[2])
        
        # Vector from start to point
        point_vec = (point[0] - line_start[0],
                   point[1] - line_start[1],
                   point[2] - line_start[2])
        
        # Length of line segment
        line_length_sq = line_vec[0]**2 + line_vec[1]**2 + line_vec[2]**2
        
        if line_length_sq == 0:
            # Line segment has zero length
            return math.sqrt(point_vec[0]**2 + point_vec[1]**2 + point_vec[2]**2)
        
        # Project point onto line
        t = max(0, min(1, (point_vec[0] * line_vec[0] + 
                          point_vec[1] * line_vec[1] + 
                          point_vec[2] * line_vec[2]) / line_length_sq))
        
        # Closest point on line segment
        closest_point = (line_start[0] + t * line_vec[0],
                        line_start[1] + t * line_vec[1],
                        line_start[2] + t * line_vec[2])
        
        # Distance from point to closest point on line
        dx = point[0] - closest_point[0]
        dy = point[1] - closest_point[1]
        dz = point[2] - closest_point[2]
        
        return math.sqrt(dx**2 + dy**2 + dz**2)
    
    def _find_detour_path(self, start: Tuple[float, float, float],
                         goal: Tuple[float, float, float],
                         obstacles: List[List[float]]) -> List[Tuple[float, float, float]]:
        """Find a detour path around obstacles using midpoint approach"""
        
        # Find the obstacle closest to the direct path
        closest_obstacle = None
        min_distance = float('inf')
        
        for obstacle in obstacles:
            obs_point = (obstacle[0], obstacle[1], obstacle[2])
            distance = self._point_to_line_distance(start, goal, obs_point)
            
            if distance < min_distance:
                min_distance = distance
                closest_obstacle = obs_point
        
        if closest_obstacle is None:
            return [start, goal]
        
        # Calculate midpoint detour
        midpoint = self._calculate_detour_midpoint(start, goal, closest_obstacle)
        
        # Check if detour segments are clear
        path1_clear = self._is_path_clear(start, midpoint, obstacles)
        path2_clear = self._is_path_clear(midpoint, goal, obstacles)
        
        if path1_clear and path2_clear:
            return [start, midpoint, goal]
        else:
            # Recursive detour if needed
            if not path1_clear:
                detour1 = self._find_detour_path(start, midpoint, obstacles)
            else:
                detour1 = [start, midpoint]
            
            if not path2_clear:
                detour2 = self._find_detour_path(midpoint, goal, obstacles)
            else:
                detour2 = [midpoint, goal]
            
            # Combine detours (remove duplicate midpoint)
            return detour1[:-1] + detour2
    
    def _calculate_detour_midpoint(self, start: Tuple[float, float, float],
                                  goal: Tuple[float, float, float],
                                  obstacle: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Calculate a detour midpoint around an obstacle"""
        
        # Vector from start to goal
        goal_vec = (goal[0] - start[0], goal[1] - start[1], goal[2] - start[2])
        
        # Vector from start to obstacle
        obs_vec = (obstacle[0] - start[0], obstacle[1] - start[1], obstacle[2] - start[2])
        
        # Project obstacle onto goal line
        goal_length_sq = goal_vec[0]**2 + goal_vec[1]**2 + goal_vec[2]**2
        
        if goal_length_sq == 0:
            # Goal is at start position
            return start
        
        t = (obs_vec[0] * goal_vec[0] + obs_vec[1] * goal_vec[1] + obs_vec[2] * goal_vec[2]) / goal_length_sq
        t = max(0, min(1, t))  # Clamp to [0, 1]
        
        # Projected point on line
        projected = (start[0] + t * goal_vec[0],
                    start[1] + t * goal_vec[1],
                    start[2] + t * goal_vec[2])
        
        # Vector from projected point to obstacle
        offset_vec = (obstacle[0] - projected[0],
                    obstacle[1] - projected[1],
                    obstacle[2] - projected[2])
        
        # Calculate perpendicular direction
        perpendicular = self._cross_product(goal_vec, offset_vec)
        perpendicular_length = math.sqrt(perpendicular[0]**2 + perpendicular[1]**2 + perpendicular[2]**2)
        
        if perpendicular_length == 0:
            # Vectors are parallel, use arbitrary perpendicular
            perpendicular = (0, 0, 1) if goal_vec[2] == 0 else (1, 0, 0)
            perpendicular_length = 1
        
        # Normalize perpendicular vector
        perpendicular = (perpendicular[0] / perpendicular_length,
                        perpendicular[1] / perpendicular_length,
                        perpendicular[2] / perpendicular_length)
        
        # Calculate detour distance
        detour_distance = self.safety_radius * 1.5  # Add some margin
        
        # Detour midpoint
        detour_point = (projected[0] + detour_distance * perpendicular[0],
                       projected[1] + detour_distance * perpendicular[1],
                       projected[2] + detour_distance * perpendicular[2])
        
        return detour_point
    
    def _cross_product(self, a: Tuple[float, float, float], 
                      b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Calculate cross product of two 3D vectors"""
        return (a[1] * b[2] - a[2] * b[1],
                a[2] * b[0] - a[0] * b[2],
                a[0] * b[1] - a[1] * b[0])
    
    def validate_path(self, path: List[Tuple[float, float, float]], 
                     obstacles: List[List[float]]) -> Dict[str, Any]:
        """
        Validate a planned path for safety and efficiency.
        
        Returns:
            Dictionary with validation metrics
        """
        if len(path) < 2:
            return {
                "valid": False,
                "reason": "Path too short",
                "pathLength": 0,
                "minSeparation": float('inf'),
                "success": False
            }
        
        # Calculate path length
        path_length = 0
        for i in range(1, len(path)):
            dx = path[i][0] - path[i-1][0]
            dy = path[i][1] - path[i-1][1]
            dz = path[i][2] - path[i-1][2]
            path_length += math.sqrt(dx**2 + dy**2 + dz**2)
        
        # Calculate minimum separation from obstacles
        min_separation = float('inf')
        for i in range(len(path) - 1):
            for obstacle in obstacles:
                obs_point = (obstacle[0], obstacle[1], obstacle[2])
                distance = self._point_to_line_distance(path[i], path[i+1], obs_point)
                min_separation = min(min_separation, distance)
        
        # Check if path is safe
        safe = min_separation >= self.safety_radius
        
        return {
            "valid": safe,
            "pathLength": path_length,
            "minSeparation": min_separation,
            "success": safe,
            "waypoints": len(path)
        }
