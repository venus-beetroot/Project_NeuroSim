import pygame
from typing import List, Dict, Optional, Tuple

class FurnitureConfig:
    """Configuration class for different building types"""
    
    FURNITURE_CONFIGS = {
        "chair": {
            "hitbox_padding": {"width": 20, "height": 10, "x": 10, "y": 5},
            "interaction_padding": 40,
        },
        "table": {
            "hitbox_padding": {"width": 30, "height": 15, "x": 15, "y": 10},
            "interaction_padding": 40,
        }
    }
    
    DEFAULT_CONFIG = {
        "hitbox_padding": {"width": 0, "height": 0, "x": 0, "y": 0},
        "interaction_padding": 40,
    }
    
    @classmethod
    def get_config(cls, furniture_type: str) -> Dict:
        """Get configuration for a building type"""
        return cls.FURNITURE_CONFIGS.get(furniture_type, cls.DEFAULT_CONFIG)
    

class InteriorFurniture:

    """Represents furniture items in building interiors"""
    
    def __init__(self, x: int, y: int, furniture_type: str, image: pygame.Surface, is_occupied = False):
        self.x = x
        self.y = y
        self.furniture_type = furniture_type
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_solid = True  # Whether player can walk through it
        self.is_occupied = is_occupied
        self.flip_image = False
                
        # Load configuration for this furniture type
        self.config = FurnitureConfig.get_config(furniture_type)
        
        # Set up collision and interaction areas
        self._setup_collision_areas()
        self._setup_interaction_zone()

        # Make collision hitbox smaller (reduce by 20 pixels on each side)
        margin = 20
        self.hitbox = pygame.Rect(
            self.rect.x + margin, 
            self.rect.y + margin, 
            self.rect.width - (margin * 2), 
            self.rect.height - (margin * 2)
        )

        # Make interaction zone smaller too (reduce by 10 pixels on each side)  
        interaction_margin = 10
        self.interaction_zone = pygame.Rect(
            self.rect.x - interaction_margin,
            self.rect.y - interaction_margin, 
            self.rect.width + (interaction_margin * 2),
            self.rect.height + (interaction_margin * 2)
        )
    
    def draw(self, surface: pygame.Surface, offset_x: int, offset_y: int):
        """Draw the furniture with offset"""
        draw_rect = self.rect.copy()
        draw_rect.x += offset_x
        draw_rect.y += offset_y
        surface.blit(self.image, draw_rect)

    def _setup_interaction_zone(self):
        """Set up interaction zone around the furniture"""
        interaction_padding = self.config["interaction_padding"]
        
        # Create interaction zone around the furniture
        zone_x = self.rect.x - interaction_padding
        zone_y = self.rect.y - interaction_padding
        zone_width = self.rect.width + (interaction_padding * 2)
        zone_height = self.rect.height + (interaction_padding * 2)
        self.interaction_zone = pygame.Rect(zone_x, zone_y, zone_width, zone_height)
    
    
    def get_collision_rect(self, offset_x: int, offset_y: int) -> pygame.Rect:
        """Get collision rectangle with offset"""
        collision_rect = self.rect.copy()
        collision_rect.x += offset_x
        collision_rect.y += offset_y
        return collision_rect
    
    def _setup_collision_areas(self):
        """Set up hitbox based on configuration"""
        padding = self.config["hitbox_padding"]
        
        # Setup hitbox
        hitbox_width = self.rect.width - padding["width"]
        hitbox_height = self.rect.height - padding["height"]
        hitbox_x = self.rect.x + padding["x"]
        hitbox_y = self.rect.y + padding["y"]
        self.hitbox = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
    
    def update_position(self, x: int, y: int):
        """Update furniture position and recalculate areas"""
        self.x = x
        self.y = y
        self.rect.topleft = (x, y)
        self._setup_collision_areas()
        self._setup_interaction_zone()
    
    def check_collision(self, other_rect: pygame.Rect) -> bool:
        """Check if another rectangle collides with this furniture's hitbox"""
        return self.hitbox.colliderect(other_rect)
    
    def check_interaction_range(self, other_rect: pygame.Rect) -> bool:
        """Check if another rectangle is within interaction range"""
        return self.interaction_zone.colliderect(other_rect)
    
    def get_collision_rect_with_offset(self, offset_x: int, offset_y: int) -> pygame.Rect:
        """Get collision rectangle with screen offset"""
        collision_rect = self.hitbox.copy()
        collision_rect.x += offset_x
        collision_rect.y += offset_y
        return collision_rect
    
    def get_interaction_rect_with_offset(self, offset_x: int, offset_y: int) -> pygame.Rect:
        """Get interaction rectangle with screen offset"""
        interaction_rect = self.interaction_zone.copy()
        interaction_rect.x += offset_x
        interaction_rect.y += offset_y
        return interaction_rect

class FurnitureInteraction:
    """Handles furniture interaction logic"""
    
    @staticmethod
    def sit_on_chair(furniture, player):
        """Make player sit on a chair"""
        if furniture.furniture_type == "chair" and not furniture.is_occupied:
            # Position player at the chair
            player.x = furniture.x + furniture.rect.width // 2
            player.y = furniture.y - 20 + furniture.rect.height // 2
            player.rect.centerx = player.x
            player.rect.centery = player.y
            
            # Mark chair as occupied and player as sitting
            furniture.is_occupied = True
            player.is_sitting = True
            player.can_move = False
            print(f"Player sat on {furniture.furniture_type}")
            return True
        return False
    
    @staticmethod
    def stand_up(furniture, player):
        """Make player stand up from furniture"""
        if furniture.furniture_type == "chair" and furniture.is_occupied:
            # Move player slightly away from chair
            player.x = furniture.x + furniture.rect.width + 20
            if player.rect.colliderect(furniture.rect):
                player.x = furniture.x + furniture.rect.width - 60

            player.y = furniture.y + furniture.rect.height // 2
            player.rect.centerx = player.x
            player.rect.centery = player.y
            
            # Mark chair as unoccupied and player as standing
            furniture.is_occupied = False
            player.is_sitting = False
            player.can_move = True
            print(f"Player stood up from {furniture.furniture_type}")
            return True
        return False
    
    @staticmethod
    def interact_with_table(furniture, player):
        """Handle table interaction"""
        if furniture.furniture_type == "table":
            print(f"Player is examining the {furniture.furniture_type}")
            # Add table-specific interaction logic here
            return True
        return False