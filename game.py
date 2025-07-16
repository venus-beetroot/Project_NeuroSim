import pygame
import random
import os
import math
from player import Player
import app
import npc
from camera import Camera
import building 


pygame.init()
pygame.mixer.init()



class Game:
    def __init__(self):
        pygame.init()  # Initialise Pygame

        ## Game window
        screen_width, screen_height = pygame.display.get_desktop_sizes()[0]
        self.screen = pygame.display.set_mode(
            (screen_width, screen_height),
            pygame.NOFRAME
         )
        

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
        map_size = 3000
        self.background = self.create_random_background(
            map_size, map_size, self.assets["floor_tiles"] # Use floor tiles to create a background
        )

        # Record start time in milliseconds
        self.start_ticks = pygame.time.get_ticks()
        
        ## Initialise buildings: one house and one shop
        self.buildings = [
            building.Building(150, 450, "house", self.assets),
            building.Building(800, 450, "shop", self.assets)
        ]


        ## Initialise camera
        self.camera = Camera(app.WIDTH, app.HEIGHT, map_size, map_size)

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
                        if self.chat_cooldown <= 0 and self.message != "":
                            # Store as a tuple to indicate the speaker
                            self.current_npc.chat_history.append(("player", self.message))
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

    def compute_game_time_and_temp(self):
        # Calculate elapsed real minutes
        elapsed_ms = pygame.time.get_ticks() - self.start_ticks
        real_elapsed_minutes = elapsed_ms / 60000
        # Game time advances 10 minutes per real minute
        game_elapsed_minutes = real_elapsed_minutes * 10
        # Calculate full game time in minutes from start (using 24-hour clock)
        full_minutes = (8 * 60 + game_elapsed_minutes) % 1440
        game_hour = int(full_minutes // 60)
        game_minute = int(full_minutes % 60)
        # Prepare 12-hour display
        ampm = "AM" if game_hour < 12 else "PM"
        display_hour = game_hour % 12
        if display_hour == 0:
            display_hour = 12
        time_str = f"{display_hour}:{game_minute:02d} {ampm}"
        # Temperature as a function of game time (sine curve over 24 hours)
        temperature = 70 + 10 * math.sin(2*math.pi*(full_minutes/1440))
        temperature = round(temperature)
        return time_str, temperature
    
    
    def draw_ui(self):
        # Compute game time and temperature
        time_str, temperature = self.compute_game_time_and_temp()
        ui_text = f"Time: {time_str}   Temp: {temperature}°F"
        ui_surf = self.font_small.render(ui_text, True, (255, 255, 255))
        # Position in top-right corner, 10 pixels margin
        pos = (app.WIDTH - ui_surf.get_width() - 10, -10)
        self.screen.blit(ui_surf, pos)


    def update(self):
        ##Ignore player input when interacting with NPCs
        if self.game_state == "playing":
            self.player.handle_input()

        if self.game_state != "settings":
            ##Update player and NPCs
            self.player.update()
            for npc_obj in self.npcs:
                npc_obj.update()

        # Make the camera follow the player when playing
        if self.game_state == "playing":
            self.camera.follow(self.player)

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

         ##Render all game elements to the screen with camera offset.
         # Draw the background using camera offset
        bg_pos = (-self.camera.offset.x, -self.camera.offset.y)
        self.screen.blit(self.background, bg_pos)

        for b in self.buildings:
            b.draw(self.screen, self.camera)
 
         # Draw the player using camera offset (replicating the drawing logic from Player.draw)
        player_draw_rect = self.camera.apply(self.player.rect)
        if self.player.facing_left:
             flipped_image = pygame.transform.flip(self.player.image, True, False)
             self.screen.blit(flipped_image, player_draw_rect)
        else:
             self.screen.blit(self.player.image, player_draw_rect)
 
         # Draw NPCs (assuming similar draw logic applies)
        for npc_obj in self.npcs:
             npc_draw_rect = self.camera.apply(npc_obj.rect)
             # Assuming npc_obj.image exists; adjust if your NPC class differs.
             self.screen.blit(npc_obj.image, npc_draw_rect)
 
        
        ## Display overlay for chat box and setting pages
        if self.game_state == "interacting":
            self.draw_chat_box()
        elif self.game_state == "settings":
            self.draw_settings()

        # Draw the UI for game time and temperature in the top-right
        self.draw_ui()

        pygame.display.flip()




    def draw_chat_box(self):
        # Draw chat history box
        history_box_width, history_box_height = app.WIDTH - 350, 450
        history_box_x, history_box_y = 175, app.HEIGHT - history_box_height - 170
        pygame.draw.rect(self.screen, (30, 30, 30), 
                        (history_box_x, history_box_y, history_box_width, history_box_height))
        pygame.draw.rect(self.screen, (255, 255, 255), 
                        (history_box_x, history_box_y, history_box_width, history_box_height), 2)

        # Render chat history, using custom styling based on speaker
        if hasattr(self, "current_npc"):
            y_offset = history_box_y + 10
            # Assume chat_history entries are tuples: (speaker, message)
            for entry in self.current_npc.chat_history[-5:]:
                if isinstance(entry, tuple):
                    speaker, message = entry
                else:  # fallback (assume NPC message)
                    speaker, message = "npc", entry

                # Define the bubble area (leaving 50px margins for the sprite boxes)
                bubble_x = history_box_x + 60
                bubble_width = history_box_width - 120

                if speaker == "player":
                    text_color = (0, 0, 255)  # Blue for player
                    # Draw player sprite on right
                    sprite_box = pygame.Rect(history_box_x + history_box_width - 50, y_offset, 40, 40)
                    pygame.draw.rect(self.screen, (200, 200, 200), sprite_box)
                    player_sprite = pygame.transform.scale(self.player.image, (40, 40))
                    self.screen.blit(player_sprite, sprite_box.topleft)
                else:  # NPC
                    text_color = (255, 255, 0)  # Yellow for NPC
                    # Draw NPC sprite on left
                    sprite_box = pygame.Rect(history_box_x + 10, y_offset, 40, 40)
                    pygame.draw.rect(self.screen, (200, 200, 200), sprite_box)
                    npc_sprite = pygame.transform.scale(self.current_npc.image, (40, 40))
                    self.screen.blit(npc_sprite, sprite_box.topleft)

                # Render message text centered in the bubble
                msg_surf = self.font_small.render(message, True, text_color)
                text_x = bubble_x + (bubble_width - msg_surf.get_width()) // 2
                text_y = y_offset + (40 - msg_surf.get_height()) // 2  # align vertically with the sprite
                self.screen.blit(msg_surf, (text_x, text_y))
                y_offset += 50

        # Draw the chat text box for typing a new message
        box_width, box_height = app.WIDTH - 350, 100
        box_x, box_y = 175, app.HEIGHT - box_height - 50
        pygame.draw.rect(self.screen, (50, 50, 50), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)

        # Render the current typed message in blue with the player's sprite on the right
        message_text = self.message if hasattr(self, "message") else ""
        if message_text:
            text_color = (0, 0, 255)
            bubble_x = box_x + 60
            bubble_width = box_width - 120
            msg_surf = self.font_small.render(message_text, True, text_color)
            text_x = bubble_x + (bubble_width - msg_surf.get_width()) // 2
            text_y = box_y + (box_height - msg_surf.get_height()) // 2
            self.screen.blit(msg_surf, (text_x, text_y))
            # Draw player sprite on the right side of the chat box
            sprite_box = pygame.Rect(box_x + box_width - 50, box_y + (box_height - 40) // 2, 40, 40)
            pygame.draw.rect(self.screen, (200,200,200), sprite_box)
            player_sprite = pygame.transform.scale(self.player.image, (40, 40))
            self.screen.blit(player_sprite, sprite_box.topleft)

        # Draw dark overlay
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Draw chat header with interacting NPC's name
        if hasattr(self, "current_npc"):
            npc_name = self.current_npc.name
        else:
            npc_name = "NPC"
        header_text = f"Chat with {npc_name}:"
        header_surf = self.font_large.render(header_text, True, (255, 255, 255))
        header_rect = header_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 400))
        self.screen.blit(header_surf, header_rect)


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