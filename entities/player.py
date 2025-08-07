import pygame
from functions import app  # Contains global settings like WIDTH, HEIGHT, PLAYER_SPEED, etc.
import math

class Player:
    def __init__(self, x, y, assets):
        ## Define all player attributes
        self.x = x # Set x position
        self.y = y # Set y position
        self.speed = app.PLAYER_SPEED # Set player speed

        self.animations = assets["player"] # Load the player animations
        self.state = "idle" # Set initial state
        self.frame_index = 0 # Set initial frame index
        self.animation_timer = 0 # Set initial animation timer
        self.animation_speed = 8 # Set animation speed

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
        """Handle player input using keybind manager if available"""
        keys = pygame.key.get_pressed()
        self.vel_x, self.vel_y = 0, 0

        # Reset speed to default every frame
        self.speed = app.PLAYER_SPEED
        
        if keybind_manager:
            # Use keybind manager for input
            move_up_key = keybind_manager.get_key("move_up")
            move_down_key = keybind_manager.get_key("move_down")
            move_left_key = keybind_manager.get_key("move_left")
            move_right_key = keybind_manager.get_key("move_right")
            run_key = keybind_manager.get_key("run")
            
            # Check if run key is pressed
            if keys[run_key]:
                self.speed = app.PLAYER_SPEED * 2
                
            # Check movement keys
            if keys[move_left_key]:
                self.vel_x = -self.speed
            if keys[move_right_key]:
                self.vel_x = self.speed
            if keys[move_up_key]:
                self.vel_y = -self.speed
            if keys[move_down_key]:
                self.vel_y = self.speed
        else:
            # Fallback to hardcoded keys if no keybind manager
            if keys[pygame.K_LSHIFT]:
                self.speed = app.PLAYER_SPEED * 2

            if keys[pygame.K_a]:
                self.vel_x = -self.speed
            if keys[pygame.K_d]:
                self.vel_x = self.speed
            if keys[pygame.K_w]:
                self.vel_y = -self.speed
            if keys[pygame.K_s]:
                self.vel_y = self.speed

        # Apply diagonal movement factor
        if self.vel_x != 0 and self.vel_y != 0:
            self.vel_x *= 0.707  # √2/2 for diagonal movement
            self.vel_y *= 0.707

        # Update animation state
        if self.vel_x != 0 or self.vel_y != 0:
            self.state = "run"
        else:
            self.state = "idle"

        # Check player facing direction
        if self.vel_x < 0:
            self.facing_left = True
        elif self.vel_x > 0:
            self.facing_left = False

    def move_and_check_collisions(self, buildings):
        """Move player with smooth collision detection"""
        
        # Move horizontally first
        if self.vel_x != 0:
            new_x = self.x + self.vel_x
            # Keep within world bounds
            new_x = min(max(new_x, 0), 3000)
            
            # Create a temporary rect for collision checking
            temp_rect = self.rect.copy()
            temp_rect.centerx = new_x
            
            # Check collision with buildings
            collision = False
            for building in buildings:
                if building.is_solid and building.check_collision(temp_rect):
                    collision = True
                    break
            
            # Only move if no collision - update BOTH x and rect
            if not collision:
                self.x = new_x
                self.rect.centerx = self.x

        # Move vertically second
        if self.vel_y != 0:
            new_y = self.y + self.vel_y
            # Keep within world bounds
            new_y = min(max(new_y, 0), 3000)
            
            # Create a temporary rect for collision checking
            temp_rect = self.rect.copy()
            temp_rect.centery = new_y
            
            # Check collision with buildings
            collision = False
            for building in buildings:
                if building.is_solid and building.check_collision(temp_rect):
                    collision = True
                    break
            
            # Only move if no collision - update BOTH y and rect
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
        """Check if player can enter or exit building using keybind manager"""
        keys = pygame.key.get_pressed()
        
        # Get the building enter key from keybind manager
        if keybind_manager:
            enter_key = keybind_manager.get_key("building_enter")
        else:
            enter_key = pygame.K_e  # Fallback
        
        # ENTER building
        if not self.inside_building and keys[enter_key]:
            for building in buildings:
                interaction_zone = self.rect.inflate(20, 20)
                if interaction_zone.colliderect(building.rect):
                    print(f"Entered {building.building_type}")
                    self.inside_building = True
                    self.last_building = building
                    return "entered"

        # EXIT building (keep Q for now, or add exit_building keybind)
        elif self.inside_building and keys[pygame.K_q]:
            print(f"Exited {self.last_building.building_type}")
            self.inside_building = False
            self.last_building = None
            return "exited"

        return None