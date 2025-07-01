import pygame
import random
import os
import math
from player import Player
import app
import npc


pygame.init()
pygame.mixer.init()



class Game:
    def __init__(self):
        pygame.init()  # Initialise Pygame

        ## Game window
        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN) #Creating a window for game
        pygame.display.set_caption("PROJECT NEUROSIM") # Setting the title of window to shooter game

        ## Game attributes
        self.clock = pygame.time.Clock() # Create a clock object to control the frame rate
        self.assets = app.load_assets() # Loading the game assets by setting a path to the assets folder

        ## Game fonts
        font_path = os.path.join("assets" ,"PressStart2P.ttf")
        self.font_small = pygame.font.Font(font_path, 18)
        self.font_large = pygame.font.Font(font_path, 32)

        ## Initialise player
        self.player = Player(100, 100, self.assets) # Create a player instance

        ## Initialise NPCs
        self.npcs = [

            npc.NPC(200, 200, self.assets, "Dave"),  # Create an NPC instance named Dave
            npc.NPC(200, 100, self.assets, "Lisa"),  # Create an NPC instance named Lisa
            npc.NPC(200, 300, self.assets, "Tom")  # Create an NPC instance named Tom

        ]  # List of NPCs, can be expanded with more NPCs

        ## Initialise background
        self.background = self.create_random_background(
            app.WIDTH, app.HEIGHT, self.assets["floor_tiles"] # Use floor tiles to create a background
        )

        ## Game state attributes
        self.running = True  # set the game state to running
        self.game_over = False # set the game state of not over
        self.game_state = "playing"  # Set the initial game state to playing
        self.reset_game() # Reset game method

    def reset_game(self):
        self.player = Player(app.WIDTH // 2, app.HEIGHT // 2, self.assets)
        self.game_over = False


    def create_random_background(self, width, height, floor_tiles):
        bg = pygame.Surface((width, height)) # Setting bg object as a surface
        tile_w = floor_tiles[0].get_width() # Set start position of tile (width)
        tile_h = floor_tiles[0].get_height() # Set start position of tile (length)

        for y in range(0, height, tile_h):
            for x in range(0, width, tile_w):
                tile = random.choice(floor_tiles)
                bg.blit(tile, (x, y)) # Use blit to place object on screen

        return bg

    def run(self):
        while self.running:
            self.clock.tick(60) # Set FPS to 60

            self.handle_events() # Process user input form keyboard and mouse
            self.update() # Looks for update for position after each frame
            self.draw() # Render updated visuals to the screen
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            ## Old code from canvas :skull:
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

                ## When interacting, capture text input
                elif self.game_state == "interacting":
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = "playing"
                        self.message = ""  # clear message input if ESC pressed
                        if hasattr(self, "current_npc"):
                            del self.current_npc
                    elif event.key == pygame.K_RETURN:
                        # Finalise the message input
                        self.message = self.message  # stored message in self.message

                        ## DEBUG print statement to show the message ##
                        #print(self.message)

                        self.message = ""  # clear after sending
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        self.message = self.message[:-1] if self.message else "" # remove last character when delete is pressed
                    else:
                        # Append any printable character to message
                        if event.unicode and event.unicode.isprintable():
                            if not hasattr(self, "message"):
                                self.message = ""
                            self.message += event.unicode

                ## Normal game input when playing
                elif event.key == pygame.K_RETURN and self.game_state == "playing":
                    # Check collision between player and any NPC
                    for npc_obj in self.npcs:
                        if self.player.rect.colliderect(npc_obj.rect):
                            self.game_state = "interacting"
                            self.current_npc = npc_obj  # store the interacting NPC
                            self.message = ""  # initialise message string
                            break
                        

    def update(self):
        ##Ignore player input when interacting with NPCs
        if self.game_state == "playing":
            self.player.handle_input()

        ##Update player and NPCs
        self.player.update()
        for npc_obj in self.npcs:
            npc_obj.update()



    def draw(self):
        ##Render all game elements to the screen.
        self.screen.blit(self.background, (0, 0))  # update the screen to position 0,0

        self.player.draw(self.screen)

        for npc_obj in self.npcs: # For each npc in the list
            npc_obj.draw(self.screen)  # Draw every NPC in the list
        
        if self.game_state == "interacting":
            self.draw_chat_box()

        pygame.display.flip()


    def draw_chat_box(self):
        # Dark overlay
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Chat header displaying the interacting NPC's name
        if hasattr(self, "current_npc"):
            npc_name = self.current_npc.name
        else:
            npc_name = "NPC"
        header_text = f"Chat with {npc_name}:"
        header_surf = self.font_large.render(header_text, True, (255, 0, 0))
        header_rect = header_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 100))
        self.screen.blit(header_surf, header_rect)

        # Chat text box background
        box_width, box_height = app.WIDTH - 200, 100
        box_x, box_y = 100, app.HEIGHT - box_height - 50
        pygame.draw.rect(self.screen, (50, 50, 50), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)

        # Display typed message inside the chat box
        message_text = self.message if hasattr(self, "message") else ""
        msg_surf = self.font_small.render(message_text, True, (255, 255, 255))
        msg_rect = msg_surf.get_rect(topleft=(box_x + 10, box_y + 10))
        self.screen.blit(msg_surf, msg_rect)