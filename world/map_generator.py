import pygame
import math
import random
from typing import List, Tuple, Dict, Optional
from .tilemap import (
    TileMap, Tile, line, generate_rectangular_city, place_buildings, 
    connect_points_with_roads, auto_tile_roads, auto_tile_cities, 
    add_nature_decorations, simple_noise, smooth_noise
)
import os

# Import the loader classes
from .tilemap_editor import TilemapLoader, MapGenerationMenu

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
    """Enhanced map generator with save/load integration"""
    
    def __init__(self, width: int, height: int, tile_size: int):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.grid_width = width // tile_size
        self.grid_height = height // tile_size
        
        # Use the new tilemap system
        self.tilemap = TileMap(self.grid_width, self.grid_height, Tile.NATURE)
        # Initialize city and path tile grids
        self.tilemap.city_tile_grid = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.tilemap.path_tile_grid = [["base-city-tile-path" for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
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
        
        # Track generation mode
        self.generation_mode = "random"
        self.loaded_from_map = None
    
    def set_pre_placed_buildings(self, building_positions: List[Tuple[int, int]]):
        """Set the positions of pre-placed buildings (in pixel coordinates)"""
        self.pre_placed_buildings = [
            (pos[0] // self.tile_size, pos[1] // self.tile_size) 
            for pos in building_positions
        ]
        self.building_positions = self.pre_placed_buildings.copy()
    
    def generate_map_interactive(self, choice=None, map_number=None) -> pygame.Surface:
        """Generate map with choice from start screen GUI"""
        if choice is None:
            choice = "random"
        
        print(f"Map generation choice: {choice}")
        
        if choice == "load" and map_number:
            print(f"Attempting to load map {map_number}")
            return self._load_and_generate_from_save(map_number)
        elif choice == "blank":
            print("Generating blank map")
            return self._generate_blank_map()
        else:  # choice == "random"
            print("Generating random map")
            return self._generate_random_map()
    
    def _load_and_generate_from_save(self, map_number: int) -> pygame.Surface:
        """Load and apply a saved map"""
        save_data = TilemapLoader.load_map_by_number(map_number)
        
        if not save_data:
            print(f"Failed to load Map #{map_number}. Generating random map instead.")
            return self._generate_random_map()
        
        # Clear and rebuild tilemap
        self.tilemap = TileMap(self.grid_width, self.grid_height, Tile.NATURE)
        
        # Initialize grids
        self.tilemap.city_tile_grid = [[None for _ in range(self.tilemap.width)] for _ in range(self.tilemap.height)]
        self.tilemap.path_tile_grid = [["base-city-tile-path" for _ in range(self.tilemap.width)] for _ in range(self.tilemap.height)]
        
        # Apply tilemap data
        tilemap_data = save_data.get('tilemap', [])
        for y, row in enumerate(tilemap_data):
            for x, tile_value in enumerate(row):
                if (0 <= x < self.tilemap.width and 0 <= y < self.tilemap.height):
                    # Convert int to Tile enum
                    try:
                        tile_enum = Tile(tile_value)
                        self.tilemap.set_tile(x, y, tile_enum)
                    except ValueError:
                        # Fallback for invalid tile values
                        self.tilemap.set_tile(x, y, Tile.NATURE)

        # Apply city tile data if available
        city_tile_data = save_data.get('city_tile_data', [])
        if city_tile_data:
            for y, row in enumerate(city_tile_data):
                for x, city_type in enumerate(row):
                    if (0 <= x < self.tilemap.width and 0 <= y < self.tilemap.height):
                        self.tilemap.city_tile_grid[y][x] = city_type

        # Apply path tile data if available  
        path_tile_data = save_data.get('path_tile_data', [])
        if path_tile_data:
            for y, row in enumerate(path_tile_data):
                for x, path_type in enumerate(row):
                    if (0 <= x < self.tilemap.width and 0 <= y < self.tilemap.height):
                        self.tilemap.path_tile_grid[y][x] = path_type
        
        # Apply building positions
        building_positions = save_data.get('building_positions', [])
        self.building_positions = [
            (pos['x'] // self.tile_size, pos['y'] // self.tile_size) 
            for pos in building_positions
        ]
        
        self.generation_mode = "loaded"
        self.loaded_from_map = map_number
        self._update_compatibility_properties()
        
        return self._create_tile_surface()
    
    def _generate_blank_map(self) -> pygame.Surface:
        """Generate a blank map filled with nature tiles"""
        # Clear the tilemap (already initialized with NATURE)
        for y in range(self.tilemap.height):
            for x in range(self.tilemap.width):
                self.tilemap.set_tile(x, y, Tile.NATURE)

        # In create_map_generator or wherever the tilemap is set up
        if not hasattr(self.tilemap, 'city_tile_grid'):
            self.tilemap.city_tile_grid = [[None for _ in range(self.tilemap.width)] for _ in range(self.tilemap.height)]
        
        # No buildings or cities
        self.building_positions = []
        self.buildings = []
        self.paths = []
        
        self.generation_mode = "blank"
        self.loaded_from_map = None
        
        # Add some basic nature decorations
        add_nature_decorations(self.tilemap)
        
        # Update compatibility properties
        self._update_compatibility_properties()
        
        print("Generated blank map ready for editing")
        return self._create_tile_surface()
    
    def _generate_random_map(self) -> pygame.Surface:
        """Generate a random map using the standard algorithm"""
        self.generation_mode = "random"
        self.loaded_from_map = None

        # In create_map_generator or wherever the tilemap is set up
        if not hasattr(self.tilemap, 'city_tile_grid'):
            self.tilemap.city_tile_grid = [[None for _ in range(self.tilemap.width)] for _ in range(self.tilemap.height)]
        
        return self.generate_map()
    
    def generate_map(self, num_additional_cities: int = 0, num_buildings_per_city: int = 0):
        """Generate the complete map using the enhanced tilemap system"""

        # In create_map_generator or wherever the tilemap is set up
        if not hasattr(self.tilemap, 'city_tile_grid'):
            self.tilemap.city_tile_grid = [[None for _ in range(self.tilemap.width)] for _ in range(self.tilemap.height)]

        if self.generation_mode == "loaded":
            # Don't regenerate if we loaded from save
            return self._create_tile_surface()
        
        # Step 1: Generate organic cities around buildings
        if self.building_positions:
            self._generate_building_cities_enhanced()
            
            # Step 2: Create connecting paths between buildings
            self._generate_building_connection_paths_enhanced()
        else:
            print("No buildings provided, generating random cities")
            self._generate_random_cities(3)
        
        # Step 3: Auto-tile cities and roads for proper rendering
        auto_tile_cities(self.tilemap)
        self._auto_tile_paths()
        
        # Step 4: Add nature decorations
        add_nature_decorations(self.tilemap)
        
        # Step 5: Create interaction zones
        if self.building_positions:
            self.create_interaction_zones(20)
        
        # Step 6: Update compatibility properties
        self._update_compatibility_properties()
        
        return self._create_tile_surface()
    
    def _generate_random_cities(self, num_cities: int):
        """Generate random cities when no buildings are provided"""
        for i in range(num_cities):
            # Random city center
            center_x = random.randint(30, self.grid_width - 30)
            center_y = random.randint(30, self.grid_height - 30)
            
            # Random city size
            city_width = random.randint(25, 40)
            city_height = random.randint(25, 40)
            
            start_x = center_x - city_width // 2
            start_y = center_y - city_height // 2
            
            generate_rectangular_city(self.tilemap, start_x, start_y, city_width, city_height)
            
            # Add this as a "building" position for compatibility
            self.building_positions.append((center_x, center_y))
        
        # Connect the random cities with roads
        if len(self.building_positions) > 1:
            connect_points_with_roads(self.tilemap, self.building_positions, self.path_width)
    
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
        """Create the final tile surface from the tilemap"""
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
        
        debug_info = {
            'generation_mode': self.generation_mode,
            'loaded_from_map': self.loaded_from_map,
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
        
        return debug_info
    
    def quick_save(self) -> str:
        """Quick save current map state and return filename"""
        import json
        import os
        from datetime import datetime
        
        # Create saves directory if it doesn't exist
        saves_dir = "saves"
        os.makedirs(saves_dir, exist_ok=True)
        
        # Find next available number
        next_number = self._get_next_map_number(saves_dir)
        filename = f"new_map_{next_number}.json"
        filepath = os.path.join(saves_dir, filename)
        
        # Extract tilemap data - this now includes any editor changes
        tilemap_data, tile_counts = self._extract_tilemap_data()
        
        city_tile_data = []
        path_tile_data = []

        for y in range(self.tilemap.height):
            city_row = []
            path_row = []
            for x in range(self.tilemap.width):
                # Get city tile type (can be None)
                city_type = self.tilemap.city_tile_grid[y][x] if hasattr(self.tilemap, 'city_tile_grid') else None
                city_row.append(city_type)
                
                # Get path tile type (default to base path if None)
                path_type = self.tilemap.path_tile_grid[y][x] if hasattr(self.tilemap, 'path_tile_grid') else "base-city-tile-path"
                path_row.append(path_type)
            
            city_tile_data.append(city_row)
            path_tile_data.append(path_row)
        
        # Create save data
        save_data = {
            "metadata": {
                "save_time": datetime.now().isoformat(),
                "version": "0.8.2",
                "map_number": next_number,
                "generation_mode": self.generation_mode,
                "loaded_from_map": self.loaded_from_map,
                "total_tiles": self.tilemap.width * self.tilemap.height,
                "tile_counts": tile_counts
            },
            "map_info": {
                "width": self.tilemap.width,
                "height": self.tilemap.height,
                "tile_size": self.tile_size,
                "map_pixel_width": self.width,
                "map_pixel_height": self.height
            },
            "building_positions": [
                {"x": pos[0] * self.tile_size, "y": pos[1] * self.tile_size} 
                for pos in self.building_positions
            ],
            "tilemap": tilemap_data,
            "city_tile_data": city_tile_data,  # NEW: Save city tile types
            "path_tile_data": path_tile_data,  # NEW: Save path tile types
            "tile_legend": self._get_tile_legend()
        }
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"Map quick-saved as: {filename}")
        return filename
    
    def _get_next_map_number(self, saves_dir: str) -> int:
        """Find the next available map number"""
        print(f"DEBUG: Getting next map number from {saves_dir}")
        
        if not os.path.exists(saves_dir):
            print(f"DEBUG: Directory doesn't exist, returning 1")
            return 1
        
        existing_numbers = []
        files = os.listdir(saves_dir)
        print(f"DEBUG: Found {len(files)} files in directory")
        
        for filename in files:
            print(f"DEBUG: Checking file: {filename}")
            if filename.startswith("new_map_") and filename.endswith(".json"):
                try:
                    number_str = filename[8:-5]  # Remove "new_map_" and ".json"
                    number = int(number_str)
                    existing_numbers.append(number)
                    print(f"DEBUG: Found existing map number: {number}")
                except ValueError:
                    print(f"DEBUG: Invalid filename format: {filename}")
                    continue
        
        next_number = max(existing_numbers, default=0) + 1
        print(f"DEBUG: Next number will be: {next_number}")
        return next_number
    
    def _extract_tilemap_data(self) -> Tuple[List[List[int]], Dict[str, int]]:
        """Extract tilemap data and count tiles"""
        tilemap_data = []
        tile_counts = {}
        
        # Updated tile names to match your current system
        tile_names = {
            0: "NATURE", 1: "CITY", 2: "ROAD", 3: "NATURE_FLOWER",
            4: "NATURE_FLOWER_RED", 5: "NATURE_LOG", 6: "NATURE_BUSH", 
            7: "NATURE_ROCK", 8: "BUILDING"
        }
        
        for y in range(self.tilemap.height):
            row = []
            for x in range(self.tilemap.width):
                tile = self.tilemap.get_tile(x, y)
                # Handle both enum and int values
                if hasattr(tile, 'value'):
                    tile_value = tile.value
                else:
                    tile_value = int(tile)
                row.append(tile_value)
                
                # Count tiles
                tile_name = tile_names.get(tile_value, f"Unknown_{tile_value}")
                tile_counts[tile_name] = tile_counts.get(tile_name, 0) + 1
            tilemap_data.append(row)
        
        return tilemap_data, tile_counts
    
    def _get_tile_legend(self) -> Dict[str, str]:
        """Get tile type legend for save data"""
        return {
            "0": "NATURE", "1": "CITY", "2": "ROAD", "3": "NATURE_FLOWER",
            "4": "NATURE_FLOWER_RED", "5": "NATURE_LOG", "6": "NATURE_BUSH", 
            "7": "NATURE_ROCK", "8": "BUILDING"
        }


# Compatibility function to create the enhanced map generator
def create_map_generator(width: int, height: int, tile_size: int) -> MapGenerator:
    """Factory function to create enhanced map generator with menu integration"""
    return MapGenerator(width, height, tile_size)


# Additional utility functions for advanced map generation
def generate_city_district(tilemap: TileMap, center_x: int, center_y: int, 
                          district_type: str = "residential") -> None:
    """Generate specialized city districts"""
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


# Usage example and testing functions
class MapGeneratorDemo:
    """Demo class showing how to use the enhanced map generator"""
    
    @staticmethod
    def demo_interactive_generation():
        """Demo the interactive map generation"""
        print("=== MAP GENERATOR DEMO ===")
        
        # Create map generator
        width, height = 3200, 3200
        tile_size = 32
        generator = MapGenerator(width, height, tile_size)
        
        # Set some example building positions (optional)
        building_positions = [
            (800, 800), (1600, 1200), (2400, 1800)
        ]
        generator.set_pre_placed_buildings(building_positions)
        
        # Generate map with interactive menu
        surface = generator.generate_map_interactive()
        
        # Print debug info
        debug_info = generator.get_debug_info()
        print("\n=== MAP GENERATION COMPLETE ===")
        print(f"Generation mode: {debug_info['generation_mode']}")
        if debug_info['loaded_from_map']:
            print(f"Loaded from: Map #{debug_info['loaded_from_map']}")
        print(f"Total tiles: {debug_info['total_tiles']}")
        print(f"City coverage: {debug_info['city_percentage']:.1f}%")
        print(f"Road coverage: {debug_info['road_percentage']:.1f}%")
        print(f"Buildings: {debug_info['num_buildings']}")
        
        return surface, generator
    
    @staticmethod
    def demo_quick_save_load():
        """Demo quick save and load functionality"""
        print("=== QUICK SAVE/LOAD DEMO ===")
        
        # Generate a random map
        generator = MapGenerator(1600, 1600, 32)
        generator.set_pre_placed_buildings([(400, 400), (800, 800)])
        surface = generator.generate_map()
        
        # Quick save
        saved_filename = generator.quick_save()
        
        # Create new generator and load the saved map
        new_generator = MapGenerator(1600, 1600, 32)
        map_number = int(saved_filename.split('_')[2].split('.')[0])
        loaded_surface = new_generator._load_and_generate_from_save(map_number)
        
        print(f"Successfully saved and reloaded {saved_filename}")
        return new_generator