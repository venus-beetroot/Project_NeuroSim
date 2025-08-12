import random
from typing import List, Tuple
from .tilemap import TileMap, Tile

def generate_perfect_rectangular_city(tilemap: TileMap, center_x: int, center_y: int, 
                                    width: int, height: int) -> None:
    """
    Generate a perfectly rectangular city - GUARANTEED rectangular shape
    This is the simplest possible algorithm that just fills a rectangle
    """
    # Calculate bounds
    half_width = width // 2
    half_height = height // 2
    
    # Calculate exact bounds
    start_x = center_x - width // 2
    start_y = center_y - height // 2
    end_x = start_x + width
    end_y = start_y + height

    # Fill every single tile in the rectangle
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            tilemap.set_tile(x, y, Tile.CITY)

    print(f"Generated rectangular city at ({center_x}, {center_y}) size {width}x{height}")

def generate_rectangular_city_with_buildings(tilemap: TileMap, center_x: int, center_y: int,
                                           width: int, height: int, 
                                           num_buildings: int = 3) -> List[Tuple[int, int]]:
    """
    Generate rectangular city with buildings inside
    Returns list of building door positions
    """
    # First create the rectangular city area
    generate_perfect_rectangular_city(tilemap, center_x, center_y, width, height)
    
    # Calculate city bounds
    half_width = width // 2
    half_height = height // 2
    start_x = center_x - half_width
    start_y = center_y - half_height
    
    # Place some buildings inside the city
    buildings = []
    door_positions = []
    
    for i in range(num_buildings):
        # Random building size
        building_w = random.randint(3, 6)
        building_h = random.randint(3, 5)
        
        # Random position within city bounds (with margin)
        margin = 2
        building_x = random.randint(start_x + margin, 
                                  start_x + width - building_w - margin)
        building_y = random.randint(start_y + margin, 
                                  start_y + height - building_h - margin)
        
        # Place building
        for by in range(building_y, building_y + building_h):
            for bx in range(building_x, building_x + building_w):
                if 0 <= bx < tilemap.width and 0 <= by < tilemap.height:
                    tilemap.set_tile(bx, by, Tile.BUILDING)
        
        # Add door position (front center of building)
        door_x = building_x + building_w // 2
        door_y = building_y  # Front of building
        door_positions.append((door_x, door_y))
        
        buildings.append({
            'x': building_x, 'y': building_y,
            'width': building_w, 'height': building_h,
            'door': (door_x, door_y)
        })
    
    return door_positions

def generate_multiple_rectangular_cities(tilemap: TileMap, 
                                       city_centers: List[Tuple[int, int]],
                                       city_size: Tuple[int, int] = (30, 25)) -> List[List[Tuple[int, int]]]:
    """
    Generate multiple rectangular cities and return all door positions
    """
    all_door_positions = []
    width, height = city_size
    
    for center_x, center_y in city_centers:
        print(f"Generating city at ({center_x}, {center_y})")
        
        # Generate the rectangular city with buildings
        door_positions = generate_rectangular_city_with_buildings(
            tilemap, center_x, center_y, width, height, num_buildings=4
        )
        
        all_door_positions.append(door_positions)
        
        # Debug: Print city bounds
        half_width = width // 2
        half_height = height // 2
        start_x = center_x - half_width
        start_y = center_y - half_height
        end_x = start_x + width
        end_y = start_y + height
        print(f"  City bounds: ({start_x}, {start_y}) to ({end_x-1}, {end_y-1})")
    
    return all_door_positions

def debug_print_city_area(tilemap: TileMap, center_x: int, center_y: int, 
                         width: int, height: int) -> None:
    """
    Debug function to print what tiles are actually set in a city area
    """
    half_width = width // 2
    half_height = height // 2
    start_x = center_x - half_width
    start_y = center_y - half_height
    
    print(f"\nDEBUG: City area from ({start_x}, {start_y}) size {width}x{height}")
    
    city_count = 0
    nature_count = 0
    building_count = 0
    road_count = 0
    
    for y in range(start_y, start_y + height):
        for x in range(start_x, start_x + width):
            if 0 <= x < tilemap.width and 0 <= y < tilemap.height:
                tile = tilemap.get_tile(x, y)
                if tile == Tile.CITY:
                    city_count += 1
                elif tile == Tile.NATURE:
                    nature_count += 1
                elif tile == Tile.BUILDING:
                    building_count += 1
                elif tile == Tile.ROAD:
                    road_count += 1
    
    total = city_count + nature_count + building_count + road_count
    print(f"  Total tiles in area: {total}")
    print(f"  City tiles: {city_count}")
    print(f"  Nature tiles: {nature_count}")
    print(f"  Building tiles: {building_count}")
    print(f"  Road tiles: {road_count}")
    
    if nature_count > 0:
        print(f"  WARNING: Found {nature_count} nature tiles inside city area!")

