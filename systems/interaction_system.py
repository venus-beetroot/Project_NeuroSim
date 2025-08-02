"""
Interaction system for buildings - handles entry/exit and player transitions
"""
import pygame
from dataclasses import dataclass
from typing import Optional, List, Tuple


@dataclass
class PlayerPosition:
    """Data class for storing player position and state"""
    x: float
    y: float
    rect_center: Tuple[int, int]


class InteractionZone:
    """Manages interaction zones around buildings"""
    
    def __init__(self, building_rect: pygame.Rect, interaction_padding: int):
        self.building_rect = building_rect
        self.interaction_padding = interaction_padding
        self.interaction_zone = self._create_interaction_zone()
    
    def _create_interaction_zone(self) -> pygame.Rect:
        """Create interaction zone around the building"""
        zone_x = self.building_rect.x - self.interaction_padding
        zone_y = self.building_rect.y - self.interaction_padding
        zone_width = self.building_rect.width + (self.interaction_padding * 2)
        zone_height = self.building_rect.height + (self.interaction_padding * 2)
        return pygame.Rect(zone_x, zone_y, zone_width, zone_height)
    
    def check_interaction_range(self, rect: pygame.Rect) -> bool:
        """Check if a rectangle is within interaction range"""
        return self.interaction_zone.colliderect(rect)
    
    def update_position(self, new_building_rect: pygame.Rect):
        """Update interaction zone when building moves"""
        self.building_rect = new_building_rect
        self.interaction_zone = self._create_interaction_zone()
    
    def draw_debug(self, surface: pygame.Surface, camera):
        """Draw debug visualization of interaction zone"""
        interaction_screen = camera.apply(self.interaction_zone)
        pygame.draw.rect(surface, (0, 255, 0), interaction_screen, 1)


class TransitionManager:
    """Manages transitions between exterior and interior spaces"""
    
    def __init__(self):
        self.current_interior = None
        self.exterior_position: Optional[PlayerPosition] = None
        self.transition_callbacks = []
    
    def add_transition_callback(self, callback):
        """Add a callback to be called on transitions"""
        self.transition_callbacks.append(callback)
    
    def _notify_transition(self, transition_type: str, building=None):
        """Notify all callbacks of a transition"""
        for callback in self.transition_callbacks:
            callback(transition_type, building)
    
    def can_enter_building(self, player_rect: pygame.Rect, buildings: List):
        """Check if player can enter any building"""
        if self.current_interior:
            return None
        
        for building in buildings:
            if (building.can_enter and 
                hasattr(building, 'interaction_zone') and 
                building.interaction_zone.check_interaction_range(player_rect)):
                return building
        return None
    
    def enter_building(self, building, player) -> bool:
        """Handle entering a building interior"""
        if not building.has_interior:
            return False
        
        # Save current exterior position
        self.exterior_position = PlayerPosition(
            x=player.x,
            y=player.y,
            rect_center=(player.rect.centerx, player.rect.centery)
        )
        
        # Move player to interior entrance
        self._position_player_in_building(player, building)
        self.current_interior = building
        
        # Notify callbacks
        self._notify_transition("enter", building)
        
        print(f"Player entered {building.building_type}")
        return True
    
    def _position_player_in_building(self, player, building):
        """Position player at building's entrance/exit zone"""
        if hasattr(building, 'interior_manager'):
            exit_pos = building.interior_manager.get_exit_pos()
            player.x = exit_pos[0]
            player.y = exit_pos[1]
            player.rect.centerx = exit_pos[0]
            player.rect.centery = exit_pos[1]
        else:
            # Fallback for buildings without interior_manager
            player.x = building.interior_size[0] // 2
            player.y = building.interior_size[1] - 50
            player.rect.centerx = player.x
            player.rect.centery = player.y
    
    def can_exit_building(self, player_rect: pygame.Rect) -> bool:
        """Check if player can exit current building"""
        if not self.current_interior:
            return False
        
        if hasattr(self.current_interior, 'interior_manager'):
            return self.current_interior.interior_manager.check_exit_range(player_rect)
        else:
            # Fallback for buildings without interior_manager
            return (hasattr(self.current_interior, 'exit_zone') and 
                   self.current_interior.exit_zone.colliderect(player_rect))
    
    def exit_building(self, player) -> bool:
        """Handle exiting current building"""
        if not self.current_interior or not self.exterior_position:
            return False
        
        # Store building type for logging
        building_type = self.current_interior.building_type
        building = self.current_interior
        
        # Restore exterior position
        self._restore_player_position(player)
        
        # Clear transition state
        self.current_interior = None
        self.exterior_position = None
        
        # Notify callbacks
        self._notify_transition("exit", building)
        
        print(f"Player exited {building_type}")
        return True
    
    def _restore_player_position(self, player):
        """Restore player to their exterior position"""
        if not self.exterior_position:
            return
        
        pos = self.exterior_position
        player.x = pos.x
        player.y = pos.y
        player.rect.centerx = pos.x
        player.rect.centery = pos.y
    
    def is_inside_building(self) -> bool:
        """Check if currently inside a building"""
        return self.current_interior is not None
    
    def get_current_interior(self):
        """Get current interior building"""
        return self.current_interior
    
    def reset(self):
        """Reset transition state (useful for cleanup)"""
        self.current_interior = None
        self.exterior_position = None


