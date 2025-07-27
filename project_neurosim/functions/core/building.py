import pygame
import random

class InteriorWall:
    """Wrapper class for interior walls to match building interface"""
    
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.hitbox = self.rect  # For compatibility with collision system
        self.is_solid = True
        self.can_enter = False
    
    def check_collision(self, other_rect):
        """Check if another rectangle collides with this wall"""
        return self.hitbox.colliderect(other_rect)
    
    def get_collision_info(self, other_rect):
        """Get detailed collision information for advanced collision resolution"""
        if not self.check_collision(other_rect):
            return None
        
        # Calculate overlap amounts
        overlap_x = min(other_rect.right - self.hitbox.left, 
                       self.hitbox.right - other_rect.left)
        overlap_y = min(other_rect.bottom - self.hitbox.top, 
                       self.hitbox.bottom - other_rect.top)
        
        return {
            'overlap_x': overlap_x,
            'overlap_y': overlap_y,
            'from_left': other_rect.centerx < self.hitbox.centerx,
            'from_top': other_rect.centery < self.hitbox.centery
        }
    
    def resolve_collision(self, other_rect):
        """Resolve collision by pushing the other rect out of this wall"""
        collision_info = self.get_collision_info(other_rect)
        if not collision_info:
            return other_rect
        
        # Create a copy to modify
        resolved_rect = other_rect.copy()
        
        # Push out along the axis with smallest overlap
        if collision_info['overlap_x'] < collision_info['overlap_y']:
            # Push horizontally
            if collision_info['from_left']:
                resolved_rect.right = self.hitbox.left
            else:
                resolved_rect.left = self.hitbox.right
        else:
            # Push vertically
            if collision_info['from_top']:
                resolved_rect.bottom = self.hitbox.top
            else:
                resolved_rect.top = self.hitbox.bottom
        
        return resolved_rect


