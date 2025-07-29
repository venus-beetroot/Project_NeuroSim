import pygame
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple


@dataclass
class CollisionInfo:
    """Data class for collision information"""
    overlap_x: float
    overlap_y: float
    from_left: bool
    from_top: bool


class CollisionMixin:
    """Mixin class providing collision detection and resolution"""
    
    def check_collision(self, other_rect: pygame.Rect) -> bool:
        """Check if another rectangle collides with this object's hitbox"""
        return self.hitbox.colliderect(other_rect)
    
    def get_collision_info(self, other_rect: pygame.Rect) -> Optional[CollisionInfo]:
        """Get detailed collision information for collision resolution"""
        if not self.check_collision(other_rect):
            return None
        
        overlap_x = min(other_rect.right - self.hitbox.left, 
                       self.hitbox.right - other_rect.left)
        overlap_y = min(other_rect.bottom - self.hitbox.top, 
                       self.hitbox.bottom - other_rect.top)
        
        return CollisionInfo(
            overlap_x=overlap_x,
            overlap_y=overlap_y,
            from_left=other_rect.centerx < self.hitbox.centerx,
            from_top=other_rect.centery < self.hitbox.centery
        )
    
    def resolve_collision(self, other_rect: pygame.Rect) -> pygame.Rect:
        """Resolve collision by pushing the other rect out of this object"""
        collision_info = self.get_collision_info(other_rect)
        if not collision_info:
            return other_rect
        
        resolved_rect = other_rect.copy()
        
        # Push out along the axis with smallest overlap
        if collision_info.overlap_x < collision_info.overlap_y:
            # Push horizontally
            if collision_info.from_left:
                resolved_rect.right = self.hitbox.left
            else:
                resolved_rect.left = self.hitbox.right
        else:
            # Push vertically
            if collision_info.from_top:
                resolved_rect.bottom = self.hitbox.top
            else:
                resolved_rect.top = self.hitbox.bottom
        
        return resolved_rect


class InteriorWall(CollisionMixin):
    """Wrapper class for interior walls"""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.hitbox = self.rect  # For compatibility with collision system
        self.is_solid = True
        self.can_enter = False


class BuildingConfig:
    """Configuration class for different building types"""
    
    BUILDING_CONFIGS = {
        "house": {
            "hitbox_padding": {"width": 20, "height": 10, "x": 10, "y": 5},
            "interaction_padding": 40,
            "max_npcs": 3,
            "interior_size": (800, 600),
            "wall_thickness": 20,
            "door_width": 100
        },
        "shop": {
            "hitbox_padding": {"width": 30, "height": 15, "x": 15, "y": 10},
            "interaction_padding": 40,
            "max_npcs": 4,
            "interior_size": (900, 700),
            "wall_thickness": 25,
            "door_width": 120
        }
    }
    
    DEFAULT_CONFIG = {
        "hitbox_padding": {"width": 0, "height": 0, "x": 0, "y": 0},
        "interaction_padding": 40,
        "max_npcs": 3,
        "interior_size": (800, 600),
        "wall_thickness": 20,
        "door_width": 100
    }
    
    @classmethod
    def get_config(cls, building_type: str) -> Dict:
        """Get configuration for a building type"""
        return cls.BUILDING_CONFIGS.get(building_type, cls.DEFAULT_CONFIG)


