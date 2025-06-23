import pygame
import app  # Contains global settings like WIDTH, HEIGHT, PLAYER_SPEED, etc.
import math

class Player:
    def __init__(self, x, y, assets):
        ## Define all player atritubes
        self.x = x # Set x position
        self.y = y # Set y position
        self.speed = app.PLAYER_SPEED # Set player speed

        self.animations = assets["player"] # Load the player animations
        self.state = "idle" # Set initial state
        self.frame_index = 0 # Set initial frame index
        self.animation_timer = 0 # Set initial animation timer
        self.animation_speed = 8 # Set animation speed
        
        self.invincible = False  # Add invincibility attribute
        self.invincibility_timer = 0  # Timer for invincibility frames
        self.invincibility_duration = 60  # Duration of invincibility in frames

        self.image = self.animations[self.state][self.frame_index] # Set initial image
        self.rect = self.image.get_rect(center=(self.x, self.y)) # Set initial rect
        self.facing_left = False # Check facing 
 
        self.health = 5 # Set starting health 
        self.xp = 0 # Set starting xp
        self.level = 1 # Set starting level




    ## Handle player input
    def handle_input(self):
        keys = pygame.key.get_pressed()
        vel_x, vel_y = 0, 0

        if keys[pygame.K_a]:
            vel_x = -self.speed # Move left
        if keys[pygame.K_d]:
            vel_x = self.speed # Move right
        if keys[pygame.K_w]:
            vel_y = -self.speed # Move up
        if keys[pygame.K_s]:
            vel_y = self.speed # Move down

        #Make sure the player does not go off screen
        self.x = min(max(self.x + vel_x, 0), app.WIDTH) 
        self.y = min(max(self.y + vel_y, 0), app.HEIGHT) 
        self.rect.center = (self.x, self.y)

        if vel_x != 0 or vel_y != 0:
            self.state = "run"  # Change state to "run" if moving
        else:
            self.state = "idle" # Change state to "idle" if not moving
 

        ##Check player facing direction
        if vel_x < 0:
            self.facing_left = True
        elif vel_x > 0:
            self.facing_left = False


    ## Update player for each frame
    def update(self):

        self.animation_timer += 1

        if self.animation_timer >= self.animation_speed: # Change animation frame
            self.animation_timer = 0 # Reset animation timer
            frames = self.animations[self.state] # Get current animation frames
            self.frame_index = (self.frame_index + 1) % len(frames) # Change frame index
            self.image = frames[self.frame_index] # Change image
            center = self.rect.center # Update rect
            self.rect = self.image.get_rect() # Update rect
            self.rect.center = center  # Update rect


        if self.invincible:  # Decrement invincibility timer if invincible
            self.invincibility_timer -= 1 # Decrement invincibility timer
            if self.invincibility_timer <= 0: # If invincibility timer runs out
                self.invincible = False  # Reset invincibility when timer runs out


    ## Draw player on screen 
    def draw(self, surface):
        if self.facing_left:
            flipped_image = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_image, self.rect)
        else:
            surface.blit(self.image, self.rect)

    ## Take damage method
    def take_damage(self, amount):
        if not self.invincible:  # Only take damage if not invincible
            self.health = max(0, self.health - amount)
            self.invincible = True  # Set invincible to True
            self.invincibility_timer = self.invincibility_duration 




