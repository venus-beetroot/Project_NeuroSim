import pygame
from typing import Optional, List
from world.furniture import FurnitureInteraction


class FurnitureInteractionSystem:
    """System for managing furniture interactions"""
    
    def __init__(self, building_manager, keybind_manager=None):
        self.building_manager = building_manager
        self.keybind_manager = keybind_manager  # Add keybind manager reference
        self.current_interaction = None
        self.interaction_cooldown = 0
        self.COOLDOWN_TIME = 30  # frames
    
    def update(self, player, keys_pressed):
        """Update furniture interaction system"""
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1
            return
        
        # Check if player is inside a building
        if not self.building_manager.is_inside_building():
            return
        
        # Use keybind manager if available, otherwise fallback to R key
        if self.keybind_manager:
            # Check if furniture_interact key is pressed
            if self.keybind_manager.is_key_pressed("furniture_interact", keys_pressed):
                self._handle_interaction(player)
        else:
            # Fallback to R key (the default from settings)
            if keys_pressed[pygame.K_r]:
                self._handle_interaction(player)
    
    def _handle_interaction(self, player):
        """Handle furniture interaction"""
        # Get interactable furniture
        interactable_furniture = self.building_manager.get_interactable_furniture(player.rect)
        
        if not interactable_furniture:
            return
        
        # Find the closest furniture
        closest_furniture = self._get_closest_furniture(player, interactable_furniture)
        
        if closest_furniture:
            self._interact_with_furniture(closest_furniture, player)
            self.interaction_cooldown = self.COOLDOWN_TIME
    
    def _get_closest_furniture(self, player, furniture_list: List):
        """Get the closest furniture to the player"""
        if not furniture_list:
            return None
        
        closest = None
        min_distance = float('inf')
        
        for furniture in furniture_list:
            # Calculate distance to furniture center
            furniture_center_x = furniture.x + furniture.rect.width // 2
            furniture_center_y = furniture.y + furniture.rect.height // 2
            
            dx = player.x - furniture_center_x
            dy = player.y - furniture_center_y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest = furniture
        
        return closest
    
    def _interact_with_furniture(self, furniture, player):
        """Interact with specific furniture"""
        furniture_type = furniture.furniture_type
        
        if furniture_type == "chair":
            if not furniture.is_occupied:
                # Sit on chair
                FurnitureInteraction.sit_on_chair(furniture, player)
                self.current_interaction = furniture
            else:
                # Stand up from chair
                FurnitureInteraction.stand_up(furniture, player)
                self.current_interaction = None
        
        elif furniture_type == "table":
            # Interact with table
            FurnitureInteraction.interact_with_table(furniture, player)
        
        else:
            print(f"Unknown furniture type: {furniture_type}")
    
    def get_interaction_prompt(self, player) -> Optional[str]:
        """Get interaction prompt for nearby furniture"""
        if not self.building_manager.is_inside_building():
            return None
        
        interactable_furniture = self.building_manager.get_interactable_furniture(player.rect)
        
        if not interactable_furniture:
            return None
        
        closest_furniture = self._get_closest_furniture(player, interactable_furniture)
        
        if not closest_furniture:
            return None
        
        # Get the current furniture interaction key
        furniture_key = self._get_furniture_key_display()
        
        furniture_type = closest_furniture.furniture_type
        
        if furniture_type == "chair":
            if closest_furniture.is_occupied:
                return f"Press {furniture_key} to stand up"
            else:
                return f"Press {furniture_key} to sit down"
        
        elif furniture_type == "table":
            return f"Press {furniture_key} to examine table"
        
        return f"Press {furniture_key} to interact"
    
    def _get_furniture_key_display(self) -> str:
        """Get the display name for furniture interaction key"""
        if self.keybind_manager:
            # Get the current effective key for furniture interaction
            furniture_key = self.keybind_manager.get_effective_key("furniture_interact")
            # Convert pygame key constant to display name
            return self.keybind_manager.get_key_display_name(furniture_key)
        else:
            return "R"  # Fallback display
    
    def draw_interaction_prompt(self, surface: pygame.Surface, player, font):
        """Draw interaction prompt on screen"""
        prompt = self.get_interaction_prompt(player)
        
        if prompt:
            # Create text surface
            text_surface = font.render(prompt, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            
            # Position at bottom center of screen
            screen_width = surface.get_width()
            screen_height = surface.get_height()
            text_rect.centerx = screen_width // 2
            text_rect.bottom = screen_height - 50
            
            # Draw background
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(surface, (0, 0, 0, 128), bg_rect)
            pygame.draw.rect(surface, (255, 255, 255), bg_rect, 2)
            
            # Draw text
            surface.blit(text_surface, text_rect)
    
    def reset_interaction(self, player):
        """Reset current interaction (e.g., when leaving building)"""
        if self.current_interaction and self.current_interaction.furniture_type == "chair":
            FurnitureInteraction.stand_up(self.current_interaction, player)
        self.current_interaction = None