class InteriorRenderer:
    """Handles interior rendering and background creation"""
    
    def __init__(self, building):
        self.building = building
        self.background = None
        self.wall_color = (60, 40, 20)
        self.door_color = (40, 30, 15)
    
    def create_background(self, assets):
        """Create the interior background with darker tiles"""
        if not self.building.has_interior:
            return
        
        self.background = pygame.Surface(self.building.interior_size)
        darkened_tiles = self._create_darkened_tiles(assets["floor_tiles"])
        self._fill_with_tiles(darkened_tiles)
        self._create_walls()
    
    def _create_darkened_tiles(self, floor_tiles: List[pygame.Surface]) -> List[pygame.Surface]:
        """Create darker versions of floor tiles"""
        darkened_tiles = []
        for tile in floor_tiles:
            dark_tile = tile.copy()
            dark_overlay = pygame.Surface(tile.get_size())
            dark_overlay.fill((50, 50, 50))
            dark_tile.blit(dark_overlay, (0, 0), special_flags=pygame.BLEND_MULT)
            darkened_tiles.append(dark_tile)
        return darkened_tiles
    
    def _fill_with_tiles(self, tiles: List[pygame.Surface]):
        """Fill interior background with tiles"""
        tile_w, tile_h = tiles[0].get_size()
        for y in range(0, self.building.interior_size[1], tile_h):
            for x in range(0, self.building.interior_size[0], tile_w):
                tile = random.choice(tiles)
                self.background.blit(tile, (x, y))
    
    def _create_walls(self):
        """Create walls around the interior perimeter"""
        wall_thickness = self.building.config["wall_thickness"]
        width, height = self.building.interior_size
        
        # Draw perimeter walls
        walls_data = [
            (0, 0, width, wall_thickness),  # Top
            (0, height - wall_thickness, width, wall_thickness),  # Bottom
            (0, 0, wall_thickness, height),  # Left
            (width - wall_thickness, 0, wall_thickness, height)  # Right
        ]
        
        for wall_rect in walls_data:
            pygame.draw.rect(self.background, self.wall_color, wall_rect)
        
        self._create_door_opening()
    
    def _create_door_opening(self):
        """Create door opening at exit position"""
        door_width = self.building.config["door_width"]
        wall_thickness = self.building.config["wall_thickness"]
        door_x = self.building.exit_pos[0] - door_width // 2
        
        pygame.draw.rect(self.background, self.door_color,
                        (door_x, 0, door_width, wall_thickness))
    
    def draw_interior(self, surface: pygame.Surface, debug_hitboxes: bool = False):
        """Draw the interior centered on screen"""
        if not self.background:
            return
        
        offset_x, offset_y = self._get_center_offset(surface)
        surface.blit(self.background, (offset_x, offset_y))
        
        self._draw_exit_indicator(surface, offset_x, offset_y)
        
        if debug_hitboxes:
            self._draw_debug_walls(surface, offset_x, offset_y)
    
    def _get_center_offset(self, surface: pygame.Surface) -> Tuple[int, int]:
        """Calculate offset to center interior on screen"""
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        interior_width, interior_height = self.building.interior_size
        
        offset_x = (screen_width - interior_width) // 2
        offset_y = (screen_height - interior_height) // 2
        return offset_x, offset_y
    
    def _draw_exit_indicator(self, surface: pygame.Surface, offset_x: int, offset_y: int):
        """Draw exit zone indicator"""
        exit_color = (100, 100, 200)
        centered_exit_zone = self.building.exit_zone.copy()
        centered_exit_zone.x += offset_x
        centered_exit_zone.y += offset_y
        pygame.draw.rect(surface, exit_color, centered_exit_zone, 3)
    
    def _draw_debug_walls(self, surface: pygame.Surface, offset_x: int, offset_y: int):
        """Draw debug visualization of interior walls"""
        walls = self.building.get_interior_walls()
        for wall in walls:
            debug_rect = wall.rect.copy()
            debug_rect.x += offset_x
            debug_rect.y += offset_y
            pygame.draw.rect(surface, (255, 0, 0), debug_rect, 2)


class NPCManager:
    """Manages NPCs inside buildings"""
    
    def __init__(self, max_npcs: int):
        self.npcs_inside: List = []
        self.max_npcs = max_npcs
    
    def can_add_npc(self) -> bool:
        """Check if an NPC can be added"""
        return len(self.npcs_inside) < self.max_npcs
    
    def add_npc(self, npc) -> bool:
        """Add an NPC to the building"""
        if npc not in self.npcs_inside and self.can_add_npc():
            self.npcs_inside.append(npc)
            return True
        return False
    
    def remove_npc(self, npc) -> bool:
        """Remove an NPC from the building"""
        if npc in self.npcs_inside:
            self.npcs_inside.remove(npc)
            return True
        return False
    
    def get_count(self) -> int:
        """Get the number of NPCs currently inside"""
        return len(self.npcs_inside)
    
    def is_at_capacity(self) -> bool:
        """Check if building is at NPC capacity"""
        return len(self.npcs_inside) >= self.max_npcs


