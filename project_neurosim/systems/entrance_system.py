"""
Enhanced building interaction system with door-only entry
"""
import pygame
import math
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
from enum import Enum

class DoorSide(Enum):
    """Enum for door placement sides"""
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"

@dataclass
class Door:
    """Represents a building door with position and interaction zone"""
    x: int
    y: int
    width: int
    height: int
    side: DoorSide
    interaction_rect: pygame.Rect
    building_id: str
    
    def __post_init__(self):
        """Create door rect after initialization"""
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

@dataclass
class BuildingEntrance:
    """Defines building entrance configuration"""
    door_side: DoorSide
    door_width: int = 40
    door_height: int = 20
    interaction_padding: int = 30
    
class DoorInteractionSystem:
    """Manages door-based building entry system"""
    
    def __init__(self):
        self.building_doors: Dict[str, Door] = {}
        self.debug_mode: bool = False
    
    def register_building(self, building, door_config: BuildingEntrance):
        """Register a building with its door configuration"""
        building_id = self._get_building_id(building)
        
        # Calculate door position based on building rect and door side
        door_pos = self._calculate_door_position(building.rect, door_config)
        
        # Create interaction zone around the door
        interaction_rect = self._create_door_interaction_zone(
            door_pos, door_config.door_width, door_config.door_height,
            door_config.interaction_padding, door_config.door_side
        )
        
        # Create door object
        door = Door(
            x=door_pos[0],
            y=door_pos[1],
            width=door_config.door_width,
            height=door_config.door_height,
            side=door_config.door_side,
            interaction_rect=interaction_rect,
            building_id=building_id
        )
        
        self.building_doors[building_id] = door
        
        # Store door reference in building for easy access
        building.door = door
        building.entrance_config = door_config
    
    def _calculate_door_position(self, building_rect: pygame.Rect, 
                               door_config: BuildingEntrance) -> Tuple[int, int]:
        """Calculate door position based on building rect and door side"""
        door_x, door_y = 0, 0
        
        if door_config.door_side == DoorSide.NORTH:
            door_x = building_rect.centerx - door_config.door_width // 2
            door_y = building_rect.top - door_config.door_height
        
        elif door_config.door_side == DoorSide.SOUTH:
            door_x = building_rect.centerx - door_config.door_width // 2
            door_y = building_rect.bottom
        
        elif door_config.door_side == DoorSide.EAST:
            door_x = building_rect.right
            door_y = building_rect.centery - door_config.door_height // 2
        
        elif door_config.door_side == DoorSide.WEST:
            door_x = building_rect.left - door_config.door_width
            door_y = building_rect.centery - door_config.door_height // 2
        
        return (door_x, door_y)
    
    def _create_door_interaction_zone(self, door_pos: Tuple[int, int], 
                                    door_width: int, door_height: int,
                                    padding: int, door_side: DoorSide) -> pygame.Rect:
        """Create an interaction zone in front of the door"""
        door_x, door_y = door_pos
        
        if door_side == DoorSide.NORTH:
            # Interaction zone above the door (player approaches from above)
            zone_x = door_x - padding
            zone_y = door_y - padding
            zone_width = door_width + (padding * 2)
            zone_height = padding + door_height // 2
        
        elif door_side == DoorSide.SOUTH:
            # Interaction zone below the door (player approaches from below)
            zone_x = door_x - padding
            zone_y = door_y + door_height - door_height // 2
            zone_width = door_width + (padding * 2)
            zone_height = padding + door_height // 2
        
        elif door_side == DoorSide.EAST:
            # Interaction zone to the right of door (player approaches from right)
            zone_x = door_x + door_width - door_width // 2
            zone_y = door_y - padding
            zone_width = padding + door_width // 2
            zone_height = door_height + (padding * 2)
        
        elif door_side == DoorSide.WEST:
            # Interaction zone to the left of door (player approaches from left)
            zone_x = door_x - padding
            zone_y = door_y - padding
            zone_width = padding + door_width // 2
            zone_height = door_height + (padding * 2)
        
        return pygame.Rect(zone_x, zone_y, zone_width, zone_height)
    
    def check_door_interaction(self, player_rect: pygame.Rect, buildings: List) -> Optional[BuildingEntrance]:
        """Check if player can interact with any door"""
        for building in buildings:
            building_id = self._get_building_id(building)
            door = self.building_doors.get(building_id)
            
            if door and hasattr(building, 'can_enter') and building.can_enter:
                if door.interaction_rect.colliderect(player_rect):
                    # Additional check: player must be facing the door
                    if self._is_player_facing_door(player_rect, door):
                        return building
        
        return None
    
    def _is_player_facing_door(self, player_rect: pygame.Rect, door: Door) -> bool:
        """Check if player is positioned correctly to use the door"""
        player_center_x = player_rect.centerx
        player_center_y = player_rect.centery
        door_center_x = door.rect.centerx
        door_center_y = door.rect.centery
        
        # Calculate angle from player to door
        dx = door_center_x - player_center_x
        dy = door_center_y - player_center_y
        
        # For doors, we want the player to approach from the correct side
        if door.side == DoorSide.NORTH:
            # Player should be above the door (negative dy)
            return dy < -10
        elif door.side == DoorSide.SOUTH:
            # Player should be below the door (positive dy)
            return dy > 10
        elif door.side == DoorSide.EAST:
            # Player should be to the right of the door (positive dx)
            return dx > 10
        elif door.side == DoorSide.WEST:
            # Player should be to the left of the door (negative dx)
            return dx < -10
        
        return True  # Default allow
    
    def update_building_position(self, building):
        """Update door position when building moves"""
        building_id = self._get_building_id(building)
        if building_id in self.building_doors and hasattr(building, 'entrance_config'):
            # Recalculate door position
            door_config = building.entrance_config
            door_pos = self._calculate_door_position(building.rect, door_config)
            
            # Update door
            door = self.building_doors[building_id]
            door.x, door.y = door_pos
            door.rect.topleft = door_pos
            door.interaction_rect = self._create_door_interaction_zone(
                door_pos, door_config.door_width, door_config.door_height,
                door_config.interaction_padding, door_config.door_side
            )
    
    def get_door_position(self, building) -> Optional[Tuple[int, int]]:
        """Get the door position for a building"""
        building_id = self._get_building_id(building)
        door = self.building_doors.get(building_id)
        return (door.x, door.y) if door else None
    
    def draw_doors(self, surface: pygame.Surface, camera=None):
        """Draw all doors (for debugging or visual representation)"""
        for door in self.building_doors.values():
            # Apply camera transformation if provided
            door_rect = camera.apply(door.rect) if camera else door.rect
            
            # Draw door as brown rectangle
            pygame.draw.rect(surface, (139, 69, 19), door_rect)
            pygame.draw.rect(surface, (101, 67, 33), door_rect, 2)
            
            # Draw door handle
            handle_size = 4
            if door.side in [DoorSide.NORTH, DoorSide.SOUTH]:
                handle_x = door_rect.right - 8
                handle_y = door_rect.centery - handle_size // 2
            else:  # EAST or WEST
                handle_x = door_rect.centerx - handle_size // 2
                handle_y = door_rect.bottom - 8
            
            pygame.draw.circle(surface, (255, 215, 0), 
                             (handle_x, handle_y), handle_size)
    
    def draw_debug_zones(self, surface: pygame.Surface, camera=None):
        """Draw debug visualization of door interaction zones"""
        if not self.debug_mode:
            return
        
        for door in self.building_doors.values():
            # Apply camera transformation if provided
            interaction_rect = camera.apply(door.interaction_rect) if camera else door.interaction_rect
            door_rect = camera.apply(door.rect) if camera else door.rect
            
            # Draw interaction zone in green
            pygame.draw.rect(surface, (0, 255, 0), interaction_rect, 2)
            
            # Draw door outline in red
            pygame.draw.rect(surface, (255, 0, 0), door_rect, 3)
            
            # Draw door direction indicator
            self._draw_door_direction_indicator(surface, door_rect, door.side)
    
    def _draw_door_direction_indicator(self, surface: pygame.Surface, 
                                     door_rect: pygame.Rect, door_side: DoorSide):
        """Draw an arrow indicating door direction"""
        center_x = door_rect.centerx
        center_y = door_rect.centery
        arrow_length = 20
        
        # Calculate arrow direction based on door side
        if door_side == DoorSide.NORTH:
            end_x, end_y = center_x, center_y - arrow_length
        elif door_side == DoorSide.SOUTH:
            end_x, end_y = center_x, center_y + arrow_length
        elif door_side == DoorSide.EAST:
            end_x, end_y = center_x + arrow_length, center_y
        elif door_side == DoorSide.WEST:
            end_x, end_y = center_x - arrow_length, center_y
        
        # Draw arrow
        pygame.draw.line(surface, (255, 255, 0), (center_x, center_y), (end_x, end_y), 3)
        
        # Draw arrowhead
        arrow_size = 5
        if door_side == DoorSide.NORTH:
            points = [(end_x, end_y), (end_x - arrow_size, end_y + arrow_size), 
                     (end_x + arrow_size, end_y + arrow_size)]
        elif door_side == DoorSide.SOUTH:
            points = [(end_x, end_y), (end_x - arrow_size, end_y - arrow_size), 
                     (end_x + arrow_size, end_y - arrow_size)]
        elif door_side == DoorSide.EAST:
            points = [(end_x, end_y), (end_x - arrow_size, end_y - arrow_size), 
                     (end_x - arrow_size, end_y + arrow_size)]
        elif door_side == DoorSide.WEST:
            points = [(end_x, end_y), (end_x + arrow_size, end_y - arrow_size), 
                     (end_x + arrow_size, end_y + arrow_size)]
        
        pygame.draw.polygon(surface, (255, 255, 0), points)
    
    def _get_building_id(self, building) -> str:
        """Generate unique ID for a building"""
        if hasattr(building, 'building_id'):
            return building.building_id
        elif hasattr(building, 'x') and hasattr(building, 'y'):
            return f"building_{int(building.x)}_{int(building.y)}"
        else:
            return f"building_{id(building)}"
    
    def set_debug_mode(self, enabled: bool):
        """Toggle debug visualization"""
        self.debug_mode = enabled
    
    def get_interaction_info(self) -> Dict:
        """Get debug information about door system"""
        return {
            "total_doors": len(self.building_doors),
            "debug_mode": self.debug_mode,
            "doors": {
                building_id: {
                    "position": (door.x, door.y),
                    "side": door.side.value,
                    "interaction_zone": {
                        "x": door.interaction_rect.x,
                        "y": door.interaction_rect.y,
                        "width": door.interaction_rect.width,
                        "height": door.interaction_rect.height
                    }
                }
                for building_id, door in self.building_doors.items()
            }
        }
    
    def cleanup(self):
        """Clean up the door system"""
        self.building_doors.clear()


