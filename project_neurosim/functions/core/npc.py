import pygame
import random
import math
from functions.assets import app
from functions.core.player import Player

class NPC:

    def __init__(self, x, y, assets, name, hangout_area=None):

        ## Define all NPC attributes
        self.x = x # Set x position
        self.y = y # Set y position
        self.speed = app.PLAYER_SPEED * 0.7  # NPCs move slightly slower than player
        self.is_running = False
        self.name = name # Set npc name

        self.animations = assets["player"] 
        #####!! TESTING WITH THE PLAYER ASSETS FOR NOW !!#####

        self.state = "idle" # Set initial state
        self.frame_index = 0 # Set initial frame index
        self.animation_timer = 0 # Set initial animation timer
        self.animation_speed = 8 # Set animation speed

        self.image = self.animations[self.state][self.frame_index] # Set initial image
        self.rect = self.image.get_rect(center=(self.x, self.y)) # Set initial rect
        self.facing_left = False # Check facing 

        self.chat_history = []  # Store chat history

        # Movement and AI attributes
        self.target_x = x
        self.target_y = y
        self.movement_timer = 0
        self.movement_delay = random.randint(120, 300)  # Frames before next movement decision
        self.is_stopped_by_player = False
        self.player_detection_radius = 80  # Distance to detect player
        self.stop_distance = 50  # Distance to stop when player is near
        
        # Hangout area (85% chance to move here, 15% chance to wander elsewhere)
        if hangout_area:
            self.hangout_area = hangout_area  # Dictionary with 'x', 'y', 'width', 'height'
        else:
            # Default hangout area around spawn point
            self.hangout_area = {
                'x': x - 100,
                'y': y - 100,
                'width': 200,
                'height': 200
            }
        
        # Speech bubble attributes
        self.show_speech_bubble = False
        self.speech_bubble_timer = 0
        self.speech_bubble_duration = 180  # 3 seconds at 60 FPS
        
        # SEPARATED DIALOGUE SYSTEMS
        # bubble_dialogue: Always shows the default introduction in speech bubbles
        # dialogue: Used by AI chat system (will be overwritten by AI responses)
        if self.name == "Dave":
            self.bubble_dialogue = "Hello, I'm Dave. I love adventures in this digital world!"
            self.dialogue = "You are Dave, an adventurous NPC who loves exploring the digital world. You're friendly and enthusiastic about new experiences."
        elif self.name == "Lisa":
            self.bubble_dialogue = "Hi, I'm Lisa. Coding and coffee fuel my day!"
            self.dialogue = "You are Lisa, a tech-savvy NPC who loves coding and coffee. You're knowledgeable and helpful with technical topics."
        elif self.name == "Tom":
            self.bubble_dialogue = "Hey, I'm Tom. Always here to keep things running smoothly!"
            self.dialogue = "You are Tom, a reliable NPC who keeps things organized and running smoothly. You're dependable and solution-oriented."
        else:
            self.bubble_dialogue = "Hello, I'm just an NPC."
            self.dialogue = "You are a generic NPC in a game world."

    def get_distance_to_player(self, player):
        """Calculate distance between NPC and player"""
        dx = self.rect.centerx - player.rect.centerx
        dy = self.rect.centery - player.rect.centery
        return math.sqrt(dx * dx + dy * dy)

    def face_player(self, player):
        """Make NPC face the player"""
        if player.rect.centerx < self.rect.centerx:
            self.facing_left = True
        else:
            self.facing_left = False

    def choose_new_target(self):
        """Choose a new target position for movement"""
        # 85% chance to move within hangout area, 15% chance to wander elsewhere
        if random.random() < 0.85:
            # Move within hangout area
            self.target_x = random.randint(
                self.hangout_area['x'], 
                self.hangout_area['x'] + self.hangout_area['width']
            )
            self.target_y = random.randint(
                self.hangout_area['y'], 
                self.hangout_area['y'] + self.hangout_area['height']
            )
        else:
            # Wander elsewhere (you can adjust these bounds based on your world size)
            self.target_x = random.randint(0, 1200)  # Adjust based on your world width
            self.target_y = random.randint(0, 800)   # Adjust based on your world height

    def move_towards_target(self):
        """Move NPC towards target position"""
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 5:  # If not close enough to target
            # Normalize direction and apply speed
            move_x = (dx / distance) * self.speed
            move_y = (dy / distance) * self.speed
            
            # Update position
            self.rect.centerx += move_x
            self.rect.centery += move_y
            
            # Update facing direction based on movement
            if move_x < 0:
                self.facing_left = True
            elif move_x > 0:
                self.facing_left = False
            
            # Set animation state to walking
            self.state = "run" if "run" in self.animations else "idle"
        else:
            # Reached target, set to idle
            self.state = "idle"

    def update(self, player=None):
        """Update NPC for each frame"""
        
        # Handle player interaction
        if player:
            distance_to_player = self.get_distance_to_player(player)
            
            # Check if player is near
            if distance_to_player <= self.player_detection_radius:
                # Stop moving and face player
                self.is_stopped_by_player = True
                self.face_player(player)
                self.state = "idle"
                
                # Show speech bubble when player is very close
                if distance_to_player <= self.stop_distance:
                    self.show_speech_bubble = True
                    self.speech_bubble_timer = self.speech_bubble_duration
            else:
                self.is_stopped_by_player = False
        
        # Handle speech bubble timer
        if self.show_speech_bubble:
            self.speech_bubble_timer -= 1
            if self.speech_bubble_timer <= 0:
                self.show_speech_bubble = False

        # Movement logic (only if not stopped by player)
        if not self.is_stopped_by_player:
            self.movement_timer += 1
            
            # Check if it's time to choose a new target
            if self.movement_timer >= self.movement_delay:
                self.choose_new_target()
                self.movement_timer = 0
                self.movement_delay = random.randint(120, 300)  # Reset delay
            
            # Move towards current target
            self.move_towards_target()

        # Handle animation
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.animations[self.state]
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]
            center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = center

    def draw_speech_bubble(self, surface, font):
        """Draw speech bubble above NPC using bubble_dialogue (not affected by AI)"""
        if not self.show_speech_bubble:
            return
        
        # Use bubble_dialogue instead of dialogue for speech bubbles
        text_surface = font.render(self.bubble_dialogue, True, (0, 0, 0))
        text_rect = text_surface.get_rect()
        
        # Calculate bubble dimensions
        bubble_width = text_rect.width + 20
        bubble_height = text_rect.height + 16
        bubble_x = self.rect.centerx - bubble_width // 2
        bubble_y = self.rect.top - bubble_height - 10
        
        # Draw bubble background
        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)
        pygame.draw.rect(surface, (255, 255, 255), bubble_rect)
        pygame.draw.rect(surface, (0, 0, 0), bubble_rect, 2)
        
        # Draw bubble tail (triangle pointing down)
        tail_points = [
            (self.rect.centerx - 10, bubble_y + bubble_height),
            (self.rect.centerx + 10, bubble_y + bubble_height),
            (self.rect.centerx, bubble_y + bubble_height + 10)
        ]
        pygame.draw.polygon(surface, (255, 255, 255), tail_points)
        pygame.draw.polygon(surface, (0, 0, 0), tail_points, 2)
        
        # Draw text
        text_x = bubble_x + 10
        text_y = bubble_y + 8
        surface.blit(text_surface, (text_x, text_y))

    def draw(self, surface, font=None):
        """Draw NPC on screen"""
        # Draw NPC sprite
        if self.facing_left:
            flipped_image = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_image, self.rect)
        else:
            surface.blit(self.image, self.rect)
        
        # Draw speech bubble if needed
        if font:
            self.draw_speech_bubble(surface, font)