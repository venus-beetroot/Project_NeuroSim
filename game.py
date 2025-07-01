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

        ## Chat cooldown attributes
        self.cooldown_duration = 3000  # milliseconds
        self.chat_cooldown = 0         # current cooldown timer
        self.final_message = ""        # temporary storage for the sent message

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

            elif event.type == pygame.KEYDOWN:

                #### "Playing" state key events ####
                if self.game_state == "playing":
                    # Enter settings state with ESC
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = "settings"
                    # Click return for interaction
                    elif event.key == pygame.K_RETURN:
                    # Check collision between player and any NPC
                        for npc_obj in self.npcs:
                            if self.player.rect.colliderect(npc_obj.rect):
                                self.game_state = "interacting"
                                self.current_npc = npc_obj  # store the interacting NPC
                                self.message = ""  # initialise message string
                                break

                #### "Interacting" state key events ####
                elif self.game_state == "interacting":
                    if event.key == pygame.K_ESCAPE: # Exit interaction with ESC
                        self.game_state = "playing"
                        self.message = "" # Delete message when exiting interaction
                        if hasattr(self, "current_npc"):
                            del self.current_npc # Remove current NPC from interaction
                    elif event.key == pygame.K_RETURN:
                        # Start cooldown and store the message
                        if self.chat_cooldown <= 0:
                            self.current_npc.chat_history.append(self.message)
                            self.final_message = self.message # Store the final message
                        ####DEBUGGING PRINT####
                        ##print(self.message)##
                        ####DEBUGGING PRINT####
                            self.chat_cooldown = self.cooldown_duration
                            self.message = "" # Reset message after sending

                    ##Delete last character with backspace or delete
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        self.message = self.message[:-1] if self.message else ""
                    else:
                        if event.unicode and event.unicode.isprintable():
                            if not hasattr(self, "message"):
                                self.message = ""
                            self.message += event.unicode

                #### "Settings" state key events ####
                elif self.game_state == "settings":
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = "playing"
            
            ####Mous interactions####
            elif event.type == pygame.MOUSEBUTTONDOWN:

                #### "Setting" state key events ####
                if self.game_state == "settings":
                    mx, my = event.pos
                    # Return button rect
                    return_rect = pygame.Rect(app.WIDTH//2 - 150, app.HEIGHT//2 - 50, 300, 50)
                    # Quit button rect
                    quit_rect = pygame.Rect(app.WIDTH//2 - 150, app.HEIGHT//2 + 10, 300, 50)
                    if return_rect.collidepoint(mx, my):
                        self.game_state = "playing"
                    elif quit_rect.collidepoint(mx, my):
                        pygame.quit()
                        exit()  

    def update(self):
        ##Ignore player input when interacting with NPCs
        if self.game_state == "playing":
            self.player.handle_input()

        if self.game_state != "settings":
            ##Update player and NPCs
            self.player.update()
            for npc_obj in self.npcs:
                npc_obj.update()

        # Process chat cooldown during interacting state
        if self.game_state == "interacting" and self.chat_cooldown > 0:
            self.chat_cooldown -= self.clock.get_time()
            if self.chat_cooldown <= 0:
                self.chat_cooldown = 0
                self.final_message = ""
                # After cooldown, save the sent message to the current NPC's chat history
                if hasattr(self, "current_npc"):
                    self.current_npc.chat_history.append(self.final_message)
                    self.final_message = ""



    def draw(self):
        ##Render all game elements to the screen.
        self.screen.blit(self.background, (0, 0))  # update the screen to position 0,0
        self.player.draw(self.screen)
        for npc_obj in self.npcs: # For each npc in the list
            npc_obj.draw(self.screen)  # Draw every NPC in the list
        
        ## Display overlay for chat box and setting pages
        if self.game_state == "interacting":
            self.draw_chat_box()
        elif self.game_state == "settings":
            self.draw_settings()

        pygame.display.flip()


    def draw_chat_box(self):

        ## Draw chat history box for the current NPC
        history_box_width, history_box_height = app.WIDTH - 350, 450
        history_box_x, history_box_y = 175, app.HEIGHT - history_box_height - 170

        pygame.draw.rect(self.screen, (30, 30, 30), 
                         (history_box_x, history_box_y, history_box_width, history_box_height))
        pygame.draw.rect(self.screen, (255, 255, 255), 
                         (history_box_x, history_box_y, history_box_width, history_box_height), 2)

        ## Render the individual chat history from the current NPC
        if hasattr(self, "current_npc"):
            y_offset = history_box_y + 10
            for message in self.current_npc.chat_history[-5:]:
                msg_surf = self.font_small.render(message, True, (255, 255, 255))
                self.screen.blit(msg_surf, (history_box_x + 10, y_offset))
                y_offset += 25

        ## Dark overlay
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        ## Chat header displaying the interacting NPC's name
        if hasattr(self, "current_npc"):
            npc_name = self.current_npc.name
        else:
            npc_name = "NPC"
        header_text = f"Chat with {npc_name}:"
        header_surf = self.font_large.render(header_text, True, (255, 255, 255))
        header_rect = header_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 400))
        self.screen.blit(header_surf, header_rect)

        ## Chat text box background
        box_width, box_height = app.WIDTH - 350, 100
        box_x, box_y = 175, app.HEIGHT - box_height - 50
        pygame.draw.rect(self.screen, (50, 50, 50), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)

        ## Display typed message inside the chat box
        message_text = self.message if hasattr(self, "message") else ""
        msg_surf = self.font_small.render(message_text, True, (255, 255, 255))
        msg_rect = msg_surf.get_rect(topleft=(box_x + 10, box_y + 10))
        self.screen.blit(msg_surf, msg_rect)

        ## If in cooldown, draw a progress bar above the chat history box
        if self.chat_cooldown > 0:
            cooldown_bar_width = history_box_width
            fill_width = int(cooldown_bar_width * (1 - self.chat_cooldown / self.cooldown_duration))
            cooldown_bar_rect = pygame.Rect(history_box_x, history_box_y - 30, cooldown_bar_width, 20)
            pygame.draw.rect(self.screen, (100, 100, 100), cooldown_bar_rect)
            pygame.draw.rect(self.screen, (0, 255, 0),
                            (history_box_x, history_box_y - 30, fill_width, 20))


    def draw_settings(self):
        # Dark overlay covering full screen
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_large.render("Settings", True, (255,255,255))
        title_rect = title_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 150))
        self.screen.blit(title_surf, title_rect)

        # Draw Return button
        return_rect = pygame.Rect(app.WIDTH//2 - 150, app.HEIGHT//2 - 50, 300, 50)
        pygame.draw.rect(self.screen, (70, 70, 70), return_rect)
        pygame.draw.rect(self.screen, (255,255,255), return_rect, 2)
        return_text = self.font_small.render("Return to Playing", True, (255,255,255))
        return_text_rect = return_text.get_rect(center=return_rect.center)
        self.screen.blit(return_text, return_text_rect)

        # Draw Quit button
        quit_rect = pygame.Rect(app.WIDTH//2 - 150, app.HEIGHT//2 + 10, 300, 50)
        pygame.draw.rect(self.screen, (70, 70, 70), quit_rect)
        pygame.draw.rect(self.screen, (255,255,255), quit_rect, 2)
        quit_text = self.font_small.render("Quit Game", True, (255,255,255))
        quit_text_rect = quit_text.get_rect(center=quit_rect.center)
        self.screen.blit(quit_text, quit_text_rect)