# Usage example and integration helper
class BuildingDoorIntegration:
    """Helper class to integrate door system with existing building system"""
    
    @staticmethod
    def setup_building_doors(buildings: List, door_system: DoorInteractionSystem):
        """Setup doors for all buildings with default configurations"""
        for building in buildings:
            # Determine door side based on building type or position
            door_side = BuildingDoorIntegration._determine_door_side(building)
            
            # Create door configuration
            door_config = BuildingEntrance(
                door_side=door_side,
                door_width=40,
                door_height=20,
                interaction_padding=25
            )
            
            # Register building with door system
            door_system.register_building(building, door_config)
    
    @staticmethod
    def _determine_door_side(building) -> DoorSide:
        """Determine the best door side for a building"""
        # You can implement logic here based on:
        # - Building type
        # - Surrounding terrain
        # - Road connections
        # - Building orientation
        
        # For now, default to south-facing doors (most common)
        if hasattr(building, 'building_type'):
            # Houses typically have south-facing doors
            if 'house' in building.building_type.lower():
                return DoorSide.SOUTH
            # Shops might face the road/street
            elif 'shop' in building.building_type.lower():
                return DoorSide.SOUTH
            # Special buildings might have different orientations
            elif 'temple' in building.building_type.lower():
                return DoorSide.WEST
        
        # Default to south
        return DoorSide.SOUTH