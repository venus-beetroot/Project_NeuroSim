from enum import Enum
import random
import math
import pygame
from typing import List, Tuple, Dict, Optional, Set

class Tile(Enum):
    """Enhanced tile enumeration with all tile types"""
    NATURE = 0
    CITY = 1
    ROAD = 2
    NATURE_FLOWER = 3
    NATURE_FLOWER_RED = 4
    NATURE_LOG = 5
    NATURE_BUSH = 6
    NATURE_ROCK = 7
    BUILDING = 8

class TileMap:
    """Clean tilemap implementation"""
    def __init__(self, width: int, height: int, default: Tile = Tile.NATURE):
        self.width = width
        self.height = height
        self.grid = [[default for _ in range(width)] for _ in range(height)]
        
        # Simplified grids
        self.city_tile_grid = [[0 for _ in range(width)] for _ in range(height)]
        self.path_tile_grid = [["base-city-tile-path" for _ in range(width)] for _ in range(height)]

    def set_tile(self, x: int, y: int, tile: Tile):
        """Set tile at position with bounds checking"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = tile

    def get_tile(self, x: int, y: int) -> Tile:
        """Get tile at position with bounds checking"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return Tile.NATURE  # Default for out of bounds

    def set_city_tile_type(self, x: int, y: int, tile_type: int):
        """Set city tile type for rendering"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.city_tile_grid[y][x] = tile_type

    def get_city_tile_type(self, x: int, y: int) -> int:
        """Get city tile type"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.city_tile_grid[y][x]
        return 0

    def set_path_tile_type(self, x: int, y: int, path_type: str):
        """Set path tile type for rendering"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.path_tile_grid[y][x] = path_type

    def get_path_tile_type(self, x: int, y: int) -> str:
        """Get path tile type"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.path_tile_grid[y][x]
        return ""