class Building:
    def __init__(self, x, y, building_type, assets):
        self.x = x
        self.y = y
        self.building_type = building_type  # "house" or "shop"
        
        # Load the building image from assets
        self.image = assets["building"][building_type][0]
        
        # Visual rectangle (for drawing)
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Collision hitbox - you can customize this per building type
        self.setup_hitbox()
        
        # Optional: Interaction zone (larger area around building for "Press E to enter")
        self.setup_interaction_zone()
        
        # Building properties
        self.can_enter = True
        self.is_solid = True  # Whether player can walk through it
        
        # Interior properties
        self.has_interior = True
        self.interior_size = (800, 600)  # Interior map size
        self.interior_background = None
        self.entrance_pos = (400, 550)  # Where player spawns inside
        self.exit_pos = (400, 50)  # Exit door position inside
        self.exit_zone = None
        
        # Create interior background
        self.create_interior_background(assets)
    
    def setup_hitbox(self):
        """Set up the collision hitbox for this building"""
        if self.building_type == "house":
            # House hitbox - maybe slightly smaller than the visual sprite
            # This creates a more realistic collision where player can get close to walls
            hitbox_width = self.rect.width - 20  # 10 pixels smaller on each side
            hitbox_height = self.rect.height - 10  # 5 pixels smaller on top/bottom
            
            # Center the hitbox on the building
            hitbox_x = self.rect.x + 10
            hitbox_y = self.rect.y + 5
            
        elif self.building_type == "shop":
            # Shop hitbox - maybe has a different shape
            hitbox_width = self.rect.width - 30
            hitbox_height = self.rect.height - 15
            
            hitbox_x = self.rect.x + 15
            hitbox_y = self.rect.y + 10
            
        else:
            # Default hitbox - same as visual rect
            hitbox_width = self.rect.width
            hitbox_height = self.rect.height
            hitbox_x = self.rect.x
            hitbox_y = self.rect.y
        
        self.hitbox = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
    
    def setup_interaction_zone(self):
        """Set up a larger zone around the building for interactions"""
        # Interaction zone is larger than the building
        zone_padding = 30  # 30 pixels around the building
        
        zone_x = self.rect.x - zone_padding
        zone_y = self.rect.y - zone_padding
        zone_width = self.rect.width + (zone_padding * 2)
        zone_height = self.rect.height + (zone_padding * 2)
        
        self.interaction_zone = pygame.Rect(zone_x, zone_y, zone_width, zone_height)
    
    def create_interior_background(self, assets):
        """Create the interior background with darker tiles"""
        if not self.has_interior:
            return
        
        self.interior_background = pygame.Surface(self.interior_size)
        
        # Get floor tiles and darken them
        floor_tiles = assets["floor_tiles"]
        darkened_tiles = []
        
        # Create darker versions of the tiles
        for tile in floor_tiles:
            dark_tile = tile.copy()
            # Apply dark overlay
            dark_overlay = pygame.Surface(tile.get_size())
            dark_overlay.fill((50, 50, 50))  # Dark overlay
            dark_tile.blit(dark_overlay, (0, 0), special_flags=pygame.BLEND_MULT)
            darkened_tiles.append(dark_tile)
        
        # Fill interior with dark tiles
        tile_w, tile_h = darkened_tiles[0].get_size()
        
        for y in range(0, self.interior_size[1], tile_h):
            for x in range(0, self.interior_size[0], tile_w):
                tile = random.choice(darkened_tiles)
                self.interior_background.blit(tile, (x, y))
        
        # Create walls around the interior
        self.create_interior_walls()
        
        # Set up exit zone (door to leave building)
        self.exit_zone = pygame.Rect(
            self.exit_pos[0] - 40, self.exit_pos[1] - 20, 80, 40
        )
    
    def create_interior_walls(self):
        """Create walls around the interior perimeter"""
        wall_color = (60, 40, 20)  # Dark brown walls
        wall_thickness = 20
        
        # Top wall
        pygame.draw.rect(self.interior_background, wall_color, 
                        (0, 0, self.interior_size[0], wall_thickness))
        
        # Bottom wall
        pygame.draw.rect(self.interior_background, wall_color, 
                        (0, self.interior_size[1] - wall_thickness, 
                         self.interior_size[0], wall_thickness))
        
        # Left wall
        pygame.draw.rect(self.interior_background, wall_color, 
                        (0, 0, wall_thickness, self.interior_size[1]))
        
        # Right wall
        pygame.draw.rect(self.interior_background, wall_color, 
                        (self.interior_size[0] - wall_thickness, 0, 
                         wall_thickness, self.interior_size[1]))
        
        # Create door opening at exit position
        door_width = 80
        door_height = wall_thickness
        door_x = self.exit_pos[0] - door_width // 2
        
        # Clear the wall area for the door (make it darker but passable)
        door_color = (40, 30, 15)  # Darker than walls
        pygame.draw.rect(self.interior_background, door_color,
                        (door_x, 0, door_width, door_height))
    
    def get_interior_walls(self):
        """Get collision rectangles for interior walls"""
        wall_thickness = 20
        walls = []
        
        # Top wall (except door area)
        door_width = 80
        door_x = self.exit_pos[0] - door_width // 2
        
        # Left part of top wall
        if door_x > 0:
            walls.append(InteriorWall(0, 0, door_x, wall_thickness))
        
        # Right part of top wall
        door_right = door_x + door_width
        if door_right < self.interior_size[0]:
            walls.append(InteriorWall(door_right, 0, 
                                   self.interior_size[0] - door_right, wall_thickness))
        
        # Bottom wall
        walls.append(InteriorWall(0, self.interior_size[1] - wall_thickness, 
                               self.interior_size[0], wall_thickness))
        
        # Left wall
        walls.append(InteriorWall(0, 0, wall_thickness, self.interior_size[1]))
        
        # Right wall
        walls.append(InteriorWall(self.interior_size[0] - wall_thickness, 0, 
                               wall_thickness, self.interior_size[1]))
        
        return walls
    
    def check_collision(self, other_rect):
        """Check if another rectangle collides with this building's hitbox"""
        return self.hitbox.colliderect(other_rect)
    
    def check_interaction_range(self, other_rect):
        """Check if another rectangle is in interaction range"""
        return self.interaction_zone.colliderect(other_rect)
    
    def check_exit_range(self, other_rect):
        """Check if player is in range to exit the building"""
        if not self.exit_zone:
            return False
        return self.exit_zone.colliderect(other_rect)
    
    def get_collision_info(self, other_rect):
        """Get detailed collision information for advanced collision resolution"""
        if not self.check_collision(other_rect):
            return None
        
        # Calculate overlap amounts
        overlap_x = min(other_rect.right - self.hitbox.left, 
                       self.hitbox.right - other_rect.left)
        overlap_y = min(other_rect.bottom - self.hitbox.top, 
                       self.hitbox.bottom - other_rect.top)
        
        return {
            'overlap_x': overlap_x,
            'overlap_y': overlap_y,
            'from_left': other_rect.centerx < self.hitbox.centerx,
            'from_top': other_rect.centery < self.hitbox.centery
        }
    
    def resolve_collision(self, other_rect):
        """Resolve collision by pushing the other rect out of this building"""
        collision_info = self.get_collision_info(other_rect)
        if not collision_info:
            return other_rect
        
        # Create a copy to modify
        resolved_rect = other_rect.copy()
        
        # Push out along the axis with smallest overlap
        if collision_info['overlap_x'] < collision_info['overlap_y']:
            # Push horizontally
            if collision_info['from_left']:
                resolved_rect.right = self.hitbox.left
            else:
                resolved_rect.left = self.hitbox.right
        else:
            # Push vertically
            if collision_info['from_top']:
                resolved_rect.bottom = self.hitbox.top
            else:
                resolved_rect.top = self.hitbox.bottom
        
        return resolved_rect
    
    def draw(self, surface, camera, debug_hitboxes=False):
        """Draw the building and optionally show hitboxes"""
        # Draw the building image
        draw_rect = camera.apply(self.rect)
        surface.blit(self.image, draw_rect)
        
        # Optional: Draw debug hitboxes
        if debug_hitboxes:
            # Draw collision hitbox in red
            hitbox_screen = camera.apply(self.hitbox)
            pygame.draw.rect(surface, (255, 0, 0), hitbox_screen, 2)
            
            # Draw interaction zone in green
            interaction_screen = camera.apply(self.interaction_zone)
            pygame.draw.rect(surface, (0, 255, 0), interaction_screen, 1)
    
    def draw_interior(self, surface, debug_hitboxes=False):
        """Draw the interior of the building centered on screen"""
        if not self.has_interior or not self.interior_background:
            return
        
        # Calculate offset to center the interior on the screen
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        interior_width, interior_height = self.interior_size
        
        offset_x = (screen_width - interior_width) // 2
        offset_y = (screen_height - interior_height) // 2
        
        # Draw interior background centered
        surface.blit(self.interior_background, (offset_x, offset_y))
        
        # Draw exit indicator with offset
        exit_color = (100, 100, 200)  # Light blue for exit
        centered_exit_zone = self.exit_zone.copy()
        centered_exit_zone.x += offset_x
        centered_exit_zone.y += offset_y
        pygame.draw.rect(surface, exit_color, centered_exit_zone, 3)
        
        # Optional: Draw interior walls for debugging with offset
        if debug_hitboxes:
            walls = self.get_interior_walls()
            for wall in walls:
                debug_rect = wall.rect.copy()
                debug_rect.x += offset_x
                debug_rect.y += offset_y
                pygame.draw.rect(surface, (255, 0, 0), debug_rect, 2)
    
    def get_interior_offset(self, screen_width, screen_height):
        """Get the offset needed to center interior on screen"""
        interior_width, interior_height = self.interior_size
        offset_x = (screen_width - interior_width) // 2
        offset_y = (screen_height - interior_height) // 2
        return offset_x, offset_y
    
    def update_position(self, x, y):
        """Update building position and recalculate hitboxes"""
        self.x = x
        self.y = y
        self.rect.topleft = (x, y)
        self.setup_hitbox()
        self.setup_interaction_zone()


