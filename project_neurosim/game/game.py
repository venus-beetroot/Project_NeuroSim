"""
Main game class and game loop
"""
"""
Main game class and game loop
"""
import pygame
import random
import os
from typing import Optional
import math

# Import all the components
from functions.assets import app
from functions.core.player import Player
from functions.core import npc
from functions.core.camera import Camera
from functions.core.building import Building
from functions.assets.ai import get_ai_response
from utils.ui_utils import draw_text_box, draw_centered_text_box

# Import managers and UI components
from managers.chat_manager import ChatManager
from managers.ui_manager import UIManager
from ui.start_screen import StartScreen
from ui.chat_renderer import ChatRenderer
from game.states import GameState
from functions.core.building import Building, BuildingManager

class Game:
    """Main game class that manages the game loop and state"""
    
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self._init_display()
        self._init_fonts()
        
        # Initialize start screen AFTER display and fonts are ready
        self.start_screen = StartScreen(self.screen, self.font_large, self.font_small)
        
        self._init_game_objects()
        self._init_managers()
        self._init_game_state()
        self._init_camera()
        self._init_building()
        self._init_arrow_system()
        
        
    
    def _init_display(self):
        """Initialize the game display"""
        screen_width, screen_height = pygame.display.get_desktop_sizes()[0]
        self.screen = pygame.display.set_mode(
            (screen_width, screen_height), pygame.FULLSCREEN
        )
        pygame.display.set_caption("PROJECT NEUROSIM")
        self.clock = pygame.time.Clock()

    def _init_arrow_system(self):
            """Initialize the building arrow system"""
            self.arrow_system = BuildingArrowSystem(self.font_small, self.font_chat, self.font_smallest)
    
    def _init_fonts(self):
        """Initialize game fonts"""
        font_path = os.path.join("assets", "PressStart2P.ttf")
        self.font_small = pygame.font.Font(font_path, 18)
        self.font_large = pygame.font.Font(font_path, 32)
        self.font_chat = pygame.font.Font(font_path, 14)
        self.font_smallest = pygame.font.Font(font_path, 12)
    
    def _init_game_objects(self):
        """Initialize game objects (player, NPCs, buildings, etc.)"""
        self.assets = app.load_assets()
        
        # Map configuration
        self.map_size = 3000
        map_center_x = self.map_size // 2
        map_center_y = self.map_size // 2
        
        # Spawn player at the center of the map (with NPCs)
        self.player = Player(map_center_x, map_center_y, self.assets)
        
        # Define hangout area at the center of the map - make it larger to include buildings
        center_hangout_area = {
            'x': map_center_x - 200,  # Expanded to 400x400 pixel area around center
            'y': map_center_y - 200,
            'width': 400,
            'height': 400
        }
        
        # Create NPCs with center hangout area - spread them around the player
        self.npcs = [
            npc.NPC(map_center_x - 80, map_center_y - 80, self.assets, "Dave", center_hangout_area),
            npc.NPC(map_center_x + 80, map_center_y - 80, self.assets, "Lisa", center_hangout_area),
            npc.NPC(map_center_x, map_center_y + 100, self.assets, "Tom", center_hangout_area)
        ]
        
        # Create background
        self.background = self._create_random_background(self.map_size, self.map_size)
    
    def _init_managers(self):
        """Initialize manager classes"""
        self.chat_manager = ChatManager(self.font_chat, self.font_small)
        self.ui_manager = UIManager(self.screen, self.font_small, self.font_large, self.font_chat)
        self.chat_renderer = ChatRenderer(self.ui_manager)
    
    def _init_game_state(self):
        """Initialize game state variables"""
        self.running = True
        self.game_over = False
        self.game_state = GameState.START_SCREEN
        self.current_npc = None
        self.start_ticks = pygame.time.get_ticks()
    
    def _init_camera(self):
        """Initialize camera with smooth following"""
        self.camera = Camera(app.WIDTH, app.HEIGHT, self.map_size, self.map_size)
        
        # Optional: Enable smooth camera following
        self.camera.smooth_follow = True
        self.camera.smoothing = 0.05  # Adjust for desired smoothness
    
    def _init_building(self):
        """Initialize buildings with hitboxes and interior system - moved to town center"""
        map_center_x = self.map_size // 2
        map_center_y = self.map_size // 2
        
        # Create buildings near the town center where NPCs hang out
        self.buildings = [
            Building(map_center_x - 150, map_center_y + 150, "house", self.assets),  # House to the left
            Building(map_center_x + 50, map_center_y + 150, "shop", self.assets)    # Shop to the right
        ]
        
        # Initialize building manager for interior/exterior transitions
        self.building_manager = BuildingManager(self.buildings)
        
        # Debug mode to see hitboxes
        self.debug_hitboxes = False  # Set to True to see hitbox outlines
    
    def _create_random_background(self, width: int, height: int) -> pygame.Surface:
        """Create a random background using floor tiles"""
        bg = pygame.Surface((width, height))
        floor_tiles = self.assets["floor_tiles"]
        tile_w, tile_h = floor_tiles[0].get_size()
        
        for y in range(0, height, tile_h):
            for x in range(0, width, tile_w):
                tile = random.choice(floor_tiles)
                bg.blit(tile, (x, y))
        
        return bg
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.clock.tick(60)
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
    
    def handle_events(self):
        """Handle all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mouse_wheel(event)
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event)
    
    def _handle_mouse_wheel(self, event):
        """Handle mouse wheel scrolling in chat"""
        if self.game_state == GameState.INTERACTING and self.current_npc:
            # ChatManager will handle the scroll logic
            pass
    
    def _handle_keydown(self, event):
        """Handle keyboard input based on current game state"""
        if self.game_state == GameState.START_SCREEN:
            if event.key == pygame.K_RETURN:
                self.game_state = GameState.PLAYING
            elif event.key == pygame.K_ESCAPE:
                self.running = False
        elif self.game_state == GameState.PLAYING:
            self._handle_playing_keys(event)
        elif self.game_state == GameState.INTERACTING:
            self._handle_interaction_keys(event)
        elif self.game_state == GameState.SETTINGS:
            self._handle_settings_keys(event)
    
    def _handle_playing_keys(self, event):
        """Handle keys during playing state"""
        if event.key == pygame.K_ESCAPE:
            self.game_state = GameState.SETTINGS
        elif event.key == pygame.K_RETURN:
            self._try_interact_with_npc()
        elif event.key == pygame.K_F1:  # Added: Toggle debug hitboxes
            self.toggle_debug_hitboxes()
        elif event.key == pygame.K_e:  # Added: Handle building entry/exit
            self._handle_building_interaction()
    
    def _handle_interaction_keys(self, event):
        """Handle keys during interaction state"""
        current_time = pygame.time.get_ticks()
        
        # Check if input is blocked
        if (self.chat_manager.typing_active or 
            (self.chat_manager.input_block_time and current_time < self.chat_manager.input_block_time)):
            if event.key != pygame.K_ESCAPE:
                return
        
        if event.key == pygame.K_ESCAPE:
            self._exit_interaction()
        elif event.key == pygame.K_RETURN:
            self._send_chat_message()
        elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
            self.chat_manager.message = self.chat_manager.message[:-1]
        elif event.unicode and event.unicode.isprintable():
            self.chat_manager.message += event.unicode
    
    def _handle_settings_keys(self, event):
        """Handle keys during settings state"""
        if event.key == pygame.K_ESCAPE:
            self.game_state = GameState.PLAYING
    
    def _handle_mouse_click(self, event):
        """Handle mouse clicks"""
        if self.game_state == GameState.START_SCREEN:
            button_clicked = self.start_screen.handle_click(event.pos)
            if button_clicked == "start":
                self.game_state = GameState.PLAYING
            elif button_clicked == "settings":
                self.game_state = GameState.SETTINGS
            elif button_clicked == "quit":
                self.running = False
                
        elif self.game_state == GameState.SETTINGS:
            mx, my = event.pos
            return_rect = pygame.Rect(app.WIDTH//2 - 150, app.HEIGHT//2 - 50, 300, 50)
            quit_rect = pygame.Rect(app.WIDTH//2 - 150, app.HEIGHT//2 + 10, 300, 50)
            
            if return_rect.collidepoint(mx, my):
                # Return to start screen instead of playing
                self.game_state = GameState.START_SCREEN
            elif quit_rect.collidepoint(mx, my):
                self.running = False

    def _handle_start_screen_action(self, action):
        """Handle completed start screen actions after loading"""
        if action == "start":
            self.game_state = GameState.PLAYING
        elif action == "settings":
            self.game_state = GameState.SETTINGS
        elif action == "quit":
            self.running = False
    
    def _handle_building_interaction(self):
        """Handle E key press for building entry/exit"""
        if self.building_manager.is_inside_building():
            # Inside building - try to exit
            if self.building_manager.check_building_exit(self.player.rect):
                # Debug: Print player position before exit
                print(f"Before exit - Player pos: ({self.player.rect.centerx}, {self.player.rect.centery})")
                print(f"Before exit - Player x,y: ({self.player.x}, {self.player.y})")
                
                success = self.building_manager.exit_building(self.player)
                if success:
                    # Ensure position is synchronized after exit
                    self.player.sync_position()
                    
                    # Reset camera to follow player again
                    self.camera.follow(self.player)
                    
                    # Debug: Print player position after exit
                    print(f"After exit - Player pos: ({self.player.rect.centerx}, {self.player.rect.centery})")
                    print(f"After exit - Player x,y: ({self.player.x}, {self.player.y})")
                    
                    print("Exited building")
        else:
            # Outside - try to enter building
            building = self.building_manager.check_building_entry(self.player.rect)
            if building:
                # Debug: Print player position before entry
                print(f"Before entry - Player pos: ({self.player.rect.centerx}, {self.player.rect.centery})")
                print(f"Before entry - Player x,y: ({self.player.x}, {self.player.y})")
                
                success = self.building_manager.enter_building(building, self.player)
                if success:
                    # Ensure position is synchronized after entry
                    self.player.sync_position()
                    
                    # Debug: Print player position after entry
                    print(f"After entry - Player pos: ({self.player.rect.centerx}, {self.player.rect.centery})")
                    print(f"After entry - Player x,y: ({self.player.x}, {self.player.y})")
                    
                    print(f"Entered {building.building_type}")

    def check_building_interactions(self):
        """Check building interactions for entry/exit"""
        if self.building_manager.is_inside_building():
            # Inside building - check for exit using interior coordinates
            if self.building_manager.check_building_exit(self.player.rect):
                # Show "Press E to exit" message at bottom center of screen
                message_y = self.screen.get_height() - 60
                self.draw_centered_text_box("Press E to exit", message_y)
        else:
            # Outside - check for building entry
            building = self.building_manager.check_building_entry(self.player.rect)
            if building:
                # Show "Press E to enter" message at bottom center of screen
                message_y = self.screen.get_height() - 60
                self.draw_centered_text_box("Press E to enter", message_y)
                
    def get_interior_screen_position(self, interior_x, interior_y):
        """Convert interior coordinates to screen coordinates when centered"""
        if not self.building_manager.is_inside_building():
            return interior_x, interior_y
        
        current_interior = self.building_manager.get_current_interior()
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        offset_x, offset_y = current_interior.get_interior_offset(screen_width, screen_height)
        
        return interior_x + offset_x, interior_y + offset_y


    def _try_interact_with_npc(self):
        """Try to interact with nearby NPCs"""
        for npc_obj in self.npcs:
            # Check if player is close enough to NPC (using distance calculation)
            distance = ((self.player.rect.centerx - npc_obj.rect.centerx) ** 2 + 
                       (self.player.rect.centery - npc_obj.rect.centery) ** 2) ** 0.5
            
            if distance <= 60:  # Interaction range
                self.game_state = GameState.INTERACTING
                self.current_npc = npc_obj
                self.chat_manager.message = ""
                break
    
    def _exit_interaction(self):
        """Exit NPC interaction"""
        self.game_state = GameState.PLAYING
        self.chat_manager.message = ""
        self.current_npc = None

    def debug_player_position(self, context=""):
        """Debug method to check if player position is synchronized"""
        rect_pos = (self.player.rect.centerx, self.player.rect.centery)
        xy_pos = (self.player.x, self.player.y)
        
        if rect_pos != xy_pos:
            print(f"DESYNC DETECTED {context}: rect=({rect_pos}), x,y=({xy_pos})")
        else:
            print(f"Position OK {context}: ({rect_pos})")
    
    def _send_chat_message(self):
        """Send a chat message to the current NPC"""
        if not self.current_npc or not self.chat_manager.can_send_message():
            return
        
        sent_message = self.chat_manager.send_message(self.current_npc)
        if sent_message:
            # Get AI response
            prompt = self._build_ai_prompt(self.current_npc, sent_message)
            ai_response = get_ai_response(prompt)
            response_text = ai_response.content if hasattr(ai_response, "content") else str(ai_response)
            
            # Set up NPC response
            self.current_npc.dialogue = response_text
            self.chat_manager.start_typing_animation(response_text)
    
    def _build_ai_prompt(self, npc_obj, new_message: str) -> str:
        """Build AI prompt for NPC response"""
        prompt = f"You are {npc_obj.name}. "
        prompt += f"Your personality: {npc_obj.dialogue}\n"
        prompt += "Conversation history:\n"
        
        for speaker, message in npc_obj.chat_history:
            prompt += f"{speaker.capitalize()}: {message}\n"
        
        prompt += f"Player: {new_message}\n"
        prompt += f"{npc_obj.name}:"
        return prompt
    
    def update(self):
        """Update all game objects"""
        if self.game_state == GameState.START_SCREEN:
            mouse_pos = pygame.mouse.get_pos()
            finished_action = self.start_screen.update(mouse_pos)
            if finished_action:
                self._handle_start_screen_action(finished_action)
            return
        
        # Only update player input when playing
        if self.game_state == GameState.PLAYING:
            self.player.handle_input()
            
            # Handle camera differently based on interior/exterior
            if self.building_manager.is_inside_building():
                # Inside building - don't follow with camera, keep it centered
                pass  # Camera stays static for interior
            else:
                # Outside - follow player normally
                self.camera.follow(self.player)
        
        # Update game objects (except during settings)
        if self.game_state != GameState.SETTINGS:
            # Get collision objects based on current location
            if self.building_manager.is_inside_building():
                # Inside building - use interior walls for collision
                collision_objects = self.building_manager.get_interior_collision_walls()
            else:
                # Outside - use buildings for collision
                collision_objects = self.buildings
            
            self.player.update(collision_objects)
            
            # Update NPCs - they can now move between interior and exterior
            for npc_obj in self.npcs:
                npc_obj.update(self.player, self.buildings, self.building_manager)
        
        # Update chat system
        if self.game_state == GameState.INTERACTING and self.current_npc:
            self.chat_manager.update_cooldown(self.clock.get_time())
            
            if self.chat_manager.update_typing_animation(self.current_npc.dialogue):
                self.current_npc.chat_history.append(("npc", self.chat_manager.current_response))
                self.chat_manager.current_response = ""

            
    def toggle_debug_hitboxes(self):
        """Toggle hitbox visualization (useful for debugging)"""
        self.debug_hitboxes = not self.debug_hitboxes
        print(f"Debug hitboxes: {'ON' if self.debug_hitboxes else 'OFF'}")
    
    # Replace the interior drawing section in your game.py draw() method with this:

    def draw(self):
        """Render all game elements"""
        if self.game_state == GameState.START_SCREEN:
            self.start_screen.draw()
            pygame.display.flip()
            return
        
        if self.building_manager.is_inside_building():
            # Draw interior centered on screen
            self.screen.fill((0, 0, 0))  # Clear screen
            
            current_interior = self.building_manager.get_current_interior()
            
            # Get the offset to center the interior
            screen_width = self.screen.get_width()
            screen_height = self.screen.get_height()
            offset_x, offset_y = current_interior.get_interior_offset(screen_width, screen_height)
            
            # Draw the interior (now centered)
            current_interior.draw_interior(self.screen, self.debug_hitboxes)
            
            # Draw player with interior offset applied
            player_draw_x = self.player.rect.x + offset_x
            player_draw_y = self.player.rect.y + offset_y
            player_draw_rect = pygame.Rect(player_draw_x, player_draw_y, 
                                        self.player.rect.width, self.player.rect.height)
            
            if self.player.facing_left:
                flipped_image = pygame.transform.flip(self.player.image, True, False)
                self.screen.blit(flipped_image, player_draw_rect)
            else:
                self.screen.blit(self.player.image, player_draw_rect)
            
            # Draw NPCs that are also inside buildings
            for npc_obj in self.npcs:
                if npc_obj.is_inside_building and npc_obj.current_building == current_interior:
                    # Draw NPC with interior offset applied
                    npc_draw_x = npc_obj.rect.x + offset_x
                    npc_draw_y = npc_obj.rect.y + offset_y
                    npc_draw_rect = pygame.Rect(npc_draw_x, npc_draw_y, 
                                              npc_obj.rect.width, npc_obj.rect.height)
                    
                    if npc_obj.facing_left:
                        flipped_image = pygame.transform.flip(npc_obj.image, True, False)
                        self.screen.blit(flipped_image, npc_draw_rect)
                    else:
                        self.screen.blit(npc_obj.image, npc_draw_rect)
                    
                    # Draw speech bubble if NPC is showing one (adjusted for interior)
                    if npc_obj.show_speech_bubble:
                        self._draw_npc_speech_bubble_interior(npc_obj, npc_draw_rect)
        else:
            # Draw exterior (your existing code)
            # Draw background
            bg_pos = (-self.camera.offset.x, -self.camera.offset.y)
            self.screen.blit(self.background, bg_pos)
            
            # Draw buildings with optional debug hitboxes
            for building in self.buildings:
                building.draw(self.screen, self.camera, self.debug_hitboxes)
            
            # Draw player with camera offset
            player_screen_rect = self.camera.apply(self.player.rect)
            if self.player.facing_left:
                flipped_image = pygame.transform.flip(self.player.image, True, False)
                self.screen.blit(flipped_image, player_screen_rect)
            else:
                self.screen.blit(self.player.image, player_screen_rect)
            
            # Draw NPCs with camera offset and speech bubbles (only those outside)
            for npc_obj in self.npcs:
                if not npc_obj.is_inside_building:
                    npc_screen_rect = self.camera.apply(npc_obj.rect)
                    
                    # Draw NPC sprite
                    if npc_obj.facing_left:
                        flipped_image = pygame.transform.flip(npc_obj.image, True, False)
                        self.screen.blit(flipped_image, npc_screen_rect)
                    else:
                        self.screen.blit(npc_obj.image, npc_screen_rect)
                    
                    # Draw speech bubble if NPC is showing one
                    if npc_obj.show_speech_bubble:
                        self._draw_npc_speech_bubble(npc_obj, npc_screen_rect)
            
            self.arrow_system.draw_building_arrows(self.screen, self.player, self.buildings, self.camera, self.building_manager)
        
        # Draw UI overlays (these work in both interior and exterior)
        if self.game_state == GameState.INTERACTING and self.current_npc:
            self.chat_renderer.draw_chat_interface(self.current_npc, self.chat_manager)
        elif self.game_state == GameState.SETTINGS:
            self.ui_manager.draw_settings_menu()
        
        # Draw game UI (time/temperature)
        self.ui_manager.draw_game_time_ui()
        
        self.arrow_system.draw_compass(self.screen)
        
        pygame.display.flip()
    
    def _draw_npc_speech_bubble(self, npc_obj, screen_rect):
        """Draw speech bubble for NPC at screen position using bubble_dialogue"""
        if not npc_obj.show_speech_bubble:
            return
        
        # Use smaller font for speech bubbles
        bubble_font = self.font_chat  # This is size 14, smaller than font_small (18)
        
        # Use bubble_dialogue instead of dialogue for speech bubbles
        words = npc_obj.bubble_dialogue.split(' ')
        max_width = 300  # Maximum bubble width
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surface = bubble_font.render(test_line, True, (0, 0, 0))
            
            if test_surface.get_width() <= max_width - 20:  # Account for padding
                current_line = test_line
            else:
                if current_line:  # If current line has content, save it
                    lines.append(current_line)
                    current_line = word
                else:  # If single word is too long, just use it anyway
                    current_line = word
        
        if current_line:  # Don't forget the last line
            lines.append(current_line)
        
        # Calculate bubble dimensions based on multiline text
        line_height = bubble_font.get_height()
        text_width = max([bubble_font.render(line, True, (0, 0, 0)).get_width() for line in lines])
        text_height = len(lines) * line_height + (len(lines) - 1) * 2  # 2px spacing between lines
        
        bubble_width = text_width + 20
        bubble_height = text_height + 16
        bubble_x = screen_rect.centerx - bubble_width // 2
        bubble_y = screen_rect.top - bubble_height - 10
        
        # Make sure bubble stays on screen
        bubble_x = max(10, min(bubble_x, self.screen.get_width() - bubble_width - 10))
        bubble_y = max(10, bubble_y)
        
        # Draw bubble background
        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)
        pygame.draw.rect(self.screen, (255, 255, 255), bubble_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), bubble_rect, 2)
        
        # Draw bubble tail (triangle pointing down) - FIXED: Use screen_rect instead of pygame.draw.rect
        tail_points = [
            (screen_rect.centerx - 10, bubble_y + bubble_height),
            (screen_rect.centerx + 10, bubble_y + bubble_height),
            (screen_rect.centerx, bubble_y + bubble_height + 10)
        ]
        pygame.draw.polygon(self.screen, (255, 255, 255), tail_points)
        pygame.draw.polygon(self.screen, (0, 0, 0), tail_points, 2)
        
        # Draw text lines
        text_x = bubble_x + 10
        text_y = bubble_y + 8
        
        for i, line in enumerate(lines):
            line_surface = bubble_font.render(line, True, (0, 0, 0))
            line_y = text_y + i * (line_height + 2)  # 2px spacing between lines
            self.screen.blit(line_surface, (text_x, line_y))

    def _draw_npc_speech_bubble_interior(self, npc_obj, draw_rect):
        """Draw speech bubble for NPC inside buildings (no camera offset needed)"""
        if not npc_obj.show_speech_bubble:
            return
        
        # Use smaller font for speech bubbles
        bubble_font = self.font_chat
        
        # Use bubble_dialogue instead of dialogue for speech bubbles
        words = npc_obj.bubble_dialogue.split(' ')
        max_width = 300  # Maximum bubble width
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surface = bubble_font.render(test_line, True, (0, 0, 0))
            
            if test_surface.get_width() <= max_width - 20:  # Account for padding
                current_line = test_line
            else:
                if current_line:  # If current line has content, save it
                    lines.append(current_line)
                    current_line = word
                else:  # If single word is too long, just use it anyway
                    current_line = word
        
        if current_line:  # Don't forget the last line
            lines.append(current_line)
        
        # Calculate bubble dimensions based on multiline text
        line_height = bubble_font.get_height()
        text_width = max([bubble_font.render(line, True, (0, 0, 0)).get_width() for line in lines])
        text_height = len(lines) * line_height + (len(lines) - 1) * 2  # 2px spacing between lines
        
        bubble_width = text_width + 20
        bubble_height = text_height + 16
        bubble_x = draw_rect.centerx - bubble_width // 2
        bubble_y = draw_rect.top - bubble_height - 10
        
        # Make sure bubble stays on screen
        bubble_x = max(10, min(bubble_x, self.screen.get_width() - bubble_width - 10))
        bubble_y = max(10, bubble_y)
        
        # Draw bubble background
        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)
        pygame.draw.rect(self.screen, (255, 255, 255), bubble_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), bubble_rect, 2)
        
        # Draw bubble tail (triangle pointing down)
        tail_points = [
            (draw_rect.centerx - 10, bubble_y + bubble_height),
            (draw_rect.centerx + 10, bubble_y + bubble_height),
            (draw_rect.centerx, bubble_y + bubble_height + 10)
        ]
        pygame.draw.polygon(self.screen, (255, 255, 255), tail_points)
        pygame.draw.polygon(self.screen, (0, 0, 0), tail_points, 2)
        
        # Draw text lines
        text_x = bubble_x + 10
        text_y = bubble_y + 8
        
        for i, line in enumerate(lines):
            line_surface = bubble_font.render(line, True, (0, 0, 0))
            line_y = text_y + i * (line_height + 2)  # 2px spacing between lines
            self.screen.blit(line_surface, (text_x, line_y))

    def limit_npc_response(self, response_text: str, max_sentences: int = 4) -> str:
        """
        Limit NPC response to a maximum number of sentences
        
        Args:
            response_text: The original AI response
            max_sentences: Maximum number of sentences to keep (default 4)
        
        Returns:
            Truncated response text
        """
        if not response_text.strip():
            return response_text
        
        # Split into sentences using common sentence endings
        import re
        
        # More sophisticated sentence splitting that handles abbreviations better
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', response_text.strip())
        
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Limit to max_sentences
        if len(sentences) <= max_sentences:
            return response_text
        
        # Take first max_sentences and join them back
        limited_sentences = sentences[:max_sentences]
        limited_response = ' '.join(limited_sentences)
        
        # Ensure it ends with proper punctuation
        if limited_response and limited_response[-1] not in '.!?':
            limited_response += '.'
        
        return limited_response

    def _send_chat_message(self):
        """Send a chat message to the current NPC"""
        if not self.current_npc or not self.chat_manager.can_send_message():
            return
        
        # Set waiting state for loading indicator
        if hasattr(self.chat_manager, 'waiting_for_response'):
            self.chat_manager.waiting_for_response = True
        
        sent_message = self.chat_manager.send_message(self.current_npc)
        if sent_message:
            # Get AI response
            prompt = self._build_ai_prompt(self.current_npc, sent_message)
            ai_response = get_ai_response(prompt)
            response_text = ai_response.content if hasattr(ai_response, "content") else str(ai_response)
            
            # Limit response length to 4 sentences max
            limited_response = self.limit_npc_response(response_text)
            
            # Set up NPC response
            self.current_npc.dialogue = limited_response
            self.chat_manager.start_typing_animation(limited_response)
            
            # Clear waiting state
            if hasattr(self.chat_manager, 'waiting_for_response'):
                self.chat_manager.waiting_for_response = False

    def _build_ai_prompt(self, npc_obj, new_message: str) -> str:
        """Build AI prompt for NPC response with length instruction"""
        prompt = f"You are {npc_obj.name}. "
        prompt += f"Your personality: {npc_obj.dialogue}\n"
        prompt += "Keep your responses short and conversational - maximum 4 sentences.\n"
        prompt += "Conversation history:\n"
        
        for speaker, message in npc_obj.chat_history:
            prompt += f"{speaker.capitalize()}: {message}\n"
        
        prompt += f"Player: {new_message}\n"
        prompt += f"{npc_obj.name}:"
        return prompt
    

class BuildingArrowSystem:
    """Manages directional arrows pointing to buildings"""
    
    def __init__(self, font_small, font_chat, font_smallest):
        self.font_small = font_small
        self.font_chat = font_chat
        self.font_smallest = font_smallest
        self.max_distance = 2400  # Maximum distance to show arrows (in pixels)
        self.min_distance = 200   # Minimum distance for edge arrows (reduced from 640)
        self.lock_distance = 640  # Distance at which arrows lock onto buildings
        
        # Building display names
        self.building_names = {
            "house": "Residential House",
            "shop": "General Store"
        }
    
    def calculate_distance(self, pos1, pos2):
        """Calculate distance between two points"""
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
    
    def calculate_angle(self, from_pos, to_pos):
        """Calculate angle from one position to another (in radians)"""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        return math.atan2(dy, dx)
    
    def create_arrow_points(self, center_x, center_y, angle, size):
        """Create arrow points for drawing"""
        # Arrow head points
        head_length = size * 0.8
        head_width = size * 0.5
        
        # Main arrow tip
        tip_x = center_x + math.cos(angle) * head_length
        tip_y = center_y + math.sin(angle) * head_length
        
        # Arrow base corners
        base_angle1 = angle + 2.8  # About 160 degrees
        base_angle2 = angle - 2.8  # About -160 degrees
        
        base1_x = center_x + math.cos(base_angle1) * head_width
        base1_y = center_y + math.sin(base_angle1) * head_width
        
        base2_x = center_x + math.cos(base_angle2) * head_width
        base2_y = center_y + math.sin(base_angle2) * head_width
        
        return [(tip_x, tip_y), (base1_x, base1_y), (base2_x, base2_y)]
    
    def get_screen_edge_position(self, player_screen_pos, building_screen_pos, screen_size, margin=60):
        """Get position for arrow based on where building appears relative to screen"""
        screen_width, screen_height = screen_size
        screen_center_x = screen_width // 2
        screen_center_y = screen_height // 2
        
        # Calculate direction from screen center to building
        dx = building_screen_pos[0] - screen_center_x
        dy = building_screen_pos[1] - screen_center_y
        
        # Normalize direction
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0:
            return None
        
        dx /= length
        dy /= length
        
        # Determine which screen edge to use based on direction
        arrow_x = screen_center_x
        arrow_y = screen_center_y
        
        # Calculate intersection with screen edges
        if abs(dx) > abs(dy):  # More horizontal movement
            if dx > 0:  # Building is to the right
                arrow_x = screen_width - margin
                arrow_y = screen_center_y + (dy / dx) * (screen_width - margin - screen_center_x)
            else:  # Building is to the left
                arrow_x = margin
                arrow_y = screen_center_y + (dy / dx) * (margin - screen_center_x)
        else:  # More vertical movement
            if dy > 0:  # Building is below
                arrow_y = screen_height - margin
                arrow_x = screen_center_x + (dx / dy) * (screen_height - margin - screen_center_y)
            else:  # Building is above
                arrow_y = margin
                arrow_x = screen_center_x + (dx / dy) * (margin - screen_center_y)
        
        # Clamp to screen bounds
        arrow_x = max(margin, min(screen_width - margin, arrow_x))
        arrow_y = max(margin, min(screen_height - margin, arrow_y))
        
        return (int(arrow_x), int(arrow_y))
    
    def get_locked_arrow_position(self, building_screen_pos, screen_size, arrow_size):
        """Get position for locked arrow directly pointing to building on screen"""
        screen_width, screen_height = screen_size
        building_x, building_y = building_screen_pos
        
        # Check if building is visible on screen
        margin = arrow_size + 20  # Ensure arrow doesn't go off screen
        
        # If building is on screen, position arrow slightly offset from building
        if (margin < building_x < screen_width - margin and 
            margin < building_y < screen_height - margin):
            # Position arrow above the building
            return (building_x, building_y - arrow_size - 30)
        
        # If building is off-screen, still lock to its position but clamp to screen edges
        clamped_x = max(margin, min(screen_width - margin, building_x))
        clamped_y = max(margin, min(screen_height - margin, building_y))
        
        return (clamped_x, clamped_y)
    
    def draw_building_arrows(self, surface, player, buildings, camera, building_manager):
        """Draw arrows pointing to all buildings"""
        # Don't show arrows when inside a building
        if building_manager.is_inside_building():
            return
        
        screen_size = (surface.get_width(), surface.get_height())
        screen_center_x = screen_size[0] // 2
        screen_center_y = screen_size[1] // 2
        player_world_pos = (player.rect.centerx, player.rect.centery)
        
        for building in buildings:
            building_world_pos = (building.rect.centerx, building.rect.centery)
            distance = self.calculate_distance(player_world_pos, building_world_pos)
            
            # Skip if too close or too far
            if distance < self.min_distance or distance > self.max_distance:
                continue
            
            # Calculate building position on screen using camera
            building_screen_rect = camera.apply(building.rect)
            building_screen_pos = (building_screen_rect.centerx, building_screen_rect.centery)
            
            # Calculate size based on distance (closer = bigger)
            size_factor = 1.0 - ((distance - self.min_distance) / (self.max_distance - self.min_distance))
            size_factor = max(0.2, min(1.0, size_factor))  # Clamp between 0.2 and 1.0
            
            arrow_size = int(20 * size_factor)  # Base size 20 pixels
            text_size_multiplier = size_factor
            
            # Determine arrow behavior based on distance
            is_locked = distance <= self.lock_distance
            
            if is_locked:
                # Lock onto building - arrow points directly to building position
                arrow_pos = self.get_locked_arrow_position(building_screen_pos, screen_size, arrow_size)
                # Calculate angle from arrow position to building
                angle = self.calculate_angle(arrow_pos, building_screen_pos)
                
                # Make locked arrows more prominent
                arrow_size = int(arrow_size * 1.3)  # 30% bigger when locked
                
            else:
                # Normal behavior - arrow at screen edge
                arrow_pos = self.get_screen_edge_position(
                    (screen_center_x, screen_center_y), building_screen_pos, screen_size
                )
                
                if not arrow_pos:
                    continue
                
                # Calculate angle from screen center to building screen position
                angle = self.calculate_angle((screen_center_x, screen_center_y), building_screen_pos)
            
            # Draw arrow
            arrow_points = self.create_arrow_points(arrow_pos[0], arrow_pos[1], angle, arrow_size)
            
            # Arrow colors based on building type (brighter when locked)
            brightness_multiplier = 1.2 if is_locked else 1.0
            
            if building.building_type == "house":
                base_arrow_color = (100, 150, 255)  # Light blue
                base_outline_color = (50, 100, 200)  # Darker blue
            elif building.building_type == "shop":
                base_arrow_color = (255, 150, 100)  # Light orange
                base_outline_color = (200, 100, 50)  # Darker orange
            else:
                base_arrow_color = (150, 150, 150)  # Gray
                base_outline_color = (100, 100, 100)  # Darker gray
            
            # Apply brightness multiplier for locked arrows
            arrow_color = tuple(min(255, int(c * brightness_multiplier)) for c in base_arrow_color)
            outline_color = tuple(min(255, int(c * brightness_multiplier)) for c in base_outline_color)
            
            # Draw arrow with outline (thicker outline when locked)
            outline_width = 3 if is_locked else 2
            pygame.draw.polygon(surface, outline_color, arrow_points)
            pygame.draw.polygon(surface, arrow_color, arrow_points, 0)
            
            # Add pulsing effect for locked arrows
            if is_locked:
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 0.3 + 0.7
                pulse_color = tuple(int(c * pulse) for c in arrow_color)
                pygame.draw.polygon(surface, pulse_color, arrow_points, 0)
            
            # Convert distance to "tiles" (assuming ~32 pixels per tile)
            distance_in_tiles = int(distance / 32)
            distance_text = f"{distance_in_tiles} tiles"
            building_name = self.building_names.get(building.building_type, building.building_type.title())
            
            # Add "NEARBY" indicator for locked arrows
            if is_locked:
                building_name = f">>> {building_name} <<<"
                distance_text = "NEARBY, Press E to Enter"
            
            # Choose font based on size
            if text_size_multiplier > 0.7:
                font = self.font_chat
            else:
                font = self.font_smallest
            
            # Create text surfaces
            name_surface = font.render(building_name, True, (255, 255, 255))
            distance_surface = font.render(distance_text, True, (200, 200, 200))
            
            # Scale text if very small
            if text_size_multiplier < 0.8 and not is_locked:
                scale_factor = max(0.6, text_size_multiplier)
                original_size = name_surface.get_size()
                new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                name_surface = pygame.transform.scale(name_surface, new_size)
                
                original_size = distance_surface.get_size()
                new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                distance_surface = pygame.transform.scale(distance_surface, new_size)
            
            # Position text near arrow (offset based on arrow direction)
            text_offset_distance = arrow_size + 15
            if is_locked:
                # For locked arrows, position text more prominently
                text_offset_distance = arrow_size + 25
            
            text_offset_x = -math.cos(angle) * text_offset_distance
            text_offset_y = -math.sin(angle) * text_offset_distance
            
            name_x = arrow_pos[0] + text_offset_x - name_surface.get_width() // 2
            name_y = arrow_pos[1] + text_offset_y - name_surface.get_height()
            
            distance_x = arrow_pos[0] + text_offset_x - distance_surface.get_width() // 2
            distance_y = name_y + name_surface.get_height() + 2
            
            # Draw text background for better readability (more prominent for locked)
            bg_alpha = 160 if is_locked else 128
            name_bg_rect = pygame.Rect(name_x - 4, name_y - 2, 
                                     name_surface.get_width() + 8, 
                                     name_surface.get_height() + distance_surface.get_height() + 6)
            
            # Semi-transparent background
            bg_surface = pygame.Surface((name_bg_rect.width, name_bg_rect.height))
            bg_surface.set_alpha(bg_alpha)
            bg_surface.fill((0, 0, 0))
            surface.blit(bg_surface, (name_bg_rect.x, name_bg_rect.y))
            
            # Draw text
            surface.blit(name_surface, (name_x, name_y))
            surface.blit(distance_surface, (distance_x, distance_y))
    
    def draw_compass(self, surface, player_direction=(0, -1)):
        """Draw a small compass at the top-left corner"""
        compass_size = 80
        compass_x = 20
        compass_y = 20
        compass_center = (compass_x + compass_size // 2, compass_y + compass_size // 2)
        
        # Create semi-transparent background
        compass_bg = pygame.Surface((compass_size, compass_size))
        compass_bg.set_alpha(120)
        compass_bg.fill((0, 0, 0))
        surface.blit(compass_bg, (compass_x, compass_y))
        
        # Draw compass circle outline
        pygame.draw.circle(surface, (200, 200, 200), compass_center, compass_size // 2 - 2, 2)
        
        # Draw cardinal directions
        directions = [
            ("N", 0, -1, (255, 100, 100)),  # North - Red
            ("E", 1, 0, (100, 255, 100)),   # East - Green  
            ("S", 0, 1, (100, 100, 255)),   # South - Blue
            ("W", -1, 0, (255, 255, 100))   # West - Yellow
        ]
        
        for label, dx, dy, color in directions:
            # Calculate position for direction label
            label_distance = compass_size // 2 - 15
            label_x = compass_center[0] + dx * label_distance
            label_y = compass_center[1] + dy * label_distance
            
            # Draw direction letter
            font = self.font_chat
            text_surface = font.render(label, True, color)
            text_rect = text_surface.get_rect(center=(label_x, label_y))
            surface.blit(text_surface, text_rect)
        
        # Draw compass needle pointing north
        needle_length = compass_size // 2 - 20
        needle_end_x = compass_center[0] + 0 * needle_length  # Always point north (up)
        needle_end_y = compass_center[1] + -1 * needle_length
        
        # Draw needle (thicker line)
        pygame.draw.line(surface, (255, 50, 50), compass_center, 
                        (needle_end_x, needle_end_y), 3)
        
        # Draw needle tip (small triangle)
        tip_size = 6
        tip_points = [
            (needle_end_x, needle_end_y - tip_size),
            (needle_end_x - tip_size//2, needle_end_y + tip_size//2),
            (needle_end_x + tip_size//2, needle_end_y + tip_size//2)
        ]
        pygame.draw.polygon(surface, (255, 50, 50), tip_points)
        
        # Draw center dot
        pygame.draw.circle(surface, (255, 255, 255), compass_center, 3)