def line(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """Bresenham's line algorithm"""
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    x, y = x0, y0
    while True:
        points.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = err * 2
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    
    return points

def generate_rectangular_city(tilemap: TileMap, x0: int, y0: int, w: int, h: int):
    """Generate perfectly rectangular city with no blending"""
    for x in range(x0, x0 + w):
        for y in range(y0, y0 + h):
            if 0 <= x < tilemap.width and 0 <= y < tilemap.height:
                tilemap.set_tile(x, y, Tile.CITY)

def place_buildings(tilemap: TileMap, buildings: List[Dict]) -> List[Tuple[int, int]]:
    """Place buildings and return door positions"""
    doors = []
    for building in buildings:
        bx0, by0 = building['x0'], building['y0']
        bw, bh = building['w'], building['h']
        
        # Mark building area as BUILDING tiles
        for x in range(bx0, bx0 + bw):
            for y in range(by0, by0 + bh):
                if 0 <= x < tilemap.width and 0 <= y < tilemap.height:
                    tilemap.set_tile(x, y, Tile.BUILDING)
        
        # Calculate door position
        dx, dy = building.get('door_offset', (bw // 2, 0))
        door = (bx0 + dx, by0 + dy)
        doors.append(door)
    
    return doors

def connect_roads(tilemap: TileMap, doors: List[Tuple[int, int]], spine_y: int, 
                 road_width: int = 1) -> None:
    """Connect doors with roads to a main spine"""
    for door_x, door_y in doors:
        # Draw road from door to spine
        road_points = line(door_x, door_y, door_x, spine_y)
        
        for x, y in road_points:
            # Draw road with specified width
            for dx in range(-road_width//2, road_width//2 + 1):
                for dy in range(-road_width//2, road_width//2 + 1):
                    road_x, road_y = x + dx, y + dy
                    if 0 <= road_x < tilemap.width and 0 <= road_y < tilemap.height:
                        # Don't overwrite buildings
                        if tilemap.get_tile(road_x, road_y) != Tile.BUILDING:
                            tilemap.set_tile(road_x, road_y, Tile.ROAD)

def connect_points_with_roads(tilemap: TileMap, points: List[Tuple[int, int]], 
                             road_width: int = 3) -> None:
    """Connect multiple points with roads using minimum spanning tree"""
    if len(points) < 2:
        return
    
    # Simple MST implementation
    connected = set([0])  # Start with first point
    unconnected = set(range(1, len(points)))
    
    while unconnected:
        min_distance = float('inf')
        best_connection = None
        
        for connected_idx in connected:
            for unconnected_idx in unconnected:
                distance = math.sqrt(
                    (points[connected_idx][0] - points[unconnected_idx][0])**2 +
                    (points[connected_idx][1] - points[unconnected_idx][1])**2
                )
                if distance < min_distance:
                    min_distance = distance
                    best_connection = (connected_idx, unconnected_idx)
        
        if best_connection:
            # Draw road between points
            start_point = points[best_connection[0]]
            end_point = points[best_connection[1]]
            road_points = line(start_point[0], start_point[1], 
                             end_point[0], end_point[1])
            
            for x, y in road_points:
                # Draw road with specified width
                for dx in range(-road_width//2, road_width//2 + 1):
                    for dy in range(-road_width//2, road_width//2 + 1):
                        road_x, road_y = x + dx, y + dy
                        if 0 <= road_x < tilemap.width and 0 <= road_y < tilemap.height:
                            if tilemap.get_tile(road_x, road_y) != Tile.BUILDING:
                                tilemap.set_tile(road_x, road_y, Tile.ROAD)
            
            # Add to connected set
            connected.add(best_connection[1])
            unconnected.remove(best_connection[1])

def auto_tile_roads(tilemap: TileMap, pick_sprite_fn) -> None:
    """Auto-tile roads based on connectivity"""
    for x in range(tilemap.width):
        for y in range(tilemap.height):
            if tilemap.get_tile(x, y) != Tile.ROAD:
                continue
                
            # Calculate bitmask based on adjacent road tiles
            mask = 0
            # N=1, E=2, S=4, W=8
            if y + 1 < tilemap.height and tilemap.get_tile(x, y + 1) == Tile.ROAD:
                mask |= 1  # South
            if x + 1 < tilemap.width and tilemap.get_tile(x + 1, y) == Tile.ROAD:
                mask |= 2  # East
            if y - 1 >= 0 and tilemap.get_tile(x, y - 1) == Tile.ROAD:
                mask |= 4  # North
            if x - 1 >= 0 and tilemap.get_tile(x - 1, y) == Tile.ROAD:
                mask |= 8  # West
            
            # Get appropriate sprite for this configuration
            sprite = pick_sprite_fn(mask)
            tilemap.path_tile_grid[y][x] = sprite

def auto_tile_cities(tilemap: TileMap) -> None:
    """Simple city auto-tiling - just set all city tiles to type 0 (interior)"""
    for x in range(tilemap.width):
        for y in range(tilemap.height):
            if tilemap.get_tile(x, y) == Tile.CITY:
                tilemap.set_city_tile_type(x, y, 0)  # All city tiles use interior texture

def get_city_tile_type(neighbors: Dict[str, bool]) -> int:
    """Determine city tile type based on neighbors"""    
    # Define tile type constants
    INTERIOR = 0
    
    # Default fallback
    return INTERIOR

def add_nature_decorations(tilemap: TileMap, flower_chance: float = 0.03, 
                          log_chance: float = 0.003, rock_chance: float = 0.003, 
                          bush_chance: float = 0.002) -> None:
    """Add decorative elements to nature tiles"""
    # Add flower clusters
    num_clusters = 8
    clusters_placed = 0
    attempts = 0
    max_attempts = num_clusters * 10
    
    while clusters_placed < num_clusters and attempts < max_attempts:
        y = random.randint(2, tilemap.height - 3)
        x = random.randint(2, tilemap.width - 3)
        
        if tilemap.get_tile(x, y) != Tile.NATURE:
            attempts += 1
            continue
        
        cluster_tiles = []
        cluster_size = random.randint(3, 6)
        offsets = [(0, 0), (1, 0), (0, 1), (1, 1), (0, -1), (-1, 0), (-1, -1)]
        random.shuffle(offsets)
        
        for dx, dy in offsets:
            tx, ty = x + dx, y + dy
            if (0 <= tx < tilemap.width and 0 <= ty < tilemap.height and
                tilemap.get_tile(tx, ty) == Tile.NATURE):
                cluster_tiles.append((tx, ty))
                if len(cluster_tiles) >= cluster_size:
                    break
        
        if len(cluster_tiles) >= cluster_size:
            for tx, ty in cluster_tiles:
                tilemap.set_tile(tx, ty, random.choice([
                    Tile.NATURE_FLOWER,
                    Tile.NATURE_FLOWER_RED
                ]))
            clusters_placed += 1
        
        attempts += 1
    
    # Add sparse decorations
    for y in range(tilemap.height):
        for x in range(tilemap.width):
            if tilemap.get_tile(x, y) == Tile.NATURE:
                rand = random.random()
                if rand < flower_chance:
                    tilemap.set_tile(x, y, random.choice([
                        Tile.NATURE_FLOWER,
                        Tile.NATURE_FLOWER_RED
                    ]))
                elif rand < flower_chance + log_chance:
                    tilemap.set_tile(x, y, Tile.NATURE_LOG)
                elif rand < flower_chance + log_chance + rock_chance:
                    tilemap.set_tile(x, y, Tile.NATURE_ROCK)
                elif rand < flower_chance + log_chance + rock_chance + bush_chance:
                    tilemap.set_tile(x, y, Tile.NATURE_BUSH)

def simple_noise(x: float, y: float, seed: int = 12345) -> float:
    """Simple pseudo-random noise function"""
    n = int(x * 374761393 + y * 668265263 + seed)
    n = (n >> 13) ^ n
    n = n * (n * n * 15731 + 789221) + 1376312589
    return (1.0 - ((n & 0x7fffffff) / 1073741824.0)) * 0.5

def smooth_noise(x: float, y: float, seed: int = 12345) -> float:
    """Smooth noise by averaging nearby values"""
    corners = (simple_noise(x-1, y-1, seed) + simple_noise(x+1, y-1, seed) + 
              simple_noise(x-1, y+1, seed) + simple_noise(x+1, y+1, seed)) / 16
    sides = (simple_noise(x-1, y, seed) + simple_noise(x+1, y, seed) + 
            simple_noise(x, y-1, seed) + simple_noise(x, y+1, seed)) / 8
    center = simple_noise(x, y, seed) / 4
    return corners + sides + center