class BuildingManager:
    """Manages building interactions and interior/exterior transitions"""
    
    def __init__(self, buildings):
        self.buildings = buildings
        self.current_interior = None  # Which building interior we're in
        self.player_exterior_pos = None  # Where player was before entering
    
    def check_building_entry(self, player_rect):
        """Check if player can enter any building"""
        if self.current_interior:  # Already inside
            return None
            
        for building in self.buildings:
            if building.can_enter and building.check_interaction_range(player_rect):
                return building
        return None
    
    def enter_building(self, building, player):
        """Enter a building interior"""
        if not building.has_interior:
            return False
        
        # Save exterior position (using both x,y and rect for consistency)
        self.player_exterior_pos = {
            'x': player.x,
            'y': player.y,
            'rect_center': (player.rect.centerx, player.rect.centery)
        }
        
        print(f"Saving exterior position: x={player.x}, y={player.y}, rect=({player.rect.centerx}, {player.rect.centery})")
        
        # Move player to the exit zone (purple rectangle) when entering
        # This makes it clear where the exit is and feels more natural
        player.x = building.exit_zone.centerx
        player.y = building.exit_zone.centery
        player.rect.centerx = building.exit_zone.centerx
        player.rect.centery = building.exit_zone.centery
        
        print(f"Set interior position: x={player.x}, y={player.y}, rect=({player.rect.centerx}, {player.rect.centery})")
        
        # Set current interior
        self.current_interior = building
        
        return True
    
    def check_building_exit(self, player_rect):
        """Check if player can exit current building"""
        if not self.current_interior:
            return False
        
        return self.current_interior.check_exit_range(player_rect)
    
    def exit_building(self, player):
        """Exit current building back to exterior"""
        if not self.current_interior or not self.player_exterior_pos:
            return False
        
        print(f"Before exit - Player: x={player.x}, y={player.y}, rect=({player.rect.centerx}, {player.rect.centery})")
        print(f"Restoring to saved position: {self.player_exterior_pos}")
        
        # Restore exterior position - update BOTH x,y AND rect consistently
        player.x = self.player_exterior_pos['x']
        player.y = self.player_exterior_pos['y']
        player.rect.centerx = self.player_exterior_pos['x']
        player.rect.centery = self.player_exterior_pos['y']
        
        print(f"After exit - Player: x={player.x}, y={player.y}, rect=({player.rect.centerx}, {player.rect.centery})")
        
        # Clear interior state
        self.current_interior = None
        self.player_exterior_pos = None
        
        return True
    
    def get_interior_collision_walls(self):
        """Get collision walls for current interior"""
        if not self.current_interior:
            return []
        
        return self.current_interior.get_interior_walls()
    
    def is_inside_building(self):
        """Check if player is currently inside a building"""
        return self.current_interior is not None
    
    def get_current_interior(self):
        """Get the current interior building"""
        return self.current_interior