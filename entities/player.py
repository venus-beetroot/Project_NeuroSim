import pygame
from functions import app  # Contains global settings like WIDTH, HEIGHT, PLAYER_SPEED, etc.
import math

class Player:
    def __init__(self, x, y, assets):
        ## Define all player attributes
        self.x = x # Set x position
        self.y = y # Set y position
        self.base_speed = app.PLAYER_SPEED  # Store base speed
        self.speed = app.PLAYER_SPEED

        self.animations = assets["player"] # Load the player animations
        self.state = "idle" # Set initial state
        self.frame_index = 0 # Set initial frame index
        self.animation_timer = 0 # Set initial animation timer
        self.animation_speed = 15 # Set animation speed

        self.image = self.animations[self.state][self.frame_index] # Set initial image
        self.rect = self.image.get_rect(center=(self.x, self.y)) # Set initial rect
        self.facing_left = False # Check facing 
        self.is_running = False
        self.inside_building = False
        self.last_building = None
        
        # Movement velocity for smooth collision
        self.vel_x = 0
        self.vel_y = 0

    ## Handle player input
    def handle_input(self, keybind_manager=None):
        """DEPRECATED: Input now handled by EventHandler"""
        # This method can be removed or kept as fallback
        pass

    def move_and_check_collisions(self, buildings):
        """Move player with robust collision detection"""
        
        # Store original position
        original_x = self.x
        original_y = self.y
        
        # Try horizontal movement first
        if self.vel_x != 0:
            # Calculate new position
            new_x = self.x + self.vel_x
            new_x = min(max(new_x, 0), 3000)  # Keep in bounds
            
            # Create temporary rect at new horizontal position
            temp_rect = self.rect.copy()
            temp_rect.centerx = new_x
            
            # Check for collisions with multiple small steps
            collision = self._check_collision_with_substeps(
                original_x, new_x, self.y, buildings, 'horizontal'
            )
            
            if not collision:
                self.x = new_x
                self.rect.centerx = self.x

        # Try vertical movement second
        if self.vel_y != 0:
            # Calculate new position  
            new_y = self.y + self.vel_y
            new_y = min(max(new_y, 0), 3000)  # Keep in bounds
            
            # Create temporary rect at new vertical position
            temp_rect = self.rect.copy()
            temp_rect.centery = new_y
            
            # Check for collisions with multiple small steps
            collision = self._check_collision_with_substeps(
                self.x, self.x, new_y, buildings, 'vertical'
            )
            
            if not collision:
                self.y = new_y
                self.rect.centery = self.y

    def sync_position(self):
        """Ensure x,y and rect.center are synchronized"""
        # This method can be called to fix any desync issues
        self.rect.centerx = self.x
        self.rect.centery = self.y

    def set_position(self, x, y):
        """Set player position and keep everything synchronized"""
        self.x = x
        self.y = y
        self.rect.centerx = x
        self.rect.centery = y

    ## Update player for each frame
    def update(self, buildings=None):
        # Handle movement with collision if buildings are provided
        if buildings is not None:
            self.move_and_check_collisions(buildings)
        else:
            # Fallback to old movement system if no buildings provided
            # Make sure to update BOTH x,y AND rect
            new_x = min(max(self.x + self.vel_x, 0), 3000)
            new_y = min(max(self.y + self.vel_y, 0), 3000)
            
            self.x = new_x
            self.y = new_y
            self.rect.centerx = self.x
            self.rect.centery = self.y

        # Update animation
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed: # Change animation frame
            self.animation_timer = 0 # Reset animation timer
            frames = self.animations[self.state] # Get current animation frames
            self.frame_index = (self.frame_index + 1) % len(frames) # Change frame index
            self.image = frames[self.frame_index] # Change image
            
            # Keep the center position when updating image rect
            center_x, center_y = self.rect.centerx, self.rect.centery
            self.rect = self.image.get_rect()
            self.rect.centerx = center_x
            self.rect.centery = center_y

    ## Draw player on screen 
    def draw(self, surface):
        if self.facing_left:
            flipped_image = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_image, self.rect)
        else:
            surface.blit(self.image, self.rect)

    ## Check if player can enter or exit building        
    def try_enter_exit_building(self, buildings, keybind_manager=None):
        """Check if player can enter or exit building - called when key is pressed"""
        
        # ENTER building
        if not self.inside_building:
            for building in buildings:
                interaction_zone = self.rect.inflate(20, 20)
                if interaction_zone.colliderect(building.rect):
                    print(f"Entered {building.building_type}")
                    self.inside_building = True
                    self.last_building = building
                    return "entered"

        # EXIT building (still using hardcoded Q for now)
        elif self.inside_building:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_q]:  # You might want to add this to keybind manager too
                print(f"Exited {self.last_building.building_type}")
                self.inside_building = False
                self.last_building = None
                return "exited"

        return None
    
    def _check_collision_with_substeps(self, start_x, end_x, y_pos, buildings, direction):
        """Check collision using small steps to prevent phasing through thin walls"""
        
        if direction == 'horizontal':
            # Check horizontal movement in small steps
            distance = abs(end_x - start_x)
            if distance == 0:
                return False
                
            steps = max(int(distance / 2), 1)  # At least 1 step, 2-pixel steps
            step_size = (end_x - start_x) / steps
            
            for i in range(1, steps + 1):
                test_x = start_x + (step_size * i)
                test_rect = self.rect.copy()
                test_rect.centerx = test_x
                test_rect.centery = y_pos
                
                if self._check_building_collision(test_rect, buildings):
                    return True
                    
        else:  # vertical
            # Check vertical movement in small steps
            distance = abs(y_pos - self.y)
            if distance == 0:
                return False
                
            steps = max(int(distance / 2), 1)  # At least 1 step, 2-pixel steps  
            step_size = (y_pos - self.y) / steps
            
            for i in range(1, steps + 1):
                test_y = self.y + (step_size * i)
                test_rect = self.rect.copy()
                test_rect.centerx = start_x
                test_rect.centery = test_y
                
                if self._check_building_collision(test_rect, buildings):
                    return True
        
        return False
    
    def _check_building_collision(self, test_rect, buildings):
        """Check if test_rect collides with any building - handles interior/exterior properly"""
        
        for building in buildings:
            if not building.is_solid:
                continue
                
            # Check if we're inside ANY building using the game's building manager
            if (hasattr(self, 'game_ref') and 
                hasattr(self.game_ref, 'building_manager') and 
                self.game_ref.building_manager.is_inside_building()):
                
                current_interior = self.game_ref.building_manager.get_current_interior()
                if current_interior == building:
                    # We're inside this building - check interior walls
                    interior_walls = self.game_ref.building_manager.get_interior_collision_walls()
                    for wall in interior_walls:
                        if wall.rect.colliderect(test_rect):
                            return True
                    continue  # Skip exterior collision for this building
            
            # Normal exterior collision
            if building.check_collision(test_rect):
                return True
        
        return False
    
    def try_interact_with_furniture(self, furnitures):
        """Handle furniture interaction with proper state management"""
        keys = pygame.key.get_pressed()

        if not hasattr(self, 'currently_interacting'):
            self.currently_interacting = False
        if not hasattr(self, 'can_move'):
            self.can_move = True

        if not self.currently_interacting and keys[pygame.K_r]:  # Use R key directly for now
            for furniture in furnitures:
                interaction_zone = self.rect.inflate(20, 20)
                if interaction_zone.colliderect(furniture.rect):
                    print(f"Interacting with {furniture.furniture_type}")
                    self.can_move = False
                    self.currently_interacting = True
                    return True
                    
        elif self.currently_interacting and keys[pygame.K_r]:
            print("Stopped interacting with furniture")
            self.can_move = True
            self.currently_interacting = False
            return False
        
        return None