class BuildingInteractionSystem:
    """Main system for managing building interactions"""
    
    def __init__(self, buildings: List):
        self.buildings = buildings
        self.transition_manager = TransitionManager()
        self.interaction_zones = []
        self._create_interaction_zones()
    
    def _create_interaction_zones(self):
        """Create interaction zones for all buildings"""
        self.interaction_zones.clear()
        for building in self.buildings:
            if hasattr(building, 'config') and hasattr(building, 'rect'):
                interaction_padding = building.config.get("interaction_padding", 40)
                zone = InteractionZone(building.rect, interaction_padding)
                building.interaction_zone = zone
                self.interaction_zones.append(zone)
    
    def add_transition_callback(self, callback):
        """Add a callback for transition events"""
        self.transition_manager.add_transition_callback(callback)
    
    def check_building_entry(self, player_rect: pygame.Rect):
        """Check if player can enter any building"""
        return self.transition_manager.can_enter_building(player_rect, self.buildings)
    
    def enter_building(self, building, player) -> bool:
        """Enter a building interior"""
        return self.transition_manager.enter_building(building, player)
    
    def check_building_exit(self, player_rect: pygame.Rect) -> bool:
        """Check if player can exit current building"""
        return self.transition_manager.can_exit_building(player_rect)
    
    def exit_building(self, player) -> bool:
        """Exit current building"""
        return self.transition_manager.exit_building(player)
    
    def is_inside_building(self) -> bool:
        """Check if player is currently inside a building"""
        return self.transition_manager.is_inside_building()
    
    def get_current_interior(self):
        """Get the current interior building"""
        return self.transition_manager.get_current_interior()
    
    def update_building_positions(self):
        """Update interaction zones when buildings move (if needed)"""
        for i, building in enumerate(self.buildings):
            if i < len(self.interaction_zones):
                self.interaction_zones[i].update_position(building.rect)
    
    def draw_debug_zones(self, surface: pygame.Surface, camera):
        """Draw debug visualization of interaction zones"""
        for zone in self.interaction_zones:
            zone.draw_debug(surface, camera)
    
    def get_interaction_info(self) -> dict:
        """Get information about current interaction state"""
        return {
            "inside_building": self.is_inside_building(),
            "current_interior": self.get_current_interior(),
            "buildings_count": len(self.buildings),
            "interaction_zones_count": len(self.interaction_zones)
        }
    
    def cleanup(self):
        """Clean up the interaction system"""
        self.transition_manager.reset()
        self.interaction_zones.clear()