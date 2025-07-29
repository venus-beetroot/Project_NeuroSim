import pygame
import math
import os
from typing import List, Tuple, Dict, Optional, Set
import random

class TileType:
    """Define different tile types for the map"""
    NATURE = 0      # floor_0.png (nature)
    CITY = 1        # floor_1.png to floor_7.png (various city tiles)
    ROAD = 2        # floor_1.png to floor_7.png (roads, same as city)
    NATURE_FLOWER = 3  # flower_0.png (nature with flowers)

class MapGenerator:
    """Generates a map with organic cities, roads, and natural areas"""
    
    def __init__(self, width: int, height: int, tile_size: int):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.grid_width = width // tile_size
        self.grid_height = height // tile_size
        
        # Initialize tile grid - everything starts as nature (0)
        self.tile_grid = [[0 for _ in range(self.grid_width)] 
                         for _ in range(self.grid_height)]
        
        # Initialize city tile grid to track which city tiles to use
        self.city_tile_grid = [[0 for _ in range(self.grid_width)] 
                              for _ in range(self.grid_height)]
        
        self.buildings: List[pygame.Rect] = []
        self.interaction_zones: List[pygame.Rect] = []
        self.city_centers: List[Tuple[int, int]] = []
        self.roads: List[List[Tuple[int, int]]] = []
        
        # Store pre-placed building locations (will be set externally)
        self.pre_placed_buildings: List[Tuple[int, int]] = []
        
        # Generation parameters
        self.noise_scale = 0.05  # Controls city shape irregularity
        self.city_threshold = 0.3  # Higher = smaller cities
        self.road_width = 2  # Width of roads in tiles
        
        # Initialize simple noise for organic shapes
        self.noise_seed = random.randint(0, 1000000)
    
    def set_pre_placed_buildings(self, building_positions: List[Tuple[int, int]]):
        """Set the positions of pre-placed buildings (in pixel coordinates)"""
        # Convert pixel coordinates to tile coordinates
        self.pre_placed_buildings = [
            (pos[0] // self.tile_size, pos[1] // self.tile_size) 
            for pos in building_positions
        ]
    
    def _simple_noise(self, x: float, y: float) -> float:
        """Simple pseudo-random noise function to replace Perlin noise"""
        # Create pseudo-random values based on coordinates
        n = int(x * 374761393 + y * 668265263 + self.noise_seed)
        n = (n >> 13) ^ n
        n = n * (n * n * 15731 + 789221) + 1376312589
        
        # Normalize to -1 to 1 range
        return (1.0 - ((n & 0x7fffffff) / 1073741824.0)) * 0.5
    
    def _smooth_noise(self, x: float, y: float) -> float:
        """Smooth noise by averaging nearby values"""
        corners = (self._simple_noise(x-1, y-1) + self._simple_noise(x+1, y-1) + 
                  self._simple_noise(x-1, y+1) + self._simple_noise(x+1, y+1)) / 16
        sides = (self._simple_noise(x-1, y) + self._simple_noise(x+1, y) + 
                self._simple_noise(x, y-1) + self._simple_noise(x, y+1)) / 8
        center = self._simple_noise(x, y) / 4
        
        return corners + sides + center
        
    def generate_map(self, num_additional_cities: int = 2, num_buildings_per_city: int = 5):
        """Generate the complete map with cities around buildings, roads, and nature"""
        # Step 1: Generate city centers around pre-placed buildings and add additional cities
        self._generate_building_centered_cities(num_additional_cities)
        
        # Step 2: Create organic city shapes using noise
        self._generate_organic_cities()
        
        # Step 3: Connect cities with roads and add nature branches
        self._generate_enhanced_road_network()
        
        # Step 4: Place additional buildings within generated cities (not around pre-placed ones)
        self._place_buildings_in_generated_cities(num_buildings_per_city)
        
        # Step 5: Create interaction zones around buildings
        self.create_interaction_zones(20)
        
        # Step 6: Add flower tiles to nature
        self._add_flower_tiles_to_nature()
        
        return self._create_tile_surface()
    
    def _generate_building_centered_cities(self, num_additional_cities: int):
        """Generate cities centered around pre-placed buildings, plus additional cities"""
        
        # First, create cities around pre-placed buildings
        for building_x, building_y in self.pre_placed_buildings:
            # Add some randomness to the city center so it's not exactly on the building
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            city_x = building_x + offset_x
            city_y = building_y + offset_y
            
            # Ensure city center is within bounds
            city_x = max(20, min(self.grid_width - 20, city_x))
            city_y = max(20, min(self.grid_height - 20, city_y))
            
            self.city_centers.append((city_x, city_y))
        
        # Then add additional cities in other areas
        min_distance = min(self.grid_width, self.grid_height) // 4
        
        for _ in range(num_additional_cities):
            attempts = 0
            while attempts < 100:  # Prevent infinite loop
                x = random.randint(min_distance, self.grid_width - min_distance)
                y = random.randint(min_distance, self.grid_height - min_distance)
                
                # Check distance from existing cities (including building-centered ones)
                valid = True
                for existing_x, existing_y in self.city_centers:
                    distance = math.sqrt((x - existing_x)**2 + (y - existing_y)**2)
                    if distance < min_distance:
                        valid = False
                        break
                
                if valid:
                    self.city_centers.append((x, y))
                    break
                
                attempts += 1
    
    def _generate_organic_cities(self):
        """Create organic, irregular city shapes using noise"""
        for i, (city_x, city_y) in enumerate(self.city_centers):
            # Make cities around pre-placed buildings larger
            is_building_city = i < len(self.pre_placed_buildings)
            
            if is_building_city:
                base_radius = random.randint(20, 30)  # Larger for building cities
            else:
                base_radius = random.randint(12, 20)  # Smaller for additional cities
            
            # Create organic city shape
            for y in range(max(0, city_y - base_radius - 5), 
                          min(self.grid_height, city_y + base_radius + 5)):
                for x in range(max(0, city_x - base_radius - 5), 
                              min(self.grid_width, city_x + base_radius + 5)):
                    
                    # Calculate distance from city center
                    distance = math.sqrt((x - city_x)**2 + (y - city_y)**2)
                    
                    # Use our custom smooth noise to create irregular borders
                    noise_value = self._smooth_noise(x * self.noise_scale, y * self.noise_scale)
                    
                    # Adjust radius based on noise (creates organic shape)
                    effective_radius = base_radius + (noise_value * 8)
                    
                    # Create gradient from city center (denser in center)
                    if distance <= effective_radius:
                        # Closer to center = higher chance of being city
                        city_probability = 1.0 - (distance / effective_radius)
                        city_probability += noise_value * 0.3  # Add some randomness
                        
                        # Building cities have higher density
                        threshold = self.city_threshold * 0.8 if is_building_city else self.city_threshold
                        
                        if city_probability > threshold:
                            self.tile_grid[y][x] = TileType.CITY
                            # Assign a random city tile (1-7)
                            self.city_tile_grid[y][x] = random.randint(1, 7)
    
    def _generate_enhanced_road_network(self):
        """Generate roads connecting cities with branches into nature"""
        if len(self.city_centers) < 2:
            return
        
        # Connect each city to at least one other city (minimum spanning tree approach)
        connected_cities = set([0])  # Start with first city
        unconnected_cities = set(range(1, len(self.city_centers)))
        
        while unconnected_cities:
            # Find closest unconnected city to any connected city
            min_distance = float('inf')
            best_connection = None
            
            for connected_idx in connected_cities:
                for unconnected_idx in unconnected_cities:
                    distance = self._calculate_distance(
                        self.city_centers[connected_idx],
                        self.city_centers[unconnected_idx]
                    )
                    if distance < min_distance:
                        min_distance = distance
                        best_connection = (connected_idx, unconnected_idx)
            
            if best_connection:
                # Create road between cities
                road_path = self._create_road_path(
                    self.city_centers[best_connection[0]],
                    self.city_centers[best_connection[1]]
                )
                self.roads.append(road_path)
                
                # Add newly connected city to connected set
                connected_cities.add(best_connection[1])
                unconnected_cities.remove(best_connection[1])
        
        # Add some additional inter-city roads for variety (40% chance per city pair)
        for i in range(len(self.city_centers)):
            for j in range(i + 2, len(self.city_centers)):
                if random.random() < 0.4:
                    road_path = self._create_road_path(
                        self.city_centers[i],
                        self.city_centers[j]
                    )
                    self.roads.append(road_path)
        
        # Add roads that branch out into nature from each city
        self._generate_nature_branches()
    
    def _generate_nature_branches(self):
        """Generate roads that branch out from cities into nature areas"""
        for city_x, city_y in self.city_centers:
            # Create 1-3 branches per city
            num_branches = random.randint(1, 3)
            
            for _ in range(num_branches):
                # Choose a random direction for the branch
                angle = random.uniform(0, 2 * math.pi)
                
                # Branch length varies
                branch_length = random.randint(15, 35)
                
                # Calculate end point
                end_x = int(city_x + math.cos(angle) * branch_length)
                end_y = int(city_y + math.sin(angle) * branch_length)
                
                # Ensure end point is within bounds
                end_x = max(5, min(self.grid_width - 5, end_x))
                end_y = max(5, min(self.grid_height - 5, end_y))
                
                # Only create branch if it leads to mostly nature (not another city)
                if self._is_mostly_nature_area(end_x, end_y, 10):
                    # Create the branch road with some curves
                    branch_path = self._create_curved_nature_road(
                        (city_x, city_y), (end_x, end_y)
                    )
                    self.roads.append(branch_path)
    
    def _is_mostly_nature_area(self, center_x: int, center_y: int, radius: int) -> bool:
        """Check if an area is mostly nature (not city)"""
        city_tiles = 0
        total_tiles = 0
        
        for y in range(max(0, center_y - radius), min(self.grid_height, center_y + radius)):
            for x in range(max(0, center_x - radius), min(self.grid_width, center_x + radius)):
                if math.sqrt((x - center_x)**2 + (y - center_y)**2) <= radius:
                    total_tiles += 1
                    if self.tile_grid[y][x] == TileType.CITY:
                        city_tiles += 1
        
        if total_tiles == 0:
            return True
            
        city_percentage = city_tiles / total_tiles
        return city_percentage < 0.3  # Less than 30% city tiles
    
    def _create_curved_nature_road(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Create a curved road path that looks more natural"""
        path = []
        start_x, start_y = start
        end_x, end_y = end
        
        # Add 2-3 waypoints for more natural curves
        waypoints = [start]
        num_waypoints = random.randint(2, 3)
        
        for i in range(num_waypoints):
            progress = (i + 1) / (num_waypoints + 1)
            
            # Linear interpolation between start and end
            base_x = start_x + (end_x - start_x) * progress
            base_y = start_y + (end_y - start_y) * progress
            
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
                waypoints.append((int(base_x), int(base_y)))
        
        waypoints.append(end)
        
        # Connect all waypoints with straight lines
        for i in range(len(waypoints) - 1):
            segment_path = self._line_path(waypoints[i], waypoints[i + 1])
            path.extend(segment_path)
        
        # Apply road tiles to the path (narrower for nature roads)
        nature_road_width = max(1, self.road_width - 1)  # Slightly narrower
        
        for x, y in path:
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                # Create road with some width
                for dy in range(-nature_road_width//2, nature_road_width//2 + 1):
                    for dx in range(-nature_road_width//2, nature_road_width//2 + 1):
                        road_x, road_y = x + dx, y + dy
                        if (0 <= road_x < self.grid_width and 
                            0 <= road_y < self.grid_height):
                            self.tile_grid[road_y][road_x] = TileType.ROAD
                            # Use different tiles for nature roads (maybe more worn/natural looking)
                            self.city_tile_grid[road_y][road_x] = random.choice([1, 2, 3])  # Use tiles 1-3 for nature roads
        
        return path
    
    def _create_road_path(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Create a road path between two points using curved pathfinding"""
        path = []
        
        # Simple line-based pathfinding with some curves
        start_x, start_y = start
        end_x, end_y = end
        
        # Add some waypoints to create curved roads
        waypoints = [start]
        
        # Add 1-2 random waypoints for more interesting roads
        num_waypoints = random.randint(1, 2)
        for _ in range(num_waypoints):
            # Create waypoint roughly between start and end, with some offset
            mid_x = (start_x + end_x) // 2 + random.randint(-15, 15)
            mid_y = (start_y + end_y) // 2 + random.randint(-15, 15)
            
            # Ensure waypoint is within bounds
            mid_x = max(5, min(self.grid_width - 5, mid_x))
            mid_y = max(5, min(self.grid_height - 5, mid_y))
            
            waypoints.append((mid_x, mid_y))
        
        waypoints.append(end)
        
        # Connect all waypoints with straight lines
        for i in range(len(waypoints) - 1):
            segment_path = self._line_path(waypoints[i], waypoints[i + 1])
            path.extend(segment_path)
        
        # Apply road tiles to the path
        for x, y in path:
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                # Create road with some width
                for dy in range(-self.road_width//2, self.road_width//2 + 1):
                    for dx in range(-self.road_width//2, self.road_width//2 + 1):
                        road_x, road_y = x + dx, y + dy
                        if (0 <= road_x < self.grid_width and 
                            0 <= road_y < self.grid_height):
                            self.tile_grid[road_y][road_x] = TileType.ROAD
                            # Assign city tiles for main roads (4-7 for better roads)
                            self.city_tile_grid[road_y][road_x] = random.randint(4, 7)
        
        return path
    
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
    
    def _place_buildings_in_generated_cities(self, num_buildings_per_city: int):
        """Place buildings only in generated cities (not around pre-placed buildings)"""
        building_size = 3  # Size in tiles
        
        # Only place buildings in cities that weren't generated around pre-placed buildings
        cities_for_buildings = self.city_centers[len(self.pre_placed_buildings):]
        
        for city_x, city_y in cities_for_buildings:
            buildings_placed = 0
            attempts = 0
            
            while buildings_placed < num_buildings_per_city and attempts < 200:
                # Try to place building near city center
                offset_x = random.randint(-12, 12)
                offset_y = random.randint(-12, 12)
                
                building_tile_x = city_x + offset_x
                building_tile_y = city_y + offset_y
                
                # Check if location is valid (within city area and has space)
                if self._can_place_building(building_tile_x, building_tile_y, building_size):
                    # Convert tile coordinates to pixel coordinates
                    building_x = building_tile_x * self.tile_size
                    building_y = building_tile_y * self.tile_size
                    building_width = building_size * self.tile_size
                    building_height = building_size * self.tile_size
                    
                    building_rect = pygame.Rect(building_x, building_y, 
                                              building_width, building_height)
                    self.buildings.append(building_rect)
                    buildings_placed += 1
                
                attempts += 1
    
    def _can_place_building(self, tile_x: int, tile_y: int, size: int) -> bool:
        """Check if a building can be placed at the given tile coordinates"""
        # Check bounds
        if (tile_x < 0 or tile_y < 0 or 
            tile_x + size >= self.grid_width or 
            tile_y + size >= self.grid_height):
            return False
        
        # Check if area is in city and not occupied by roads
        for y in range(tile_y, tile_y + size):
            for x in range(tile_x, tile_x + size):
                if self.tile_grid[y][x] != TileType.CITY:
                    return False
        
        # Check distance from existing buildings
        building_center_x = (tile_x + size // 2) * self.tile_size
        building_center_y = (tile_y + size // 2) * self.tile_size
        
        for existing_building in self.buildings:
            distance = math.sqrt(
                (building_center_x - existing_building.centerx)**2 + 
                (building_center_y - existing_building.centery)**2
            )
            if distance < 80:  # Minimum distance between buildings
                return False
        
        return True
    
    def _add_flower_tiles_to_nature(self, flower_chance: float = 0.03, num_clusters: int = 12, cluster_size_range=(4, 6)):
        """Place sparse single flowers and a few clusters of flowers in nature areas"""
        # 1. Place clusters
        attempts = 0
        clusters_placed = 0
        max_attempts = num_clusters * 10
        while clusters_placed < num_clusters and attempts < max_attempts:
            # Pick a random center in a nature area
            y = random.randint(2, self.grid_height - 3)
            x = random.randint(2, self.grid_width - 3)
            if self.tile_grid[y][x] != TileType.NATURE:
                attempts += 1
                continue
            # Check if enough space for a cluster
            cluster_tiles = []
            cluster_size = random.randint(*cluster_size_range)
            # Try to make a compact cluster (2x2, 2x3, 3x2, or similar)
            offsets = [
                (0, 0), (1, 0), (0, 1), (1, 1),
                (0, -1), (-1, 0), (1, 1), (-1, -1),
                (0, 2), (2, 0), (-2, 0), (0, -2)
            ]
            random.shuffle(offsets)
            for dx, dy in offsets:
                tx, ty = x + dx, y + dy
                if (0 <= tx < self.grid_width and 0 <= ty < self.grid_height and
                    self.tile_grid[ty][tx] == TileType.NATURE):
                    cluster_tiles.append((tx, ty))
                    if len(cluster_tiles) >= cluster_size:
                        break
            if len(cluster_tiles) < cluster_size:
                attempts += 1
                continue
            # Place the cluster
            for tx, ty in cluster_tiles:
                self.tile_grid[ty][tx] = TileType.NATURE_FLOWER
            clusters_placed += 1
            attempts += 1
        # 2. Place sparse single flowers
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.tile_grid[y][x] == TileType.NATURE:
                    if random.random() < flower_chance:
                        self.tile_grid[y][x] = TileType.NATURE_FLOWER
    
    def _create_tile_surface(self) -> pygame.Surface:
        """Create the final tile surface based on the tile grid"""
        surface = pygame.Surface((self.width, self.height))
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                tile_type = self.tile_grid[y][x]
                
                # Create colored rectangles for different tile types
                # You can replace these with actual tile images later
                pixel_x = x * self.tile_size
                pixel_y = y * self.tile_size
                tile_rect = pygame.Rect(pixel_x, pixel_y, self.tile_size, self.tile_size)
                
                if tile_type == TileType.NATURE:
                    # Green for nature (floor_0.png equivalent)
                    color = (34, 139, 34)  # Forest green
                elif tile_type == TileType.NATURE_FLOWER:
                    # Pinkish for flower tile (flower_0.png equivalent)
                    color = (255, 182, 193)  # Light pink
                elif tile_type in [TileType.CITY, TileType.ROAD]:
                    # Different shades of gray for different city tiles (floor_1.png to floor_7.png)
                    city_tile_num = self.city_tile_grid[y][x]
                    # Create different shades based on tile number
                    base_gray = 100 + (city_tile_num * 15)  # Varies from 115 to 205
                    color = (base_gray, base_gray, base_gray)
                
                pygame.draw.rect(surface, color, tile_rect)
        
        return surface
    
    def create_interaction_zones(self, padding: int):
        """Create interaction zones around each building"""
        for building in self.buildings:
            zone_x = building.x - padding
            zone_y = building.y - padding
            zone_width = building.width + (padding * 2)
            zone_height = building.height + (padding * 2)
            interaction_zone = pygame.Rect(zone_x, zone_y, zone_width, zone_height)
            self.interaction_zones.append(interaction_zone)
    
    def get_tile_info_at_position(self, x: int, y: int) -> Tuple[int, int]:
        """Get the tile type and city tile number at a specific pixel position"""
        tile_x = x // self.tile_size
        tile_y = y // self.tile_size
        
        if (0 <= tile_x < self.grid_width and 0 <= tile_y < self.grid_height):
            tile_type = self.tile_grid[tile_y][tile_x]
            city_tile_num = self.city_tile_grid[tile_y][tile_x]
            return (tile_type, city_tile_num)
        
        return (TileType.NATURE, 0)  # Default to nature if out of bounds
    
    def is_walkable_at_position(self, x: int, y: int) -> bool:
        """Check if a pixel position is walkable (not blocked by collision)"""
        # Convert pixel coordinates to tile coordinates
        tile_x = x // self.tile_size
        tile_y = y // self.tile_size
        
        # If out of bounds, consider it walkable (nature)
        if not (0 <= tile_x < self.grid_width and 0 <= tile_y < self.grid_height):
            return True
        
        # All tile types should be walkable - the issue might be elsewhere
        # You can add specific collision logic here if needed
        return True
    
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
            'num_cities': len(self.city_centers),
            'num_buildings': len(self.buildings),
            'num_roads': len(self.roads),
            'pre_placed_buildings': len(self.pre_placed_buildings),
            'building_centered_cities': len(self.pre_placed_buildings),
            'additional_cities': len(self.city_centers) - len(self.pre_placed_buildings)
        }