# UPDATED MapGenerator method - replace your existing one:
def _generate_building_cities_enhanced_FIXED(self):
    """Generate rectangular cities around buildings using the SIMPLE algorithm"""
    
    for building_x, building_y in self.building_positions:
        print(f"\nGenerating city for building at ({building_x}, {building_y})")
        
        # Use the simple, guaranteed rectangular algorithm
        city_width = 30
        city_height = 25
        
        # Generate perfect rectangle
        generate_perfect_rectangular_city(
            self.tilemap, 
            building_x, building_y,  # Center position
            city_width, city_height
        )
        
        # Debug: Check what was actually generated
        debug_print_city_area(self.tilemap, building_x, building_y, 
                            city_width, city_height)
    
    print(f"\nGenerated {len(self.building_positions)} rectangular cities")

# Alternative: If you want cities that don't overlap, use this version:
def generate_non_overlapping_rectangular_cities(tilemap: TileMap, 
                                              city_centers: List[Tuple[int, int]],
                                              city_width: int = 30, 
                                              city_height: int = 25,
                                              min_spacing: int = 5) -> None:
    """
    Generate rectangular cities that don't overlap with each other
    """
    placed_cities = []
    
    for center_x, center_y in city_centers:
        # Check if this city would overlap with existing ones
        can_place = True
        
        for existing_x, existing_y in placed_cities:
            distance = max(abs(center_x - existing_x), abs(center_y - existing_y))
            required_distance = max(city_width, city_height) // 2 + min_spacing
            
            if distance < required_distance:
                can_place = False
                print(f"Skipping city at ({center_x}, {center_y}) - too close to ({existing_x}, {existing_y})")
                break
        
        if can_place:
            generate_perfect_rectangular_city(tilemap, center_x, center_y, 
                                            city_width, city_height)
            placed_cities.append((center_x, center_y))
            print(f"Placed city at ({center_x}, {center_y})")
        
    print(f"Successfully placed {len(placed_cities)} non-overlapping cities")

# Test function to verify rectangles are perfect:
def test_rectangle_generation():
    """Test function to verify the rectangle generation works"""
    # Create a small test tilemap
    test_map = TileMap(50, 50, Tile.NATURE)
    
    # Generate a city
    generate_perfect_rectangular_city(test_map, 25, 25, 20, 15)
    
    # Verify it's perfectly rectangular
    city_tiles = []
    for y in range(50):
        for x in range(50):
            if test_map.get_tile(x, y) == Tile.CITY:
                city_tiles.append((x, y))
    
    print(f"Generated {len(city_tiles)} city tiles")
    
    # Check bounds
    if city_tiles:
        min_x = min(pos[0] for pos in city_tiles)
        max_x = max(pos[0] for pos in city_tiles)
        min_y = min(pos[1] for pos in city_tiles)
        max_y = max(pos[1] for pos in city_tiles)
        
        actual_width = max_x - min_x + 1
        actual_height = max_y - min_y + 1
        
        print(f"City bounds: ({min_x}, {min_y}) to ({max_x}, {max_y})")
        print(f"Actual size: {actual_width}x{actual_height}")
        print(f"Expected size: 20x15")
        
        # Verify every tile in the rectangle is a city tile
        perfect_rectangle = True
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if test_map.get_tile(x, y) != Tile.CITY:
                    perfect_rectangle = False
                    print(f"Missing city tile at ({x}, {y})")
        
        if perfect_rectangle:
            print("SUCCESS: Perfect rectangle generated!")
        else:
            print("ERROR: Rectangle has holes!")

# Run the test
if __name__ == "__main__":
    test_rectangle_generation()