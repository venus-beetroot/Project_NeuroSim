import pygame
from functions.assets import app
from functions.core.player import Player

class NPC:

    def __init__(self, x, y, assets, name):

        ## Define all NPC atritubes
        self.x = x # Set x position
        self.y = y # Set y position
        self.speed = app.PLAYER_SPEED # Set npc speed
        self.is_running = False
        self.name = name # Set npc name

        self.animations = assets["player"] 
        #####!! TESTING WITH THE PLAYER ASSETS FOR NOW !!#####
        #####!! TESTING WITH THE PLAYER ASSETS FOR NOW !!#####


        self.state = "idle" # Set initial state
        self.frame_index = 0 # Set initial frame index
        self.animation_timer = 0 # Set initial animation timer
        self.animation_speed = 8 # Set animation speed

        self.image = self.animations[self.state][self.frame_index] # Set initial image
        self.rect = self.image.get_rect(center=(self.x, self.y)) # Set initial rect
        self.facing_left = False # Check facing 

        self.chat_history = []  # Store chat history

        # Assign a preset dialogue introduction
        if self.name == "Dave":
            self.dialogue = "Hello, I'm Dave. I love adventures in this digital world!"
        elif self.name == "Lisa":
            self.dialogue = "Hi, I'm Lisa. Coding and coffee fuel my day!"
        elif self.name == "Tom":
            self.dialogue = "Hey, I'm Tom. Always here to keep things running smoothly!"
        else:
            self.dialogue = "Hello, I'm just an NPC."



    ## Update NPC for each frame
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


    ## Draw NPC on screen 
    def draw(self, surface):
        if self.facing_left:
            flipped_image = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_image, self.rect)
        else:
            surface.blit(self.image, self.rect)





