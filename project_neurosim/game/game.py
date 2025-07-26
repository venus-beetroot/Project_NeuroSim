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

# Import all the components
from functions.assets import app
from functions.core.player import Player
from functions.core import npc
from functions.core.camera import Camera
from functions.core.building import Building
from functions.assets.ai import get_ai_response
from utils.ui_utils import draw_text_box

# Import managers and UI components
from managers.chat_manager import ChatManager
from managers.ui_manager import UIManager
from ui.start_screen import StartScreen
from ui.chat_renderer import ChatRenderer
from game.states import GameState

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
    
    def _init_display(self):
        """Initialize the game display"""
        screen_width, screen_height = pygame.display.get_desktop_sizes()[0]
        self.screen = pygame.display.set_mode(
            (screen_width, screen_height), pygame.FULLSCREEN
        )
        pygame.display.set_caption("PROJECT NEUROSIM")
        self.clock = pygame.time.Clock()
    
    def _init_fonts(self):
        """Initialize game fonts"""
        font_path = os.path.join("assets", "PressStart2P.ttf")
        self.font_small = pygame.font.Font(font_path, 18)
        self.font_large = pygame.font.Font(font_path, 32)
        self.font_chat = pygame.font.Font(font_path, 14)
    
    def _init_game_objects(self):
        """Initialize game objects (player, NPCs, buildings, etc.)"""
        self.assets = app.load_assets()
        self.player = Player(100, 100, self.assets)
        
        self.npcs = [
            npc.NPC(200, 200, self.assets, "Dave"),
            npc.NPC(200, 100, self.assets, "Lisa"),
            npc.NPC(200, 300, self.assets, "Tom")
        ]
        
        # Create background
        map_size = 3000
        self.background = self._create_random_background(map_size, map_size)
    
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
        map_size = 3000
        self.camera = Camera(app.WIDTH, app.HEIGHT, map_size, map_size)
        
        # Optional: Enable smooth camera following
        self.camera.smooth_follow = True
        self.camera.smoothing = 0.05  # Adjust for desired smoothness
    
    def _init_building(self):
        """Initialize buildings with hitboxes"""
        # Create buildings with hitboxes
        self.buildings = [
            Building(150, 450, "house", self.assets),
            Building(800, 450, "shop", self.assets)
        ]
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
    
    def check_building_interactions(self):
        """Check if player can interact with any buildings"""
        for building in self.buildings:
            if building.can_enter and building.check_interaction_range(self.player.rect):
                # Show "Press E to enter" message
                draw_text_box(self.screen, self.font_small, "Press E to enter", 
                            (self.screen.get_width() // 2, self.screen.get_height() - 40))
                
                # Check if player pressed E
                keys = pygame.key.get_pressed()
                if keys[pygame.K_e]:
                    # Handle building entry logic here
                    print(f"Entering {building.building_type}")
                break
    
    def _try_interact_with_npc(self):
        """Try to interact with nearby NPCs"""
        for npc_obj in self.npcs:
            if self.player.rect.colliderect(npc_obj.rect):
                self.game_state = GameState.INTERACTING
                self.current_npc = npc_obj
                self.chat_manager.message = ""
                break
    
    def _exit_interaction(self):
        """Exit NPC interaction"""
        self.game_state = GameState.PLAYING
        self.chat_manager.message = ""
        self.current_npc = None
    
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
            # Check if loading finished and get the action
            finished_action = self.start_screen.update(mouse_pos)
            if finished_action:
                self._handle_start_screen_action(finished_action)
            return  # Don't update game objects on start screen
        
        # Only update player input when playing
        if self.game_state == GameState.PLAYING:
            self.player.handle_input()
            self.camera.follow(self.player)
        
        # Check for building interactions
        self.check_building_interactions()
        
        # Update game objects (except during settings)
        if self.game_state != GameState.SETTINGS:
            self.player.update(self.buildings)  # Collision handling is now inside player.update()
            for npc_obj in self.npcs:
                npc_obj.update()
        
        # Update chat system
        if self.game_state == GameState.INTERACTING and self.current_npc:
            self.chat_manager.update_cooldown(self.clock.get_time())
            
            if self.chat_manager.update_typing_animation(self.current_npc.dialogue):
                # Finished typing - add to chat history
                self.current_npc.chat_history.append(("npc", self.chat_manager.current_response))
                self.chat_manager.current_response = ""
    
    def toggle_debug_hitboxes(self):
        """Toggle hitbox visualization (useful for debugging)"""
        self.debug_hitboxes = not self.debug_hitboxes
        print(f"Debug hitboxes: {'ON' if self.debug_hitboxes else 'OFF'}")
    
    def draw(self):
        """Render all game elements"""
        if self.game_state == GameState.START_SCREEN:
            self.start_screen.draw()
            pygame.display.flip()
            return
        
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
        
        # Draw NPCs with camera offset
        for npc_obj in self.npcs:
            npc_screen_rect = self.camera.apply(npc_obj.rect)
            self.screen.blit(npc_obj.image, npc_screen_rect)
        
        # Draw UI overlays
        if self.game_state == GameState.INTERACTING and self.current_npc:
            self.chat_renderer.draw_chat_interface(self.current_npc, self.chat_manager)
        elif self.game_state == GameState.SETTINGS:
            self.ui_manager.draw_settings_menu()
        
        # Draw game UI (time/temperature)
        self.ui_manager.draw_game_time_ui()
        
        pygame.display.flip()