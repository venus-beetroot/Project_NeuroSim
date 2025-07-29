"""
Main game class and game loop - Refactored with separated event handling
"""
import pygame
import random
import os
from typing import Optional
import math

# Import all the components
from functions.assets import app
from entities.player import Player
from entities import npc
from systems.camera import Camera

# Updated building imports - now using the refactored modular system
from world.building import Building, BuildingManager, create_building_manager
from systems.collision_system import CollisionSystem

from functions.assets.ai import get_ai_response
from utils.ui_utils import draw_text_box, draw_centered_text_box

# Import managers and UI components
from managers.chat_manager import ChatManager
from managers.ui_manager import UIManager
from ui.start_screen import StartScreen
from ui.chat_renderer import ChatRenderer
from core.states import GameState
from systems.arrow_system import BuildingArrowSystem
from systems.tip_system import TipManager

# Import the new event handler
from core.event_handler import EventHandler


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
        self._init_building()  # Now uses refactored building system
        self._init_systems()
        self._init_event_handler()  # Initialize the new event handler
        
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
        font_path = os.path.join("assets", "fonts", "PressStart2P.ttf")
        self.font_small = pygame.font.Font(font_path, 18)
        self.font_large = pygame.font.Font(font_path, 32)
        self.font_chat = pygame.font.Font(font_path, 14)
        self.font_smallest = pygame.font.Font(font_path, 12)
    
    def _init_systems(self):
        """Initialize tip manager and arrow system"""
        # Initialize tip manager
        self.tip_manager = TipManager(self.font_small, self.font_chat)
        
        # Initialize building arrow system
        self.arrow_system = BuildingArrowSystem(self.font_small, self.font_chat, self.font_smallest)
        
        # Start tutorial for new players (you could save this in a config file)
        if hasattr(self.tip_manager, 'start_tutorial'):
            self.tip_manager.start_tutorial()
    
    def _init_event_handler(self):
        """Initialize the event handler system"""
        self.event_handler = EventHandler(self)
    
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
        
        # Initialize tracking variables for tips
        self._player_has_moved = False
        self._has_talked_to_npc = False
        self._has_entered_building = False
    
    def _init_camera(self):
        """Initialize camera with smooth following"""
        self.camera = Camera(app.WIDTH, app.HEIGHT, self.map_size, self.map_size)
        
        # Optional: Enable smooth camera following
        self.camera.smooth_follow = True
        self.camera.smoothing = 0.05  # Adjust for desired smoothness
    
    def _init_building(self):
        """Initialize buildings with the new refactored building system"""
        map_center_x = self.map_size // 2
        map_center_y = self.map_size // 2
        
        # Create building data for the new system
        building_data = [
            {
                "x": map_center_x - 150,
                "y": map_center_y + 150,
                "building_type": "house"
            },
            {
                "x": map_center_x + 50,
                "y": map_center_y + 150,
                "building_type": "shop"
            }
        ]
        
        # Create buildings using the new system
        self.building_manager = create_building_manager(building_data, self.assets)
        self.buildings = self.building_manager.buildings  # For backwards compatibility
        
        # Initialize collision system for better collision management
        self.collision_system = CollisionSystem()
        
        # Add buildings to collision system
        for building in self.buildings:
            self.collision_system.add_collision_object(building)
        
        # Debug mode to see hitboxes
        self.debug_hitboxes = False
    
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
        """Main game loop - now using the event handler"""
        while self.running:
            self.clock.tick(60)
            self.event_handler.handle_events()  # Use the event handler
            self.update()
            self.draw()
        pygame.quit()
    
    def update(self):
        """Updated update method with new collision system"""
        if self.game_state == GameState.START_SCREEN:
            mouse_pos = pygame.mouse.get_pos()
            finished_action = self.start_screen.update(mouse_pos)
            if finished_action:
                self._handle_start_screen_action(finished_action)
            return
        
        # Only update player input when playing
        if self.game_state == GameState.PLAYING:
            # Track player movement
            old_pos = (self.player.rect.centerx, self.player.rect.centery)
            self.player.handle_input()
            new_pos = (self.player.rect.centerx, self.player.rect.centery)
            
            # Track movement for tips
            if old_pos != new_pos:
                self._player_has_moved = True
            
            # Handle camera differently based on interior/exterior
            if self.building_manager.is_inside_building():
                # Inside building - don't follow with camera, keep it centered
                pass  # Camera stays static for interior
            else:
                # Outside - follow player normally
                self.camera.follow(self.player)
        
        # Update game objects (except during settings)
        if self.game_state != GameState.SETTINGS:
            # Get collision objects based on current location using the new system
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
        
        # Update tips system
        self.update_tips()

    def update_tips(self):
        """Update tips system with current game state"""
        # Create game state dictionary for tip system
        game_state = {
            "start_time": self.start_ticks,
            "player_moved": self._player_has_moved,
            "near_npc": self._is_near_npc(),
            "near_building": self._is_near_building(),
            "inside_building": self.building_manager.is_inside_building(),
            "talked_to_npc": self._has_talked_to_npc,
            "hit_chat_cooldown": self.chat_manager.chat_cooldown > 0,
            "far_from_buildings": self._is_far_from_buildings()
        }
        
        # Update tip manager
        self.tip_manager.update(game_state)

    def _handle_start_screen_action(self, action):
        """Handle completed start screen actions after loading"""
        if action == "start":
            self.game_state = GameState.PLAYING
        elif action == "settings":
            self.game_state = GameState.SETTINGS
        elif action == "quit":
            self.running = False
            
    def toggle_debug_hitboxes(self):
        """Toggle hitbox visualization with enhanced debugging"""
        self.debug_hitboxes = not self.debug_hitboxes
        status = "ON" if self.debug_hitboxes else "OFF"
        print(f"Debug hitboxes: {status}")
        
        # Print building system info when debugging is enabled
        if self.debug_hitboxes:
            system_info = self.building_manager.get_system_info()
            print("Building System Info:", system_info)

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

    def draw(self):
        """Updated draw method for the refactored building system"""
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
            
            # Draw additional debug info if enabled
            if self.debug_hitboxes:
                self.building_manager.draw_debug_info(self.screen, self.camera)
            
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
            
            # Draw building arrows (only when outside)
            self.arrow_system.draw_building_arrows(
                self.screen, self.player, self.buildings, 
                self.camera, self.building_manager
            )
        
        # Draw UI overlays (these work in both interior and exterior)
        if self.game_state == GameState.INTERACTING and self.current_npc:
            self.chat_renderer.draw_chat_interface(self.current_npc, self.chat_manager)
        elif self.game_state == GameState.SETTINGS:
            self.ui_manager.draw_settings_menu()
        
        # Draw game UI (time/temperature)
        self.ui_manager.draw_game_time_ui()
        
        # Draw compass (only when outside buildings)
        if not self.building_manager.is_inside_building():
            self.arrow_system.draw_compass(self.screen)
        
        # Draw tips (always visible)
        self.tip_manager.draw(self.screen)
        
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
        
        # Draw bubble tail (triangle pointing down)
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
        """Complete version of interior speech bubble drawing"""
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

    def _is_near_npc(self):
        """Check if player is near any NPC"""
        player_pos = (self.player.rect.centerx, self.player.rect.centery)
        for npc_obj in self.npcs:
            npc_pos = (npc_obj.rect.centerx, npc_obj.rect.centery)
            distance = ((player_pos[0] - npc_pos[0]) ** 2 + (player_pos[1] - npc_pos[1]) ** 2) ** 0.5
            if distance <= 80:  # Slightly larger than interaction range
                return True
        return False

    def _is_near_building(self):
        """Check if player is near any building (close enough to enter)"""
        for building in self.buildings:
            # Check if player is near building entrance
            distance = ((self.player.rect.centerx - building.rect.centerx) ** 2 + 
                    (self.player.rect.centery - building.rect.centery) ** 2) ** 0.5
            if distance <= 100:  # Close enough to enter
                return True
        return False

    def _is_far_from_buildings(self):
        """Check if player is far from all buildings"""
        for building in self.buildings:
            distance = ((self.player.rect.centerx - building.rect.centerx) ** 2 + 
                    (self.player.rect.centery - building.rect.centery) ** 2) ** 0.5
            if distance <= 300:  # Within reasonable distance
                return False
        return True

    def trigger_tutorial(self):
        """Trigger the tutorial (for testing or restarting)"""
        if hasattr(self.tip_manager, 'start_tutorial'):
            self.tip_manager.start_tutorial()
        else:
            # Fallback if tip_manager doesn't have start_tutorial
            print("Tutorial triggered")

    def trigger_tip(self, tip_type):
        """Trigger a specific tip type for testing"""
        if hasattr(self.tip_manager, 'show_tip'):
            self.tip_manager.show_tip(tip_type)
        else:
            # Fallback for testing
            print(f"Tip triggered: {tip_type}")

    def print_building_system_status(self):
        """Print detailed status of the building system (for debugging)"""
        print("\n=== Building System Status ===")
        system_info = self.building_manager.get_system_info()
        for key, value in system_info.items():
            print(f"{key}: {value}")
        
        building_info = self.building_manager.get_building_info()
        print("\n=== Individual Building Info ===")
        for info in building_info:
            print(f"Building: {info}")
        print("=" * 30)