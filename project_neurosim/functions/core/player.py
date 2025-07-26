import pygame
from functions.assets import app  # Contains global settings like WIDTH, HEIGHT, PLAYER_SPEED, etc.
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
    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.vel_x, self.vel_y = 0, 0

        # Reset speed to default every frame
        self.speed = app.PLAYER_SPEED
        # If pressed shift, increase speed
        if keys[pygame.K_LSHIFT]:
            self.speed = app.PLAYER_SPEED * 2

        if keys[pygame.K_a]:
            self.vel_x = -self.speed # Move left
        if keys[pygame.K_d]:
            self.vel_x = self.speed # Move right
        if keys[pygame.K_w]:
            self.vel_y = -self.speed # Move up
        if keys[pygame.K_s]:
            self.vel_y = self.speed # Move down

        # Update animation state
        if self.vel_x != 0 or self.vel_y != 0:
            self.state = "run"  # Change state to "run" if moving
        else:
            self.state = "idle" # Change state to "idle" if not moving

        ##Check player facing direction
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
            
            # Only move if no collision
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
            
            # Only move if no collision
            if not collision:
                self.y = new_y
                self.rect.centery = self.y

    ## Update player for each frame
    def update(self, buildings=None):
        # Handle movement with collision if buildings are provided
        if buildings is not None:
            self.move_and_check_collisions(buildings)
        else:
            # Fallback to old movement system if no buildings provided
            self.x = min(max(self.x + self.vel_x, 0), 3000) 
            self.y = min(max(self.y + self.vel_y, 0), 3000) 
            self.rect.center = (self.x, self.y)

        # Update animation
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed: # Change animation frame
            self.animation_timer = 0 # Reset animation timer
            frames = self.animations[self.state] # Get current animation frames
            self.frame_index = (self.frame_index + 1) % len(frames) # Change frame index
            self.image = frames[self.frame_index] # Change image
            center = self.rect.center # Update rect
            self.rect = self.image.get_rect() # Update rect
            self.rect.center = center  # Update rect

    ## Draw player on screen 
    def draw(self, surface):
        if self.facing_left:
            flipped_image = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_image, self.rect)
        else:
            surface.blit(self.image, self.rect)

    ## Check if player can enter or exit building        
    def try_enter_exit_building(self, buildings):
        keys = pygame.key.get_pressed()

        # ENTER building
        if not self.inside_building and keys[pygame.K_e]:
            for building in buildings:
                interaction_zone = self.rect.inflate(20, 20)
                if interaction_zone.colliderect(building.rect):
                    print(f"Entered {building.building_type}")
                    self.inside_building = True
                    self.last_building = building
                    return "entered"

        # EXIT building
        elif self.inside_building and keys[pygame.K_q]:
            print(f"Exited {self.last_building.building_type}")
            self.inside_building = False
            self.last_building = None
            return "exited"

        return None