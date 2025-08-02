"""
Interior rendering and management system for buildings
"""
import pygame
import random
from typing import List, Tuple, Dict
from systems.collision_system import InteriorWall


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
        """Create darker versions of floor tiles for interior ambiance"""
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
        if not tiles:
            return
            
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


class InteriorLayout:
    """Manages the layout and structure of building interiors"""
    
    def __init__(self, config: Dict, interior_size: Tuple[int, int]):
        self.config = config
        self.interior_size = interior_size
        self.entrance_pos = self._calculate_entrance_pos()
        self.exit_pos = self._calculate_exit_pos()
        self.exit_zone = self._create_exit_zone()
        self.walls = []
    
    def _calculate_entrance_pos(self) -> Tuple[int, int]:
        """Calculate where player enters the interior"""
        return (self.interior_size[0] // 2, self.interior_size[1] - 50)
    
    def _calculate_exit_pos(self) -> Tuple[int, int]:
        """Calculate where the exit door is located"""
        return (self.interior_size[0] // 2, 50)
    
    def _create_exit_zone(self) -> pygame.Rect:
        """Create the interactive exit zone"""
        return pygame.Rect(
            self.exit_pos[0] - 50, self.exit_pos[1] - 30, 100, 60
        )
    
    def generate_walls(self) -> List[InteriorWall]:
        """Generate collision walls for the interior"""
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
        
        self.walls = walls
        return walls
    
    def get_interior_offset(self, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """Get the offset needed to center interior on screen"""
        interior_width, interior_height = self.interior_size
        offset_x = (screen_width - interior_width) // 2
        offset_y = (screen_height - interior_height) // 2
        return offset_x, offset_y
    
    def check_exit_range(self, rect: pygame.Rect) -> bool:
        """Check if a rectangle is in range to exit the building"""
        return self.exit_zone.colliderect(rect)


class InteriorManager:
    """High-level manager for interior systems"""
    
    def __init__(self, building):
        self.building = building
        self.layout = InteriorLayout(building.config, building.interior_size)
        self.renderer = InteriorRenderer(building)
        self.npcs_inside: List = []
        self.max_npcs = building.config["max_npcs"]
    
    def initialize(self, assets):
        """Initialize the interior with assets"""
        self.renderer.create_background(assets)
        self.layout.generate_walls()
    
    def can_add_npc(self) -> bool:
        """Check if an NPC can be added to the interior"""
        return len(self.npcs_inside) < self.max_npcs
    
    def add_npc(self, npc) -> bool:
        """Add an NPC to the interior"""
        if npc not in self.npcs_inside and self.can_add_npc():
            self.npcs_inside.append(npc)
            return True
        return False
    
    def remove_npc(self, npc) -> bool:
        """Remove an NPC from the interior"""
        if npc in self.npcs_inside:
            self.npcs_inside.remove(npc)
            return True
        return False
    
    def get_npc_count(self) -> int:
        """Get the number of NPCs currently inside"""
        return len(self.npcs_inside)
    
    def is_at_capacity(self) -> bool:
        """Check if interior is at NPC capacity"""
        return len(self.npcs_inside) >= self.max_npcs
    
    def get_walls(self) -> List[InteriorWall]:
        """Get collision walls for the interior"""
        return self.layout.walls
    
    def check_exit_range(self, rect: pygame.Rect) -> bool:
        """Check if a rectangle can exit the interior"""
        return self.layout.check_exit_range(rect)
    
    def get_entrance_pos(self) -> Tuple[int, int]:
        """Get the entrance position"""
        return self.layout.entrance_pos
    
    def get_exit_pos(self) -> Tuple[int, int]:
        """Get the exit position"""
        return self.layout.exit_pos
    
    def get_interior_offset(self, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """Get offset to center interior on screen"""
        return self.layout.get_interior_offset(screen_width, screen_height)
    
    def draw_interior(self, surface: pygame.Surface, debug_hitboxes: bool = False):
        """Draw the interior"""
        self.renderer.draw_interior(surface, debug_hitboxes)