import pygame
import math
import os
from typing import List, Tuple, Dict, Optional, Set
import random

class TileType:
    """Define different tile types for the map"""
    NATURE = 0      # floor_0.png (nature)
    CITY = 1        # floor_1.png to floor_7.png (various city tiles)
    ROAD = 2        # Path tiles with proper borders
    NATURE_FLOWER = 3  # flower_0.png (nature with flowers)
    NATURE_FLOWER_RED = 4
    NATURE_LOG = 5
    NATURE_BUSH = 6
    NATURE_ROCK = 7

class PathTileType:
    """Define specific path tile types for proper rendering"""
    BASE_PATH = "base-city-tile-path"
    WEST_SIDE = "city-tile-path-west-side"
    EAST_SIDE = "city-tile-path-east-side"
    SOUTH_SIDE = "city-tile-path-south-side"
    NORTH_SIDE = "city-tile-path-north-side"
    NORTH_WEST_CORNER = "city-tile-path-north-west-corner"
    NORTH_EAST_CORNER = "city-tile-path-north-east-corner"
    SOUTH_WEST_CORNER = "city-tile-path-south-west-corner"
    SOUTH_EAST_CORNER = "city-tile-path-south-east-corner"

class MapGenerator:
    """Generates a map with building-centered cities and connecting paths"""
    
    def __init__(self, width: int, height: int, tile_size: int):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.grid_width = width // tile_size
        self.grid_height = height // tile_size
        
        # Initialize tile grid - everything starts as nature (0)
        self.tile_grid = [[TileType.NATURE for _ in range(self.grid_width)] 
                         for _ in range(self.grid_height)]
        
        # Initialize city tile grid to track which city tiles to use
        self.city_tile_grid = [[0 for _ in range(self.grid_width)] 
                              for _ in range(self.grid_height)]
        
        # Initialize path tile grid for proper path rendering
        self.path_tile_grid = [["" for _ in range(self.grid_width)] 
                              for _ in range(self.grid_height)]
        
        self.buildings: List[pygame.Rect] = []
        self.interaction_zones: List[pygame.Rect] = []
        self.building_positions: List[Tuple[int, int]] = []  # Store building centers in tile coords
        self.paths: List[List[Tuple[int, int]]] = []
        
        # Store pre-placed building locations (will be set externally)
        self.pre_placed_buildings: List[Tuple[int, int]] = []
        
        # Generation parameters
        self.city_radius = 25  # Radius around buildings for city generation
        self.path_width = 3  # Width of connecting paths
        
        # Initialize simple noise for organic shapes
        self.noise_seed = random.randint(0, 1000000)
    
    def set_pre_placed_buildings(self, building_positions: List[Tuple[int, int]]):
        """Set the positions of pre-placed buildings (in pixel coordinates)"""
        # Convert pixel coordinates to tile coordinates and store
        self.pre_placed_buildings = [
            (pos[0] // self.tile_size, pos[1] // self.tile_size) 
            for pos in building_positions
        ]
        self.building_positions = self.pre_placed_buildings.copy()
    
    def _simple_noise(self, x: float, y: float) -> float:
        """Simple pseudo-random noise function"""
        n = int(x * 374761393 + y * 668265263 + self.noise_seed)
        n = (n >> 13) ^ n
        n = n * (n * n * 15731 + 789221) + 1376312589
        return (1.0 - ((n & 0x7fffffff) / 1073741824.0)) * 0.5
    
    def _smooth_noise(self, x: float, y: float) -> float:
        """Smooth noise by averaging nearby values"""
        corners = (self._simple_noise(x-1, y-1) + self._simple_noise(x+1, y-1) + 
                  self._simple_noise(x-1, y+1) + self._simple_noise(x+1, y+1)) / 16
        sides = (self._simple_noise(x-1, y) + self._simple_noise(x+1, y) + 
                self._simple_noise(x, y-1) + self._simple_noise(x, y+1)) / 8
        center = self._simple_noise(x, y) / 4
        return corners + sides + center
    
    def _validate_color(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Ensure color values are valid for pygame (0-255 range)"""
        r, g, b = color
        # Clamp each value to 0-255 range and ensure they're integers
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        return (r, g, b)
        
    def generate_map(self, num_additional_cities: int = 0, num_buildings_per_city: int = 0):
        """Generate the complete map focused on building-centered cities with paths"""
        # Step 1: Generate city areas around all buildings
        self._generate_building_cities()
        
        # Step 2: Create connecting paths between all buildings
        self._generate_building_connection_paths()
        
        # Step 3: Determine proper path tile types for rendering
        self._determine_path_tile_types()
        
        # Step 4: Create interaction zones around buildings
        self.create_interaction_zones(20)
        
        # Step 5: Add nature decorations to remaining nature areas
        self._add_nature_decorations()
        
        return self._create_tile_surface()
    
    def _generate_building_cities(self):
        """Generate organic city areas around each building with proper edge/corner placement"""
        for building_x, building_y in self.building_positions:
            # Create organic city shape around each building
            for y in range(max(0, building_y - self.city_radius), 
                        min(self.grid_height, building_y + self.city_radius + 1)):
                for x in range(max(0, building_x - self.city_radius), 
                            min(self.grid_width, building_x + self.city_radius + 1)):
                    
                    # Calculate distance from building center
                    distance = math.sqrt((x - building_x)**2 + (y - building_y)**2)
                    
                    # Use noise to create organic city borders
                    noise_value = self._smooth_noise(x * 0.1, y * 0.1)
                    
                    # Adjust radius based on noise for organic shape
                    effective_radius = self.city_radius + (noise_value * 8)
                    
                    # Create gradient - closer to building = higher chance of city
                    if distance <= effective_radius:
                        city_probability = 1.0 - (distance / effective_radius)
                        city_probability += noise_value * 0.2
                        
                        # Higher threshold closer to building center
                        threshold = 0.3 - (distance / effective_radius) * 0.2
                        
                        if city_probability > threshold:
                            self.tile_grid[y][x] = TileType.CITY
                            # Don't assign random city tile here - we'll determine it later
                            self.city_tile_grid[y][x] = 0  # Placeholder

        # After generating city areas, determine proper tile types
        self._determine_city_tile_types()

    def _determine_city_tile_types(self):
        """Determine the appropriate city tile type for each city tile based on position"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.tile_grid[y][x] == TileType.CITY:
                    # Check surrounding tiles to determine city tile type
                    neighbors = self._get_city_neighbors(x, y)
                    self.city_tile_grid[y][x] = self._get_city_tile_type(neighbors)

    def _get_city_neighbors(self, x: int, y: int) -> Dict[str, bool]:
        """Get the city neighbors for a tile"""
        neighbors = {}
        directions = {
            'north': (0, -1),
            'south': (0, 1),
            'east': (1, 0),
            'west': (-1, 0),
            'north_east': (1, -1),
            'north_west': (-1, -1),
            'south_east': (1, 1),
            'south_west': (-1, 1)
        }
        
        for direction, (dx, dy) in directions.items():
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                neighbors[direction] = self.tile_grid[ny][nx] == TileType.CITY
            else:
                neighbors[direction] = False
        
        return neighbors

    def _get_city_tile_type(self, neighbors: Dict[str, bool]) -> int:
        """Determine the appropriate city tile based on neighbors - returns tile index"""
        north = neighbors['north']
        south = neighbors['south']
        east = neighbors['east']
        west = neighbors['west']
        north_east = neighbors['north_east']
        north_west = neighbors['north_west']
        south_east = neighbors['south_east']
        south_west = neighbors['south_west']
        
        # Count orthogonal connections
        orthogonal_connections = sum([north, south, east, west])
        
        # Define tile type constants
        INTERIOR = 0
        TOP_LEFT_CORNER = 1
        TOP_RIGHT_CORNER = 2
        BOTTOM_LEFT_CORNER = 3
        BOTTOM_RIGHT_CORNER = 4
        TOP_EDGE = 5
        BOTTOM_EDGE = 6
        LEFT_EDGE = 7
        RIGHT_EDGE = 8
        INNER_TOP_CORNER = 9
        INNER_BOTTOM_CORNER = 10
        INNER_LEFT_CORNER = 11
        INNER_RIGHT_CORNER = 12
        ISOLATED = 13
        
        # Interior tile (surrounded by city on all sides)
        if north and south and east and west:
            return INTERIOR
        
        # Corner pieces (only two adjacent sides are city)
        if not north and not west and south and east:
            return TOP_LEFT_CORNER
        if not north and not east and south and west:
            return TOP_RIGHT_CORNER
        if not south and not west and north and east:
            return BOTTOM_LEFT_CORNER
        if not south and not east and north and west:
            return BOTTOM_RIGHT_CORNER
        
        # Edge pieces (one side is not city)
        if not north and south and east and west:
            return TOP_EDGE
        if not south and north and east and west:
            return BOTTOM_EDGE
        if not east and north and south and west:
            return RIGHT_EDGE
        if not west and north and south and east:
            return LEFT_EDGE
        
        # Inner corners (three sides are city, but diagonal is missing)
        if north and south and east and west:
            if not north_east and not north_west:
                return INNER_TOP_CORNER
            elif not south_east and not south_west:
                return INNER_BOTTOM_CORNER
            elif not north_west and not south_west:
                return INNER_LEFT_CORNER
            elif not north_east and not south_east:
                return INNER_RIGHT_CORNER
        
        # Isolated or barely connected tiles
        if orthogonal_connections <= 1:
            return ISOLATED
        
        # Default fallback
        return INTERIOR

    def _generate_building_connection_paths(self):
        """Create paths connecting all buildings using minimum spanning tree"""
        if len(self.building_positions) < 2:
            return
        
        # Use minimum spanning tree to connect all buildings efficiently
        connected_buildings = set([0])  # Start with first building
        unconnected_buildings = set(range(1, len(self.building_positions)))
        
        while unconnected_buildings:
            # Find closest unconnected building to any connected building
            min_distance = float('inf')
            best_connection = None
            
            for connected_idx in connected_buildings:
                for unconnected_idx in unconnected_buildings:
                    distance = self._calculate_distance(
                        self.building_positions[connected_idx],
                        self.building_positions[unconnected_idx]
                    )
                    if distance < min_distance:
                        min_distance = distance
                        best_connection = (connected_idx, unconnected_idx)
            
            if best_connection:
                # Create path between buildings
                path = self._create_building_path(
                    self.building_positions[best_connection[0]],
                    self.building_positions[best_connection[1]]
                )
                self.paths.append(path)
                
                # Add newly connected building to connected set
                connected_buildings.add(best_connection[1])
                unconnected_buildings.remove(best_connection[1])
        
        # Optionally add some additional connections for redundancy
        if len(self.building_positions) > 2:
            # Add one extra connection between distant buildings
            max_distance = 0
            best_extra_connection = None
            
            for i in range(len(self.building_positions)):
                for j in range(i + 1, len(self.building_positions)):
                    distance = self._calculate_distance(
                        self.building_positions[i],
                        self.building_positions[j]
                    )
                    if distance > max_distance:
                        max_distance = distance
                        best_extra_connection = (i, j)
            
            if best_extra_connection and random.random() < 0.6:  # 60% chance
                extra_path = self._create_building_path(
                    self.building_positions[best_extra_connection[0]],
                    self.building_positions[best_extra_connection[1]]
                )
                self.paths.append(extra_path)
    
    def _create_building_path(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Create a path between two buildings with some curves"""
        path = []
        start_x, start_y = start
        end_x, end_y = end
        
        # Create path with 1-2 waypoints for more natural curves
        waypoints = [start]
        
        # Add waypoints for curved paths
        distance = self._calculate_distance(start, end)
        if distance > 30:  # Only add waypoints for longer paths
            num_waypoints = random.randint(1, 2)
            for i in range(num_waypoints):
                progress = (i + 1) / (num_waypoints + 1)
                
                # Linear interpolation between start and end
                base_x = int(start_x + (end_x - start_x) * progress)
                base_y = int(start_y + (end_y - start_y) * progress)
                
                # Add perpendicular offset for curves
                perpendicular_offset = random.randint(-8, 8)
                direction_x = end_y - start_y
                direction_y = start_x - end_x
                length = math.sqrt(direction_x**2 + direction_y**2)
                
                if length > 0:
                    direction_x /= length
                    direction_y /= length
                    
                    curve_x = int(base_x + direction_x * perpendicular_offset)
                    curve_y = int(base_y + direction_y * perpendicular_offset)
                    
                    # Ensure waypoint is within bounds
                    curve_x = max(5, min(self.grid_width - 5, curve_x))
                    curve_y = max(5, min(self.grid_height - 5, curve_y))
                    
                    waypoints.append((curve_x, curve_y))
                else:
                    waypoints.append((base_x, base_y))
        
        waypoints.append(end)
        
        # Connect all waypoints with straight lines
        for i in range(len(waypoints) - 1):
            segment_path = self._line_path(waypoints[i], waypoints[i + 1])
            path.extend(segment_path)
        
        # Apply path tiles
        for x, y in path:
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                # Create path with specified width
                for dy in range(-self.path_width//2, self.path_width//2 + 1):
                    for dx in range(-self.path_width//2, self.path_width//2 + 1):
                        path_x, path_y = x + dx, y + dy
                        if (0 <= path_x < self.grid_width and 
                            0 <= path_y < self.grid_height):
                            self.tile_grid[path_y][path_x] = TileType.ROAD
        
        return path
    
    def _determine_path_tile_types(self):
        """Determine the appropriate path tile type for each path tile"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.tile_grid[y][x] == TileType.ROAD:
                    # Check surrounding tiles to determine path type
                    neighbors = self._get_path_neighbors(x, y)
                    self.path_tile_grid[y][x] = self._get_path_tile_type(neighbors)
    
    def _get_path_neighbors(self, x: int, y: int) -> Dict[str, bool]:
        """Get the path neighbors for a tile"""
        neighbors = {}
        directions = {
            'north': (0, -1),
            'south': (0, 1),
            'east': (1, 0),
            'west': (-1, 0)
        }
        
        for direction, (dx, dy) in directions.items():
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                neighbors[direction] = self.tile_grid[ny][nx] == TileType.ROAD
            else:
                neighbors[direction] = False
        
        return neighbors
    
    def _get_path_tile_type(self, neighbors: Dict[str, bool]) -> str:
        """Determine the appropriate path tile based on neighbors"""
        north = neighbors['north']
        south = neighbors['south']
        east = neighbors['east']
        west = neighbors['west']
        
        # Count connections
        connections = sum([north, south, east, west])
        
        if connections == 0:
            return PathTileType.BASE_PATH
        elif connections == 1:
            # Dead end - use appropriate side tile
            if north: return PathTileType.SOUTH_SIDE
            if south: return PathTileType.NORTH_SIDE
            if east: return PathTileType.WEST_SIDE
            if west: return PathTileType.EAST_SIDE
        elif connections == 2:
            # Straight path or corner
            if north and south: return PathTileType.BASE_PATH  # Vertical
            if east and west: return PathTileType.BASE_PATH    # Horizontal
            
            # Corners
            if north and east: return PathTileType.SOUTH_WEST_CORNER
            if north and west: return PathTileType.SOUTH_EAST_CORNER
            if south and east: return PathTileType.NORTH_WEST_CORNER
            if south and west: return PathTileType.NORTH_EAST_CORNER
        elif connections >= 3:
            # T-junction or cross - use base path
            return PathTileType.BASE_PATH
        
        return PathTileType.BASE_PATH
    
    def _line_path(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Create a straight line path between two points using Bresenham's algorithm"""
        x0, y0 = start
        x1, y1 = end
        
        path = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        
        while True:
            path.append((x, y))
            
            if x == x1 and y == y1:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return path
    
    def _calculate_distance(self, point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def _add_nature_decorations(self):
        """Add flowers, logs, rocks, and bushes to nature areas"""
        self._add_flower_tiles_to_nature()
        self._add_log_tiles_to_nature()
        self._add_rock_tiles_to_nature()
        self._add_bush_tiles_to_nature()
    
    def _add_flower_tiles_to_nature(self, flower_chance: float = 0.03, num_clusters: int = 8):
        """Place flower clusters in nature areas"""
        clusters_placed = 0
        attempts = 0
        max_attempts = num_clusters * 10
        
        while clusters_placed < num_clusters and attempts < max_attempts:
            y = random.randint(2, self.grid_height - 3)
            x = random.randint(2, self.grid_width - 3)
            
            if self.tile_grid[y][x] != TileType.NATURE:
                attempts += 1
                continue
            
            cluster_tiles = []
            cluster_size = random.randint(3, 6)
            offsets = [(0, 0), (1, 0), (0, 1), (1, 1), (0, -1), (-1, 0), (-1, -1)]
            random.shuffle(offsets)
            
            for dx, dy in offsets:
                tx, ty = x + dx, y + dy
                if (0 <= tx < self.grid_width and 0 <= ty < self.grid_height and
                    self.tile_grid[ty][tx] == TileType.NATURE):
                    cluster_tiles.append((tx, ty))
                    if len(cluster_tiles) >= cluster_size:
                        break
            
            if len(cluster_tiles) >= cluster_size:
                for tx, ty in cluster_tiles:
                    self.tile_grid[ty][tx] = random.choice([
                        TileType.NATURE_FLOWER,
                        TileType.NATURE_FLOWER_RED
                    ])
                clusters_placed += 1
            
            attempts += 1
        
        # Add sparse single flowers
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.tile_grid[y][x] == TileType.NATURE:
                    if random.random() < flower_chance:
                        self.tile_grid[y][x] = random.choice([
                            TileType.NATURE_FLOWER,
                            TileType.NATURE_FLOWER_RED
                        ])
    
    def _add_log_tiles_to_nature(self, log_chance: float = 0.003):
        """Add log tiles sparsely to nature areas"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.tile_grid[y][x] == TileType.NATURE:
                    if random.random() < log_chance:
                        self.tile_grid[y][x] = TileType.NATURE_LOG
    
    def _add_rock_tiles_to_nature(self, rock_chance: float = 0.003):
        """Add rock tiles sparsely to nature areas"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.tile_grid[y][x] == TileType.NATURE:
                    if random.random() < rock_chance:
                        self.tile_grid[y][x] = TileType.NATURE_ROCK
    
    def _add_bush_tiles_to_nature(self, bush_chance: float = 0.002):
        """Add bush tiles to nature areas"""
        for y in range(self.grid_height - 1):
            for x in range(self.grid_width - 1):
                if self.tile_grid[y][x] != TileType.NATURE:
                    continue
                
                if random.random() < bush_chance:
                    # Try 2x2 cluster first
                    if (self.tile_grid[y][x] == TileType.NATURE and
                        self.tile_grid[y+1][x] == TileType.NATURE and
                        self.tile_grid[y][x+1] == TileType.NATURE and
                        self.tile_grid[y+1][x+1] == TileType.NATURE):
                        
                        if random.random() < 0.7:
                            # 2x2 cluster
                            self.tile_grid[y][x] = TileType.NATURE_BUSH
                            self.tile_grid[y+1][x] = TileType.NATURE_BUSH
                            self.tile_grid[y][x+1] = TileType.NATURE_BUSH
                            self.tile_grid[y+1][x+1] = TileType.NATURE_BUSH
                        else:
                            # Single bush
                            self.tile_grid[y][x] = TileType.NATURE_BUSH
                    else:
                        # Single bush
                        self.tile_grid[y][x] = TileType.NATURE_BUSH
    
    def _create_tile_surface(self) -> pygame.Surface:
        """Create the final tile surface based on the tile grid - FIXED COLOR VALIDATION"""
        surface = pygame.Surface((self.width, self.height))
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                tile_type = self.tile_grid[y][x]
                pixel_x = x * self.tile_size
                pixel_y = y * self.tile_size
                tile_rect = pygame.Rect(pixel_x, pixel_y, self.tile_size, self.tile_size)
                
                # Choose color based on tile type with validation
                if tile_type == TileType.NATURE:
                    color = self._validate_color((34, 139, 34))  # Forest green
                elif tile_type == TileType.NATURE_FLOWER:
                    color = self._validate_color((255, 182, 193))  # Light pink
                elif tile_type == TileType.NATURE_LOG:
                    color = self._validate_color((139, 69, 19))  # Brown
                elif tile_type == TileType.NATURE_ROCK:
                    color = self._validate_color((105, 105, 105))  # Dim gray
                elif tile_type == TileType.NATURE_FLOWER_RED:
                    color = self._validate_color((220, 20, 60))  # Crimson red
                elif tile_type == TileType.NATURE_BUSH:
                    color = self._validate_color((34, 100, 34))  # Dark green
                elif tile_type == TileType.CITY:
                    # Different shades for city tiles - with proper validation
                    city_tile_num = self.city_tile_grid[y][x]
                    # Ensure city_tile_num is within reasonable bounds
                    city_tile_num = max(0, min(13, city_tile_num))  # Clamp to 0-13 range
                    base_gray = 120 + (city_tile_num * 10)  # Reduced multiplier to prevent overflow
                    # Validate the color before using it
                    color = self._validate_color((base_gray, base_gray, base_gray))
                elif tile_type == TileType.ROAD:
                    # Path tiles - light brown/tan color
                    color = self._validate_color((205, 170, 125))  # Sandy brown for paths
                else:
                    color = self._validate_color((34, 139, 34))  # Default to nature
                
                pygame.draw.rect(surface, color, tile_rect)
        
        return surface
    
    def get_path_tile_type(self, x: int, y: int) -> str:
        """Get the path tile type for rendering at specific coordinates"""
        tile_x = x // self.tile_size
        tile_y = y // self.tile_size
        
        if (0 <= tile_x < self.grid_width and 0 <= tile_y < self.grid_height):
            if self.tile_grid[tile_y][tile_x] == TileType.ROAD:
                return self.path_tile_grid[tile_y][tile_x]
        
        return ""
    
    def create_interaction_zones(self, padding: int):
        """Create interaction zones around each building"""
        for building_x, building_y in self.building_positions:
            # Convert tile coordinates back to pixel coordinates
            pixel_x = building_x * self.tile_size
            pixel_y = building_y * self.tile_size
            
            # Assume building size (you may need to adjust this based on your building sizes)
            building_size = 3 * self.tile_size  # 3x3 tiles
            
            zone_x = pixel_x - padding
            zone_y = pixel_y - padding
            zone_width = building_size + (padding * 2)
            zone_height = building_size + (padding * 2)
            
            interaction_zone = pygame.Rect(zone_x, zone_y, zone_width, zone_height)
            self.interaction_zones.append(interaction_zone)
    
    def get_debug_info(self) -> Dict:
        """Get debug information about the generated map"""
        city_tiles = sum(row.count(TileType.CITY) for row in self.tile_grid)
        road_tiles = sum(row.count(TileType.ROAD) for row in self.tile_grid)
        nature_tiles = sum(row.count(TileType.NATURE) for row in self.tile_grid)
        total_tiles = self.grid_width * self.grid_height
        
        return {
            'total_tiles': total_tiles,
            'city_tiles': city_tiles,
            'road_tiles': road_tiles,
            'nature_tiles': nature_tiles,
            'city_percentage': (city_tiles / total_tiles) * 100,
            'road_percentage': (road_tiles / total_tiles) * 100,
            'nature_percentage': (nature_tiles / total_tiles) * 100,
            'num_buildings': len(self.building_positions),
            'num_paths': len(self.paths),
            'building_positions': self.building_positions
        }