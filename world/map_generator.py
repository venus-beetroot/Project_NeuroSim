"""
Enhanced MapGenerator that integrates the new tilemap system with existing functionality
Replaces the existing map_generator.py with improved city generation and cleaner code
"""
import pygame
import math
import random
from typing import List, Tuple, Dict, Optional
from .tilemap import (
    TileMap, Tile, line, generate_rectangular_city, place_buildings, connect_points_with_roads, auto_tile_roads, auto_tile_cities, add_nature_decorations, simple_noise, smooth_noise
)

# Keep compatibility with existing TileType class
class TileType:
    """Compatibility layer for existing code"""
    NATURE = 0
    CITY = 1
    ROAD = 2
    NATURE_FLOWER = 3
    NATURE_FLOWER_RED = 4
    NATURE_LOG = 5
    NATURE_BUSH = 6
    NATURE_ROCK = 7
    BUILDING = 8

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
    """Enhanced map generator using the new tilemap system"""
    
    def __init__(self, width: int, height: int, tile_size: int):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.grid_width = width // tile_size
        self.grid_height = height // tile_size
        
        # Use the new tilemap system
        self.tilemap = TileMap(self.grid_width, self.grid_height, Tile.NATURE)
        
        # Compatibility properties for existing code
        self.tile_grid = None  # Will be populated from tilemap
        self.city_tile_grid = None
        self.path_tile_grid = None
        
        self.buildings: List[pygame.Rect] = []
        self.interaction_zones: List[pygame.Rect] = []
        self.building_positions: List[Tuple[int, int]] = []
        self.paths: List[List[Tuple[int, int]]] = []
        
        # Store pre-placed building locations
        self.pre_placed_buildings: List[Tuple[int, int]] = []
        
        # Generation parameters
        self.city_radius = 25
        self.path_width = 3
        self.noise_seed = random.randint(0, 1000000)
    
    def set_pre_placed_buildings(self, building_positions: List[Tuple[int, int]]):
        """Set the positions of pre-placed buildings (in pixel coordinates)"""
        self.pre_placed_buildings = [
            (pos[0] // self.tile_size, pos[1] // self.tile_size) 
            for pos in building_positions
        ]
        self.building_positions = self.pre_placed_buildings.copy()
    
    def generate_map(self, num_additional_cities: int = 0, num_buildings_per_city: int = 0):
        """Generate the complete map using the enhanced tilemap system"""
        # Step 1: Generate organic cities around buildings
        self._generate_building_cities_enhanced()
        
        # Step 2: Create connecting paths between buildings
        self._generate_building_connection_paths_enhanced()
        
        # Step 3: Auto-tile cities and roads for proper rendering
        auto_tile_cities(self.tilemap)
        self._auto_tile_paths()
        
        # Step 4: Add nature decorations
        add_nature_decorations(self.tilemap)
        
        # Step 5: Create interaction zones
        self.create_interaction_zones(20)
        
        # Step 6: Update compatibility properties
        self._update_compatibility_properties()
        
        return self._create_tile_surface()
    
    def _generate_building_cities_enhanced(self):
        """Generate simple rectangular cities around buildings"""
        for building_x, building_y in self.building_positions:
            city_width = 30
            city_height = 30
            
            # Center rectangle around building
            start_x = building_x - city_width // 2
            start_y = building_y - city_height // 2
            
            # Use the simple clean rectangle function
            generate_rectangular_city(
                self.tilemap, start_x, start_y, city_width, city_height
            )
        
        print(f"Generated {len(self.building_positions)} rectangular cities")
    
    def _generate_building_connection_paths_enhanced(self):
        """Create paths connecting buildings using the enhanced system"""
        if len(self.building_positions) < 2:
            return
        
        # Connect all building positions with roads
        connect_points_with_roads(self.tilemap, self.building_positions, self.path_width)
        
        # Store paths for compatibility (convert back to old format)
        self._extract_paths_from_tilemap()
    
    def _auto_tile_paths(self):
        """Auto-tile paths using the enhanced system"""
        def pick_path_sprite(bitmask: int) -> str:
            """Convert bitmask to path sprite name"""
            # Bitmask: N=4, E=2, S=1, W=8
            if bitmask == 0:
                return PathTileType.BASE_PATH
            elif bitmask == 1:  # Only South
                return PathTileType.NORTH_SIDE
            elif bitmask == 2:  # Only East
                return PathTileType.WEST_SIDE
            elif bitmask == 4:  # Only North
                return PathTileType.SOUTH_SIDE
            elif bitmask == 8:  # Only West
                return PathTileType.EAST_SIDE
            elif bitmask == 5:  # North + South (vertical)
                return PathTileType.BASE_PATH
            elif bitmask == 10:  # East + West (horizontal)
                return PathTileType.BASE_PATH
            elif bitmask == 6:  # North + East
                return PathTileType.SOUTH_WEST_CORNER
            elif bitmask == 12:  # North + West
                return PathTileType.SOUTH_EAST_CORNER
            elif bitmask == 3:  # South + East
                return PathTileType.NORTH_WEST_CORNER
            elif bitmask == 9:  # South + West
                return PathTileType.NORTH_EAST_CORNER
            else:
                # T-junctions and crosses use base path
                return PathTileType.BASE_PATH
        
        auto_tile_roads(self.tilemap, pick_path_sprite)
    
    def _extract_paths_from_tilemap(self):
        """Extract path information for compatibility with existing code"""
        self.paths = []
        visited = set()
        
        # Find all road tiles and group them into paths
        for y in range(self.tilemap.height):
            for x in range(self.tilemap.width):
                if (self.tilemap.get_tile(x, y) == Tile.ROAD and 
                    (x, y) not in visited):
                    # Start a new path from this road tile
                    path = self._trace_path(x, y, visited)
                    if len(path) > 1:
                        self.paths.append(path)
    
    def _trace_path(self, start_x: int, start_y: int, visited: set) -> List[Tuple[int, int]]:
        """Trace a path from a starting road tile"""
        path = []
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack.pop()
            if (x, y) in visited:
                continue
            
            if self.tilemap.get_tile(x, y) == Tile.ROAD:
                visited.add((x, y))
                path.append((x, y))
                
                # Add adjacent road tiles to stack
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < self.tilemap.width and 
                        0 <= ny < self.tilemap.height and
                        (nx, ny) not in visited and
                        self.tilemap.get_tile(nx, ny) == Tile.ROAD):
                        stack.append((nx, ny))
        
        return path
    
    def _update_compatibility_properties(self):
        """Update compatibility properties for existing code"""
        # Convert tilemap to old grid format
        self.tile_grid = []
        for y in range(self.tilemap.height):
            row = []
            for x in range(self.tilemap.width):
                tile = self.tilemap.get_tile(x, y)
                row.append(tile.value)  # Convert enum to int
            self.tile_grid.append(row)
        
        # Copy city and path tile grids
        self.city_tile_grid = [row.copy() for row in self.tilemap.city_tile_grid]
        self.path_tile_grid = [row.copy() for row in self.tilemap.path_tile_grid]
    
    def _create_tile_surface(self) -> pygame.Surface:
        """Create the final tile surface from the tilemap - FIXED to return colored surface for texture application"""
        surface = pygame.Surface((self.width, self.height))
        
        for y in range(self.tilemap.height):
            for x in range(self.tilemap.width):
                tile = self.tilemap.get_tile(x, y)
                pixel_x = x * self.tile_size
                pixel_y = y * self.tile_size
                tile_rect = pygame.Rect(pixel_x, pixel_y, self.tile_size, self.tile_size)
                
                # Choose color based on tile type - these colors will be REPLACED by textures
                color = self._get_tile_color(tile, x, y)
                pygame.draw.rect(surface, color, tile_rect)
        
        return surface
    
    def _get_tile_color(self, tile: Tile, x: int, y: int) -> Tuple[int, int, int]:
        """Get color for tile type with validation"""
        if tile == Tile.NATURE:
            return self._validate_color((34, 139, 34))  # Forest green
        elif tile == Tile.NATURE_FLOWER:
            return self._validate_color((255, 182, 193))  # Light pink
        elif tile == Tile.NATURE_LOG:
            return self._validate_color((139, 69, 19))  # Brown
        elif tile == Tile.NATURE_ROCK:
            return self._validate_color((105, 105, 105))  # Dim gray
        elif tile == Tile.NATURE_FLOWER_RED:
            return self._validate_color((220, 20, 60))  # Crimson red
        elif tile == Tile.NATURE_BUSH:
            return self._validate_color((34, 100, 34))  # Dark green
        elif tile == Tile.CITY:
            # Use city tile type for shading
            city_tile_num = self.tilemap.get_city_tile_type(x, y)
            city_tile_num = max(0, min(13, city_tile_num))
            base_gray = 120 + (city_tile_num * 8)
            return self._validate_color((base_gray, base_gray, base_gray))
        elif tile == Tile.ROAD:
            return self._validate_color((205, 170, 125))  # Sandy brown for paths
        elif tile == Tile.BUILDING:
            return self._validate_color((80, 80, 80))  # Dark gray for buildings
        else:
            return self._validate_color((34, 139, 34))  # Default to nature
    
    def _validate_color(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Ensure color values are valid for pygame (0-255 range)"""
        r, g, b = color
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        return (r, g, b)
    
    def create_interaction_zones(self, padding: int):
        """Create interaction zones around each building"""
        for building_x, building_y in self.building_positions:
            # Convert tile coordinates back to pixel coordinates
            pixel_x = building_x * self.tile_size
            pixel_y = building_y * self.tile_size
            
            # Assume building size (adjust based on your building sizes)
            building_size = 3 * self.tile_size  # 3x3 tiles
            
            zone_x = pixel_x - padding
            zone_y = pixel_y - padding
            zone_width = building_size + (padding * 2)
            zone_height = building_size + (padding * 2)
            
            interaction_zone = pygame.Rect(zone_x, zone_y, zone_width, zone_height)
            self.interaction_zones.append(interaction_zone)
    
    def get_path_tile_type(self, x: int, y: int) -> str:
        """Get the path tile type for rendering at specific coordinates"""
        tile_x = x // self.tile_size
        tile_y = y // self.tile_size
        
        if (0 <= tile_x < self.tilemap.width and 0 <= tile_y < self.tilemap.height):
            if self.tilemap.get_tile(tile_x, tile_y) == Tile.ROAD:
                return self.tilemap.get_path_tile_type(tile_x, tile_y)
        
        return ""
    
    def get_debug_info(self) -> Dict:
        """Get debug information about the generated map"""
        city_tiles = sum(1 for y in range(self.tilemap.height) 
                        for x in range(self.tilemap.width) 
                        if self.tilemap.get_tile(x, y) == Tile.CITY)
        
        road_tiles = sum(1 for y in range(self.tilemap.height) 
                        for x in range(self.tilemap.width) 
                        if self.tilemap.get_tile(x, y) == Tile.ROAD)
        
        nature_tiles = sum(1 for y in range(self.tilemap.height) 
                          for x in range(self.tilemap.width) 
                          if self.tilemap.get_tile(x, y) == Tile.NATURE)
        
        total_tiles = self.tilemap.width * self.tilemap.height
        
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

# Compatibility function to create the enhanced map generator
def create_map_generator(width: int, height: int, tile_size: int) -> MapGenerator:
    """Factory function to create enhanced map generator"""
    return MapGenerator(width, height, tile_size)

# Additional utility functions for advanced map generation
def generate_city_district(tilemap: TileMap, center_x: int, center_y: int, 
                          district_type: str = "residential") -> None:
    """Generate specialized city districts - FIXED"""
    if district_type == "residential":
        # More organic, smaller buildings
        width, height = 30, 25
        start_x = center_x - width // 2
        start_y = center_y - height // 2
        generate_rectangular_city(tilemap, start_x, start_y, width, height, margin=6)
        
    elif district_type == "commercial":
        # Denser, more rectangular
        width, height = 40, 35
        start_x = center_x - width // 2
        start_y = center_y - height // 2
        generate_rectangular_city(tilemap, start_x, start_y, width, height, margin=4)
        
    elif district_type == "industrial":
        # Large, blocky areas
        width, height = 50, 45
        start_x = center_x - width // 2
        start_y = center_y - height // 2
        generate_rectangular_city(tilemap, start_x, start_y, width, height, margin=2)

def add_specialty_roads(tilemap: TileMap, road_type: str = "highway") -> None:
    """Add specialty road types"""
    if road_type == "highway":
        # Add a main highway across the map
        mid_y = tilemap.height // 2
        for x in range(tilemap.width):
            for dy in range(-2, 3):  # 5-tile wide highway
                y = mid_y + dy
                if 0 <= y < tilemap.height:
                    if tilemap.get_tile(x, y) != Tile.BUILDING:
                        tilemap.set_tile(x, y, Tile.ROAD)

def add_natural_features(tilemap: TileMap) -> None:
    """Add natural features like rivers, hills, etc."""
    # Add a meandering river
    river_start_x = random.randint(0, tilemap.width // 4)
    river_start_y = random.randint(tilemap.height // 4, 3 * tilemap.height // 4)
    
    x, y = river_start_x, river_start_y
    direction = random.uniform(0, math.pi / 4)  # Generally eastward
    
    while x < tilemap.width and 0 <= y < tilemap.height:
        # Create river tiles (could be a new tile type)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                rx, ry = x + dx, y + dy
                if 0 <= rx < tilemap.width and 0 <= ry < tilemap.height:
                    if tilemap.get_tile(rx, ry) not in [Tile.BUILDING, Tile.CITY]:
                        tilemap.set_tile(rx, ry, Tile.NATURE)  # For now, use nature
        
        # Update river direction with some randomness
        direction += random.uniform(-0.2, 0.2)
        direction = max(-math.pi/3, min(math.pi/3, direction))  # Keep generally eastward
        
        # Move to next position
        x += int(3 * math.cos(direction))
        y += int(3 * math.sin(direction))

def optimize_road_network(tilemap: TileMap) -> None:
    """Optimize road network by removing redundant roads and improving connections"""
    # Remove isolated road tiles
    to_remove = []
    for y in range(tilemap.height):
        for x in range(tilemap.width):
            if tilemap.get_tile(x, y) == Tile.ROAD:
                # Count adjacent road tiles
                adjacent_roads = 0
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < tilemap.width and 0 <= ny < tilemap.height and
                        tilemap.get_tile(nx, ny) == Tile.ROAD):
                        adjacent_roads += 1
                
                # Remove isolated roads
                if adjacent_roads == 0:
                    to_remove.append((x, y))
    
    for x, y in to_remove:
        tilemap.set_tile(x, y, Tile.NATURE)