import pygame

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
    
    def check_collision(self, other_rect):
        """Check if another rectangle collides with this building's hitbox"""
        return self.hitbox.colliderect(other_rect)
    
    def check_interaction_range(self, other_rect):
        """Check if another rectangle is in interaction range"""
        return self.interaction_zone.colliderect(other_rect)
    
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
    
    def update_position(self, x, y):
        """Update building position and recalculate hitboxes"""
        self.x = x
        self.y = y
        self.rect.topleft = (x, y)
        self.setup_hitbox()
        self.setup_interaction_zone()