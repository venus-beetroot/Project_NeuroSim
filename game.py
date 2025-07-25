import pygame
import random
import os
import math
from player import Player
import app
import npc
from camera import Camera
import building 
from ai import get_ai_response


pygame.init()
pygame.mixer.init()



class Game:
    def __init__(self):
        pygame.init()  # Initialise Pygame

        ## Game window
        screen_width, screen_height = pygame.display.get_desktop_sizes()[0]
        self.screen = pygame.display.set_mode(
            (screen_width, screen_height),
            pygame.FULLSCREEN
         )
        

        pygame.display.set_caption("PROJECT NEUROSIM") # Setting the title of window to shooter game
        ## Game attributes
        self.clock = pygame.time.Clock() # Create a clock object to control the frame rate
        self.assets = app.load_assets() # Loading the game assets by setting a path to the assets folder
        ## Game fonts
        font_path = os.path.join("assets" ,"PressStart2P.ttf")
        self.font_small = pygame.font.Font(font_path, 18)
        self.font_large = pygame.font.Font(font_path, 32)
        self.font_chat = pygame.font.Font(font_path, 14)
        self.chat_scroll_offset = 0  # Initial scroll offset in chat history
        # Initialize NPC typing variables:
        self.npc_letter_timer = None
        self.npc_response_start_time = None
        self.npc_typing_active = False
        self.npc_current_response = ""
        self.npc_dialogue_index = 0


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

            elif event.type == pygame.MOUSEWHEEL:
                # Only scroll if chat box is visible (when interacting)
                if self.game_state == "interacting" and hasattr(self, "current_npc"):
                    # Adjust scroll offset (mouse wheel up gives y positive)
                    self.chat_scroll_offset -= event.y  
                    if self.chat_scroll_offset < 0:
                        self.chat_scroll_offset = 0

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
                    current_time = pygame.time.get_ticks()
                    # Clear input block if expired
                    if hasattr(self, "input_block_time") and self.input_block_time is not None and current_time >= self.input_block_time:
                        self.input_block_time = None
                    # If NPC is typing or input block is active, ignore keys (except ESC)
                    if ((hasattr(self, "npc_typing_active") and self.npc_typing_active) or 
                        (hasattr(self, "input_block_time") and self.input_block_time is not None and current_time < self.input_block_time)):
                        if event.key != pygame.K_ESCAPE:
                            continue

                    if event.key == pygame.K_ESCAPE: # Exit interaction with ESC
                        self.game_state = "playing"
                        self.message = "" # Delete message when exiting interaction
                        if hasattr(self, "current_npc"):
                            del self.current_npc # Remove current NPC from interaction
                    elif event.key == pygame.K_RETURN:
                        # Start cooldown and process the player's message
                        if self.chat_cooldown <= 0 and self.message != "":
                            # Append player's message to the chat history
                            self.current_npc.chat_history.append(("player", self.message))
                            self.final_message = self.message  # Store final message
                            self.chat_cooldown = self.cooldown_duration
                            # Build a prompt from the NPC's personality and chat history including the new message
                            prompt = self.build_prompt(self.current_npc, self.message)
                            ai_response = get_ai_response(prompt)
                            # Convert AI response to a text string (depending on API response structure)
                            response_text = ai_response.content if hasattr(ai_response, "content") else str(ai_response)
                            # Assign the AI response as NPC's new dialogue
                            self.current_npc.dialogue = response_text
                            self.message = ""  # Reset player's message
                            # Set delay for NPC letter-by-letter typing of the AI response
                            self.npc_response_start_time = pygame.time.get_ticks() + 2000
                            self.npc_typing_active = True
                            self.npc_current_response = ""
                            self.npc_dialogue_index = 0
                            self.npc_live_message = ""

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
        pos = (app.WIDTH - ui_surf.get_width() - 10, 10)
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

        # Decrement chat cooldown timer if active in "interacting" state
        if self.game_state == "interacting" and self.chat_cooldown > 0:
            self.chat_cooldown -= self.clock.get_time()
            if self.chat_cooldown < 0:
                self.chat_cooldown = 0

        if self.game_state == "interacting" and self.npc_typing_active:
            current_time = pygame.time.get_ticks()
            if current_time >= self.npc_response_start_time:
                if self.npc_letter_timer is None:
                    self.npc_letter_timer = current_time + 30
                if current_time >= self.npc_letter_timer:
                    dialogue = self.current_npc.dialogue
                    dialogue_text = dialogue.content if hasattr(dialogue, "content") else str(dialogue)
                    if self.npc_dialogue_index < len(dialogue_text):
                        letter = dialogue_text[self.npc_dialogue_index]
                        self.npc_current_response += letter
                        self.npc_dialogue_index += 1
                        self.npc_live_message = self.npc_current_response
                        base_delay = 30
                        extra_delay = 0
                        if letter in [",", ";"]:
                            extra_delay = 100
                        elif letter in [".", "!", "?"]:
                            extra_delay = 150
                        self.npc_letter_timer = current_time + base_delay + extra_delay
                    else:
                        # Finished typing; append the full text to chat history, clear live message, and block input briefly
                        self.npc_typing_active = False
                        self.current_npc.chat_history.append(("npc", self.npc_current_response))
                        self.npc_current_response = ""
                        self.npc_dialogue_index = 0
                        self.npc_letter_timer = None
                        self.npc_response_start_time = None
                        self.npc_live_message = ""
                        self.input_block_time = current_time + 500




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


    def wrap_text(self, text, font, max_width):
       words = text.split()
       lines = []
       current_line = ""
       for word in words:
           test_line = current_line + (" " if current_line != "" else "") + word
           if font.size(test_line)[0] <= max_width:
               current_line = test_line
           else:
               if current_line:
                   lines.append(current_line)
               current_line = word
       if current_line:
           lines.append(current_line)
       return lines


    def draw_chat_box(self):
        # Chat history box dimensions
        history_box_width, history_box_height = app.WIDTH - 350, 450
        history_box_x, history_box_y = 175, app.HEIGHT - history_box_height - 170
        pygame.draw.rect(self.screen, (30, 30, 30), 
                         (history_box_x, history_box_y, history_box_width, history_box_height))
        pygame.draw.rect(self.screen, (255, 255, 255), 
                         (history_box_x, history_box_y, history_box_width, history_box_height), 2)

        # Define the area for text (leave horizontal margins for sprites and scrollbar)
        text_margin_left = 60
        text_margin_right = 20  # leaving room for scrollbar
        bubble_width = history_box_width - text_margin_left - text_margin_right

        # Build a flat list of wrapped lines from the entire chat history.
        all_lines = []  # Each element: (speaker, line_text, is_first_line)
        if hasattr(self, "current_npc"):
            for entry in self.current_npc.chat_history:
                if isinstance(entry, tuple):
                    speaker, message = entry
                else:
                    speaker, message = "npc", entry
                wrapped = self.wrap_text(message, self.font_chat, bubble_width)
                for idx, line in enumerate(wrapped):
                    all_lines.append((speaker, line, idx == 0))

        # Determine visible area for text
        top_padding = 10
        bottom_padding = 10
        available_height = history_box_height - top_padding - bottom_padding
        line_spacing = 5  # extra spacing between lines
        line_height = self.font_chat.get_height() + line_spacing
        visible_lines = available_height // line_height

        # Clamp the scroll offset to maximum possible value
        total_lines = len(all_lines)
        max_offset = max(0, total_lines - visible_lines)
        if self.chat_scroll_offset > max_offset:
            self.chat_scroll_offset = max_offset

        # Draw the visible portion of the chat history.
        y_offset = history_box_y + top_padding
        for line in all_lines[self.chat_scroll_offset : self.chat_scroll_offset + visible_lines]:
            speaker, line_text, is_first = line
            text_color = (0, 0, 255) if speaker == "player" else (255, 255, 0)
            # Center each line within the bubble defined by text_margin_left and text_margin_right.
            bubble_x = history_box_x + text_margin_left
            text_x = bubble_x + (bubble_width - self.font_chat.size(line_text)[0]) // 2
            line_surf = self.font_chat.render(line_text, True, text_color)
            self.screen.blit(line_surf, (text_x, y_offset))
            # Also draw the sprite for the first line of each message.
            if is_first and line_text.strip() != "":
                if speaker == "player":
                    sprite_box = pygame.Rect(history_box_x + history_box_width - 60, y_offset, 40, 50)
                    player_sprite = pygame.transform.flip(pygame.transform.scale(self.player.image, (40, 50)), True, False)
                    self.screen.blit(player_sprite, sprite_box.topleft)
                elif speaker == "npc":
                    sprite_box = pygame.Rect(history_box_x + 10, y_offset, 40, 50)
                    npc_sprite = pygame.transform.scale(self.current_npc.image, (40, 50))
                    self.screen.blit(npc_sprite, sprite_box.topleft)
            y_offset += line_height

        if hasattr(self, "npc_live_message") and self.npc_live_message != "":
            live_text = self.npc_live_message
            live_color = (255, 255, 0)  # NPC text color
            # Use the same bubble settings as chat history
            bubble_x = history_box_x + text_margin_left
            live_lines = self.wrap_text(live_text, self.font_chat, bubble_width)
            # Start drawing below the last history line (current y_offset)
            live_y = y_offset
            for line in live_lines:
                text_x = bubble_x + (bubble_width - self.font_chat.size(line)[0]) // 2
                line_surf = self.font_chat.render(line, True, live_color)
                self.screen.blit(line_surf, (text_x, live_y))
                live_y += self.font_chat.get_height() + 5  # add extra spacing between lines
            # Advance overall y_offset to account for live message height
            y_offset = live_y

        # Draw the scrollbar on the right side of the chat box.
        if total_lines > visible_lines:
            bar_x = history_box_x + history_box_width - 10
            bar_y = history_box_y + top_padding
            bar_width = 8
            bar_height = available_height
            # Draw background track
            pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
            # Compute thumb size (at least 20 pixels high)
            thumb_height = max(20, bar_height * visible_lines // total_lines)
            # Compute thumb position proportional to scroll offset
            thumb_y = bar_y + (bar_height - thumb_height) * self.chat_scroll_offset // max(1, total_lines - visible_lines)
            pygame.draw.rect(self.screen, (200, 200, 200), (bar_x, thumb_y, bar_width, thumb_height))


        # Draw the chat text box for typing a new message.
        box_width, box_height = app.WIDTH - 350, 100
        box_x, box_y = 175, app.HEIGHT - box_height - 50
        pygame.draw.rect(self.screen, (50, 50, 50), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)

        # Render the current typed message in blue.
        message_text = self.message if hasattr(self, "message") else ""
        if message_text:
            text_color = (0, 0, 255)
            bubble_x = box_x + 60
            bubble_width = box_width - 120
            msg_surf = self.font_small.render(message_text, True, text_color)
            text_x = bubble_x + (bubble_width - msg_surf.get_width()) // 2
            text_y = box_y + (box_height - msg_surf.get_height()) // 2
            self.screen.blit(msg_surf, (text_x, text_y))

        # Draw dark overlay over chat (if needed)
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Draw chat header with interacting NPC's name.
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

    def build_prompt(self, npc, new_message):
        prompt = f"You are {npc.name}. "
        prompt += f"Your personality: {npc.dialogue}\n"
        prompt += "Conversation history:\n"
        for speaker, message in npc.chat_history:
            prompt += f"{speaker.capitalize()}: {message}\n"
        prompt += f"Player: {new_message}\n"
        prompt += f"{npc.name}:"
        return prompt