class Building(CollisionMixin):
    """Main building class with improved organization"""
    
    def __init__(self, x: int, y: int, building_type: str, assets):
        self.x = x
        self.y = y
        self.building_type = building_type
        self.config = BuildingConfig.get_config(building_type)
        
        # Load building image and set up rectangles
        self.image = assets["building"][building_type][0]
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Initialize components
        self._setup_collision_areas()
        self._setup_interior()
        
        # Initialize managers
        self.npc_manager = NPCManager(self.config["max_npcs"])
        self.interior_renderer = InteriorRenderer(self)
        
        # Building properties
        self.can_enter = True
        self.is_solid = True
        self.has_interior = True
        
        # Create interior background
        self.interior_renderer.create_background(assets)
    
    def _setup_collision_areas(self):
        """Set up hitbox and interaction zones"""
        padding = self.config["hitbox_padding"]
        
        # Setup hitbox
        hitbox_width = self.rect.width - padding["width"]
        hitbox_height = self.rect.height - padding["height"]
        hitbox_x = self.rect.x + padding["x"]
        hitbox_y = self.rect.y + padding["y"]
        self.hitbox = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
        
        # Setup interaction zone
        zone_padding = self.config["interaction_padding"]
        zone_x = self.rect.x - zone_padding
        zone_y = self.rect.y - zone_padding
        zone_width = self.rect.width + (zone_padding * 2)
        zone_height = self.rect.height + (zone_padding * 2)
        self.interaction_zone = pygame.Rect(zone_x, zone_y, zone_width, zone_height)
    
    def _setup_interior(self):
        """Set up interior properties"""
        self.interior_size = self.config["interior_size"]
        self.entrance_pos = (self.interior_size[0] // 2, self.interior_size[1] - 50)
        self.exit_pos = (self.interior_size[0] // 2, 50)
        
        # Create exit zone
        self.exit_zone = pygame.Rect(
            self.exit_pos[0] - 50, self.exit_pos[1] - 30, 100, 60
        )
    
    def check_interaction_range(self, other_rect: pygame.Rect) -> bool:
        """Check if another rectangle is in interaction range"""
        return self.interaction_zone.colliderect(other_rect)
    
    def check_exit_range(self, other_rect: pygame.Rect) -> bool:
        """Check if player is in range to exit the building"""
        return self.exit_zone and self.exit_zone.colliderect(other_rect)
    
    def get_interior_walls(self) -> List[InteriorWall]:
        """Get collision rectangles for interior walls"""
        wall_thickness = self.config["wall_thickness"]
        door_width = self.config["door_width"]
        door_x = self.exit_pos[0] - door_width // 2
        
        walls = []
        
        # Top wall (with door opening)
        if door_x > 0:
            walls.append(InteriorWall(0, 0, door_x, wall_thickness))
        
        door_right = door_x + door_width
        if door_right < self.interior_size[0]:
            walls.append(InteriorWall(door_right, 0, 
                                   self.interior_size[0] - door_right, wall_thickness))
        
        # Other walls
        walls.extend([
            InteriorWall(0, self.interior_size[1] - wall_thickness, 
                        self.interior_size[0], wall_thickness),  # Bottom
            InteriorWall(0, 0, wall_thickness, self.interior_size[1]),  # Left
            InteriorWall(self.interior_size[0] - wall_thickness, 0, 
                        wall_thickness, self.interior_size[1])  # Right
        ])
        
        return walls
    
    def update_position(self, x: int, y: int):
        """Update building position and recalculate areas"""
        self.x = x
        self.y = y
        self.rect.topleft = (x, y)
        self._setup_collision_areas()
    
    def get_interior_offset(self, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """Get the offset needed to center interior on screen"""
        interior_width, interior_height = self.interior_size
        offset_x = (screen_width - interior_width) // 2
        offset_y = (screen_height - interior_height) // 2
        return offset_x, offset_y
    
    def draw(self, surface: pygame.Surface, camera, debug_hitboxes: bool = False):
        """Draw the building and optionally show debug info"""
        # Draw the building image
        draw_rect = camera.apply(self.rect)
        surface.blit(self.image, draw_rect)
        
        if debug_hitboxes:
            self._draw_debug_info(surface, camera)
    
    def _draw_debug_info(self, surface: pygame.Surface, camera):
        """Draw debug hitboxes and information"""
        # Draw collision hitbox in red
        hitbox_screen = camera.apply(self.hitbox)
        pygame.draw.rect(surface, (255, 0, 0), hitbox_screen, 2)
        
        # Draw interaction zone in green
        interaction_screen = camera.apply(self.interaction_zone)
        pygame.draw.rect(surface, (0, 255, 0), interaction_screen, 1)
    
    def draw_interior(self, surface: pygame.Surface, debug_hitboxes: bool = False):
        """Draw the interior of the building"""
        self.interior_renderer.draw_interior(surface, debug_hitboxes)
    
    # NPC management methods (delegated to NPCManager)
    def can_npc_enter(self) -> bool:
        return self.npc_manager.can_add_npc()
    
    def add_npc(self, npc) -> bool:
        return self.npc_manager.add_npc(npc)
    
    def remove_npc(self, npc) -> bool:
        return self.npc_manager.remove_npc(npc)
    
    def get_npc_count(self) -> int:
        return self.npc_manager.get_count()


@dataclass
class PlayerPosition:
    """Data class for storing player position"""
    x: float
    y: float
    rect_center: Tuple[int, int]


class TransitionManager:
    """Manages transitions between exterior and interior"""
    
    def __init__(self):
        self.current_interior: Optional[Building] = None
        self.exterior_position: Optional[PlayerPosition] = None
    
    def can_enter_building(self, player_rect: pygame.Rect, buildings: List[Building]) -> Optional[Building]:
        """Check if player can enter any building"""
        if self.current_interior:
            return None
        
        for building in buildings:
            if building.can_enter and building.check_interaction_range(player_rect):
                return building
        return None
    
    def enter_building(self, building: Building, player) -> bool:
        """Handle entering a building"""
        if not building.has_interior:
            return False
        
        # Save current position
        self.exterior_position = PlayerPosition(
            x=player.x,
            y=player.y,
            rect_center=(player.rect.centerx, player.rect.centery)
        )
        
        # Move player to exit zone
        self._position_player_in_building(player, building)
        self.current_interior = building
        
        print(f"Player entered {building.building_type}")
        return True
    
    def _position_player_in_building(self, player, building: Building):
        """Position player at building's exit zone"""
        player.x = building.exit_zone.centerx
        player.y = building.exit_zone.centery
        player.rect.centerx = building.exit_zone.centerx
        player.rect.centery = building.exit_zone.centery
    
    def can_exit_building(self, player_rect: pygame.Rect) -> bool:
        """Check if player can exit current building"""
        return (self.current_interior and 
                self.current_interior.check_exit_range(player_rect))
    
    def exit_building(self, player) -> bool:
        """Handle exiting current building"""
        if not self.current_interior or not self.exterior_position:
            return False
        
        # Restore exterior position
        self._restore_player_position(player)
        
        # Clear transition state
        building_type = self.current_interior.building_type
        self.current_interior = None
        self.exterior_position = None
        
        print(f"Player exited {building_type}")
        return True
    
    def _restore_player_position(self, player):
        """Restore player to exterior position"""
        pos = self.exterior_position
        player.x = pos.x
        player.y = pos.y
        player.rect.centerx = pos.x
        player.rect.centery = pos.y
    
    def is_inside_building(self) -> bool:
        """Check if currently inside a building"""
        return self.current_interior is not None
    
    def get_current_interior(self) -> Optional[Building]:
        """Get current interior building"""
        return self.current_interior


class BuildingManager:
    """Main manager for building system"""
    
    def __init__(self, buildings: List[Building]):
        self.buildings = buildings
        self.transition_manager = TransitionManager()
    
    def check_building_entry(self, player_rect: pygame.Rect) -> Optional[Building]:
        """Check if player can enter any building"""
        return self.transition_manager.can_enter_building(player_rect, self.buildings)
    
    def enter_building(self, building: Building, player) -> bool:
        """Enter a building interior"""
        return self.transition_manager.enter_building(building, player)
    
    def check_building_exit(self, player_rect: pygame.Rect) -> bool:
        """Check if player can exit current building"""
        return self.transition_manager.can_exit_building(player_rect)
    
    def exit_building(self, player) -> bool:
        """Exit current building"""
        return self.transition_manager.exit_building(player)
    
    def get_interior_collision_walls(self) -> List[InteriorWall]:
        """Get collision walls for current interior"""
        current_interior = self.transition_manager.get_current_interior()
        return current_interior.get_interior_walls() if current_interior else []
    
    def is_inside_building(self) -> bool:
        """Check if player is currently inside a building"""
        return self.transition_manager.is_inside_building()
    
    def get_current_interior(self) -> Optional[Building]:
        """Get the current interior building"""
        return self.transition_manager.get_current_interior()
    
    def get_building_info(self) -> List[Dict]:
        """Get information about all buildings and their NPC counts"""
        return [
            {
                'type': building.building_type,
                'position': (building.x, building.y),
                'npc_count': building.get_npc_count(),
                'max_npcs': building.npc_manager.max_npcs
            }
            for building in self.buildings
        ]