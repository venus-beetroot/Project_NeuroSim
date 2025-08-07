"""
Main game class and game loop - Refactored with separated event handling
"""
import pygame
import random
import os
from typing import Optional
import math

# Import all the components
from functions import app
from entities.player import Player
from entities import npc
from systems.camera import Camera

# Updated building imports - now using the refactored modular system
from world.building import Building, BuildingManager, create_building_manager
from systems.collision_system import CollisionSystem

from functions.ai import get_ai_response
from utils.ui_utils import draw_text_box, draw_centered_text_box

# Import managers and UI components
from managers.chat_manager import ChatManager
from managers.ui_manager import UIManager
from ui.start_screen import StartScreen
from ui.chat_renderer import ChatRenderer
from core.states import GameState
from systems.arrow_system import BuildingArrowSystem
from systems.tip_system import TipManager
from world.map_generator import MapGenerator, TileType, create_map_generator


# Import the new event handler
from core.event_handler import EventHandler
from utils.debug_utils import DebugUtils


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
        self._init_debug_utils()  # Initialize debug utilities
        
        self.showing_credits = False
        self.showing_version = False
        self.sound_enabled = True
        self.showing_keybinds = False
    
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
    
    def _init_debug_utils(self):
        """Initialize debug utilities"""
        self.debug_utils = DebugUtils(self)
        # Keep backward compatibility
        self.debug_hitboxes = False
    
    def _init_game_objects(self):
        """Initialize game objects (player, NPCs, buildings, etc.)"""
        self.assets = app.load_assets()
        
        # Map configuration
        self.map_size = 3000
        map_center_x = self.map_size // 2
        map_center_y = self.map_size // 2

        player_spawn_x = map_center_x
        player_spawn_y = map_center_y + 200
        
        # Spawn player at the center of the map (with NPCs)
        self.player = Player(player_spawn_x, player_spawn_y, self.assets)
        
        # Define hangout area at the center of the map - make it larger to include buildings
        center_hangout_area = {
            'x': map_center_x - 200,  # Expanded to 400x400 pixel area around center
            'y': map_center_y - 200,
            'width': 400,
            'height': 400
        }
        
        # Create NPCs with center hangout area - spread them around the player
        self.npcs = []
        npc_spawn_data = [
            ("Dave", map_center_x - 80, map_center_y - 80),
            ("Lisa", map_center_x + 80, map_center_y - 80),
            ("Tom", map_center_x, map_center_y + 100)
        ]

        # Create buildings first (they're created in _init_building)
        # We'll fix spawn positions after buildings are created
        for name, x, y in npc_spawn_data:
            self.npcs.append(npc.NPC(x, y, self.assets, name, center_hangout_area))
        
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
        """Initialize camera with smooth following - FIXED for dynamic map size"""
        self.camera = Camera(app.WIDTH, app.HEIGHT, self.map_size, self.map_size)  # Use self.map_size here
        
        # Optional: Enable smooth camera following
        self.camera.smooth_follow = True
        self.camera.smoothing = 0.1  # Adjust for desired smoothness
    
    def _init_building(self):
        """Initialize buildings with the new refactored building system including one fountain"""
        map_center_x = self.map_size // 2
        map_center_y = self.map_size // 2
        
        # Create building data - just add fountain to existing setup
        building_data = [
            # Town hall in the center
            {
                "x": map_center_x - 100,
                "y": map_center_y - 50,
                "building_type": "town_hall"
            },
            # House moved to the left
            {
                "x": map_center_x - 300,
                "y": map_center_y + 100,
                "building_type": "house"
            },
            # Shop moved to the right
            {
                "x": map_center_x + 200,
                "y": map_center_y + 100,
                "building_type": "shop"
            },
            # New ramen shop
            {
                "x": map_center_x + 400,
                "y": map_center_y + 100,
                "building_type": "food_shop"
            },
            # Fountain stays where it is (no change)
            {
                "x": map_center_x - 300,
                "y": map_center_y - 300,
                "building_type": "fountain"
            }
        ]
        
        # Create buildings using the enhanced system
        self.building_manager = create_building_manager(building_data, self.assets)
        self.buildings = self.building_manager.buildings  # For backwards compatibility
        
        # Initialize collision system for better collision management
        self.collision_system = CollisionSystem()
        
        # Add buildings to collision system
        for building in self.buildings:
            self.collision_system.add_collision_object(building)
        
        # Fix NPC spawn positions to avoid building collisions
        self._fix_npc_spawn_positions() 

    def _fix_npc_spawn_positions(self):
        """Fix NPC spawn positions to ensure they don't spawn inside buildings"""
        for npc_obj in self.npcs:
            # Check if NPC spawned inside a building and fix it
            npc_obj.check_and_fix_spawn_collision(self.buildings)
            print(f"NPC {npc_obj.name} final position: ({npc_obj.rect.centerx}, {npc_obj.rect.centery})")

    def _create_random_background(self, width: int, height: int) -> pygame.Surface:
        """Create a background using the ENHANCED building-centered map generation system"""
        tile_size = 32  # Adjust this to match your tile size
        
        # Create the ENHANCED map generator
        map_generator = create_map_generator(width, height, tile_size)
        
        # Pass the building positions to the map generator
        map_center_x = self.map_size // 2
        map_center_y = self.map_size // 2
        
        building_positions = [
            (map_center_x - 100, map_center_y - 50),   # Town hall
            (map_center_x - 300, map_center_y + 100), # House  
            (map_center_x + 200, map_center_y + 100), # Shop
            (map_center_x + 400, map_center_y + 100), # Ramen shop
            (map_center_x - 300, map_center_y - 300)  # Fountain
        ]
        
        map_generator.set_pre_placed_buildings(building_positions)
        
        # Generate the map with enhanced building-centered cities and connecting paths
        generated_surface = map_generator.generate_map()
        
        # Store the map generator for later use and debugging
        self.map_generator = map_generator
        
        # Apply actual tile textures instead of colored rectangles - THIS IS THE KEY PART
        return self._apply_tile_textures(generated_surface, map_generator, tile_size)
    
    def _apply_tile_textures(self, base_surface: pygame.Surface, 
                                map_generator: MapGenerator, tile_size: int) -> pygame.Surface:
        """Apply actual tile textures to the generated map - DEBUG VERSION"""
        # Create a copy of the base surface
        textured_surface = base_surface.copy()
        
        # Load tiles (keeping your existing tile loading logic)
        tiles = {}
        try:
            # Load nature tile (base grass)
            tiles["nature"] = pygame.image.load("assets/images/environment/base_grass_tile0.png")
            print("✓ Loaded nature tile")
            
            # Load nature decoration tiles
            tiles["flower"] = pygame.image.load("assets/images/environment/flower_0.png")
            tiles["red_flower"] = pygame.image.load("assets/images/environment/red_flower_tile_0.png")
            tiles["log"] = pygame.image.load("assets/images/environment/log_tile_0.png")
            tiles["bush"] = pygame.image.load("assets/images/environment/bush_tile_0.png")
            tiles["rock"] = pygame.image.load("assets/images/environment/rock-tile.png")
            print(f"✓ Loaded {len(tiles)} decoration tiles")
            
            # Load path tiles
            tiles["base_path"] = pygame.image.load("assets/images/environment/base-city-tile-path.png")
            tiles["path_west"] = pygame.image.load("assets/images/environment/city-tile-path-west-side.png")
            tiles["path_east"] = pygame.image.load("assets/images/environment/city-tile-path-east-side.png")
            tiles["path_south"] = pygame.image.load("assets/images/environment/city-tile-path-south-side.png")
            tiles["path_north"] = pygame.image.load("assets/images/environment/city-tile-path-north-side.png")
            tiles["path_nw_corner"] = pygame.image.load("assets/images/environment/city-tile-path-north-west-corner.png")
            tiles["path_ne_corner"] = pygame.image.load("assets/images/environment/city-tile-path-north-east-corner.png")
            tiles["path_sw_corner"] = pygame.image.load("assets/images/environment/city-tile-path-south-west-corner.png")
            tiles["path_se_corner"] = pygame.image.load("assets/images/environment/city-tile-path-south-east-corner.png")
            print(f"✓ Loaded path tiles, total tiles: {len(tiles)}")
            
            # CITY TILES - Enhanced with better variety
            tiles["city_interior"] = pygame.image.load("assets/images/environment/base-city-tile-path.png")
            tiles["city_top_left_corner"] = pygame.image.load("assets/images/environment/city-tile-path-south-east-corner.png")
            tiles["city_top_right_corner"] = pygame.image.load("assets/images/environment/city-tile-path-south-west-corner.png")
            tiles["city_bottom_left_corner"] = pygame.image.load("assets/images/environment/city-tile-path-north-east-corner.png")
            tiles["city_bottom_right_corner"] = pygame.image.load("assets/images/environment/city-tile-path-north-west-corner.png")
            tiles["city_top_edge"] = pygame.image.load("assets/images/environment/city-tile-path-south-side.png")
            tiles["city_bottom_edge"] = pygame.image.load("assets/images/environment/city-tile-path-north-side.png")
            tiles["city_left_edge"] = pygame.image.load("assets/images/environment/city-tile-path-east-side.png")
            tiles["city_right_edge"] = pygame.image.load("assets/images/environment/city-tile-path-west-side.png")
            tiles["city_inner_top_corner"] = pygame.image.load("assets/images/environment/city-tile-path-north-east-corner.png")
            tiles["city_inner_bottom_corner"] = pygame.image.load("assets/images/environment/city-tile-path-south-east-corner.png")
            tiles["city_inner_left_corner"] = pygame.image.load("assets/images/environment/city-tile-path-north-west-corner.png")
            tiles["city_inner_right_corner"] = pygame.image.load("assets/images/environment/city-tile-path-south-west-corner.png")
            tiles["city_isolated"] = pygame.image.load("assets/images/environment/base-city-tile-path.png")
            print(f"✓ All tiles loaded successfully, total: {len(tiles)}")
            
            # Scale all tiles to match tile_size
            for key in tiles:
                tiles[key] = pygame.transform.scale(tiles[key], (tile_size, tile_size))
            print(f"✓ All tiles scaled to {tile_size}x{tile_size}")
            
        except pygame.error as e:
            # If tiles can't be loaded, return the colored surface
            print(f"❌ ERROR: Could not load tile textures - {e}")
            print("Using colored rectangles instead")
            return textured_surface
        
        # Apply textures based on tile type using the enhanced tilemap
        grid_width = base_surface.get_width() // tile_size
        grid_height = base_surface.get_height() // tile_size
        
        print(f"Applying textures to {grid_width}x{grid_height} grid...")
        
        # Count tile types for debugging
        tile_counts = {}
        
        for y in range(grid_height):
            for x in range(grid_width):
                # Get tile from the enhanced tilemap system
                tile = map_generator.tilemap.get_tile(x, y)
                pixel_x = x * tile_size
                pixel_y = y * tile_size
                
                # Count tiles for debugging
                tile_name = tile.name if hasattr(tile, 'name') else str(tile)
                tile_counts[tile_name] = tile_counts.get(tile_name, 0) + 1
                
                # Apply texture based on tile type
                if tile.value == 0:  # NATURE
                    textured_surface.blit(tiles["nature"], (pixel_x, pixel_y))
                    
                elif tile.value == 3:  # NATURE_FLOWER
                    textured_surface.blit(tiles["flower"], (pixel_x, pixel_y))
                    
                elif tile.value == 5:  # NATURE_LOG
                    textured_surface.blit(tiles["log"], (pixel_x, pixel_y))
                    
                elif tile.value == 4:  # NATURE_FLOWER_RED
                    textured_surface.blit(tiles["red_flower"], (pixel_x, pixel_y))
                    
                elif tile.value == 6:  # NATURE_BUSH
                    textured_surface.blit(tiles["bush"], (pixel_x, pixel_y))

                elif tile.value == 7:  # NATURE_ROCK
                    textured_surface.blit(tiles["rock"], (pixel_x, pixel_y))
                    
                elif tile.value == 1:  # CITY
                    # Use the city tile type determined by enhanced auto-tiling
                    city_tile_type = map_generator.tilemap.get_city_tile_type(x, y)
                    city_tile_type = max(0, min(13, city_tile_type))
                    
                    # Map city tile types to actual tiles using integer indices
                    city_tiles = [
                        tiles["city_interior"],           # 0
                        tiles["city_top_left_corner"],    # 1
                        tiles["city_top_right_corner"],   # 2
                        tiles["city_bottom_left_corner"], # 3
                        tiles["city_bottom_right_corner"],# 4
                        tiles["city_top_edge"],           # 5
                        tiles["city_bottom_edge"],        # 6
                        tiles["city_left_edge"],          # 7
                        tiles["city_right_edge"],         # 8
                        tiles["city_interior"],           # 9 - inner corners use interior for now
                        tiles["city_interior"],           # 10
                        tiles["city_interior"],           # 11
                        tiles["city_interior"],           # 12
                        tiles["city_isolated"]            # 13
                    ]
                    
                    if 0 <= city_tile_type < len(city_tiles):
                        textured_surface.blit(city_tiles[city_tile_type], (pixel_x, pixel_y))
                    else:
                        # Fallback to interior tile
                        textured_surface.blit(tiles["city_interior"], (pixel_x, pixel_y))
                    
                elif tile.value == 2:  # ROAD
                    # Use the appropriate path tile based on enhanced auto-tiling
                    path_tile_type = map_generator.tilemap.get_path_tile_type(x, y)
                    
                    path_tile_map = {
                        "base-city-tile-path": tiles["base_path"],
                        "city-tile-path-west-side": tiles["path_west"],
                        "city-tile-path-east-side": tiles["path_east"],
                        "city-tile-path-south-side": tiles["path_south"],
                        "city-tile-path-north-side": tiles["path_north"],
                        "city-tile-path-north-west-corner": tiles["path_nw_corner"],
                        "city-tile-path-north-east-corner": tiles["path_ne_corner"],
                        "city-tile-path-south-west-corner": tiles["path_sw_corner"],
                        "city-tile-path-south-east-corner": tiles["path_se_corner"]
                    }
                    
                    if path_tile_type and path_tile_type in path_tile_map:
                        textured_surface.blit(path_tile_map[path_tile_type], (pixel_x, pixel_y))
                    else:
                        # Fallback to base path tile
                        textured_surface.blit(tiles["base_path"], (pixel_x, pixel_y))
                
                elif tile.value == 8:  # BUILDING
                    # Buildings could have their own special tile
                    textured_surface.blit(tiles["city_interior"], (pixel_x, pixel_y))
        
        print("Tile counts:", tile_counts)
        print("✓ Texture application complete")
        return textured_surface

    def run(self):
        """Main game loop - now using the event handler"""
        while self.running:
            self.clock.tick(60)
            self.event_handler.handle_events()  # Use the event handler
            self.update()
            self.draw()
        pygame.quit()

    def _get_ai_response_callback(self):
        """Create AI response callback for enhanced chat system"""
        def ai_callback(npc_id: str, message: str, context):
            # Find the NPC
            npc = None
            for npc_obj in self.npcs:
                test_id = f"{npc_obj.name}_{npc_obj.rect.x}_{npc_obj.rect.y}"
                if test_id == npc_id:
                    npc = npc_obj
                    break
            
            if not npc:
                return "I seem to have lost my train of thought..."
            
            # Build conversation history
            conversation_history = []
            for msg in context[-5:]:  # Last 5 messages
                if msg.sender.value == "player":
                    conversation_history.append(("player", msg.content))
                elif msg.sender.value == "npc":
                    conversation_history.append(("npc", msg.content))
            
            # Add current message
            conversation_history.append(("player", message))
            
            # Use your existing AI system
            try:
                from functions.ai import get_ai_response
                
                # Build prompt
                prompt = f"""You are {npc.name}, a character in a simulation game.

    Personality: {getattr(npc, 'dialogue', 'Friendly and helpful')}

    Recent conversation:
    """
                for role, msg in conversation_history:
                    prompt += f"{role.title()}: {msg}\n"
                
                prompt += f"\nRespond as {npc.name} in 1-3 sentences:"
                
                response = get_ai_response(prompt)
                return response if response else "That's interesting. Tell me more!"
                
            except Exception as e:
                print(f"AI response error: {e}")
                return "Sorry, I'm having trouble thinking right now."
        
        return ai_callback
    
    def update(self):
        """Updated update method with AI response handling"""
        if self.game_state == GameState.START_SCREEN:
            mouse_pos = pygame.mouse.get_pos()
            finished_action = self.start_screen.update(mouse_pos)
            if finished_action:
                self.event_handler._handle_start_screen_action(finished_action)
            return
        
        # Handle pending AI responses
        if hasattr(self, '_pending_ai_response') and self._pending_ai_response:
            ai_response = self._pending_ai_response
            self._pending_ai_response = None
            
            # Start the typing animation for the AI response
            if self.current_npc and self.game_state == GameState.INTERACTING:
                self.chat_manager.start_typing_animation(ai_response)
        
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
                pass  # Camera stays static for interior
            else:
                self.camera.follow(self.player)
        
        # Update game objects (except during settings)
        if self.game_state != GameState.SETTINGS:
            # Get collision objects based on current location
            if self.building_manager.is_inside_building():
                collision_objects = self.building_manager.get_interior_collision_walls()
            else:
                collision_objects = self.buildings
            
            self.player.update(collision_objects)
            
            # Update NPCs
            for npc_obj in self.npcs:
                npc_obj.update(self.player, self.buildings, self.building_manager)
        
        # Update chat system with lock handling
        if self.game_state == GameState.INTERACTING and self.current_npc:
            self.chat_manager.update_cooldown(self.clock.get_time())
            
            # Update typing animation - this will unlock chat when finished
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
        """Handle completed start screen actions after loading - FIXED VERSION"""
        if action == "start":
            self.game_state = GameState.PLAYING
        elif action == "settings":
            self.game_state = GameState.SETTINGS
        elif action == "credits":
            # Properly delegate to event handler
            if hasattr(self.event_handler, '_handle_start_screen_action'):
                self.event_handler._handle_start_screen_action(action)
            else:
                # Fallback for compatibility
                self.event_handler.showing_credits = True
                self.showing_credits = True
        elif action == "quit":
            self.running = False

    # Debug methods now delegated to debug_utils
    def toggle_debug_hitboxes(self):
        """Toggle hitbox visualization - now uses debug_utils"""
        return self.debug_utils.toggle_debug_hitboxes()

    def debug_collision_at_position(self, x, y):
        """Debug collision at position - now uses debug_utils"""
        return self.debug_utils.debug_collision_at_position(x, y)

    def debug_map_info(self):
        """Debug map info - now uses debug_utils"""
        return self.debug_utils.debug_map_info()

    def print_building_system_status(self):
        """Print building system status - now uses debug_utils"""
        return self.debug_utils.print_building_system_status()

    def limit_npc_response(self, response_text: str, max_sentences: int = 3) -> str:
        """Limit NPC response to prevent overly long responses"""
        if not response_text.strip():
            return response_text
        
        import re
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', response_text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Limit to max_sentences
        if len(sentences) <= max_sentences:
            return response_text
        
        # Take first max_sentences and join them back
        limited_sentences = sentences[:max_sentences]
        limited_response = ' '.join(limited_sentences)
        
        # Ensure proper punctuation
        if limited_response and limited_response[-1] not in '.!?':
            limited_response += '.'
        
        return limited_response

    def draw(self):
        """Updated draw method for the refactored building system"""
        if self.game_state == GameState.START_SCREEN:
            self.start_screen.draw()
            # Draw overlays even on start screen
            if hasattr(self.event_handler, 'render_overlays'):
                self.event_handler.render_overlays()
            elif hasattr(self, 'showing_credits') and self.showing_credits:
                self._draw_credits_overlay()
            elif hasattr(self, 'showing_version') and self.showing_version:
                self._draw_version_overlay()

            # Draw keybind overlay (highest priority)
            if self.showing_keybinds and hasattr(self.event_handler, 'keybind_overlay_handler'):
                self.event_handler.keybind_overlay_handler.render()
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
            self.event_handler.render_corner_version()
        
        # Draw game UI (time/temperature)
        self.ui_manager.draw_game_time_ui()
        
        # Draw compass (only when outside buildings)
        if not self.building_manager.is_inside_building():
            self.arrow_system.draw_compass(self.screen)
        
        # Draw tips (always visible)
        self.tip_manager.draw(self.screen)
        
        # Draw overlays using event handler
        if hasattr(self.event_handler, 'render_overlays'):
            self.event_handler.render_overlays()
        elif hasattr(self, 'showing_credits') and self.showing_credits:
            self._draw_credits_overlay()
        elif hasattr(self, 'showing_version') and self.showing_version:
            self._draw_version_overlay()

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
        if hasattr(self.tip_manager, 'trigger_tip'):
            self.tip_manager.trigger_tip(tip_type, force=True)  # Use force=True for testing
        else:
            # Fallback for testing
            print(f"Tip triggered: {tip_type}")

    def get_keybind_manager(self):
        """Get reference to keybind manager"""
        if hasattr(self.event_handler, 'keybind_manager'):
            return self.event_handler.keybind_manager
        return None

    # Additional debug utility access methods
    def get_debug_utils(self):
        """Get access to debug utilities for external use"""
        return self.debug_utils

    def comprehensive_debug_report(self):
        """Generate comprehensive debug report - delegated to debug_utils"""
        return self.debug_utils.comprehensive_debug_report()

    def debug_player_state(self):
        """Debug player state - delegated to debug_utils"""
        return self.debug_utils.debug_player_state()

    def debug_npc_states(self):
        """Debug NPC states - delegated to debug_utils"""
        return self.debug_utils.debug_npc_states()

    def debug_camera_state(self):
        """Debug camera state - delegated to debug_utils"""
        return self.debug_utils.debug_camera_state()

    def debug_game_state(self):
        """Debug game state - delegated to debug_utils"""
        return self.debug_utils.debug_game_state()

    def debug_performance_info(self):
        """Debug performance info - delegated to debug_utils"""
        return self.debug_utils.debug_performance_info()

    def _draw_credits_overlay(self):
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))
        font = self.font_large
        text = "CREDITS"
        text_surf = font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(self.screen.get_width() // 2, 150))
        self.screen.blit(text_surf, text_rect)
        font_small = self.font_small
        credits_lines = [
            "Haoran Fang",
            "Angus Shui",
            "Lucas Guo",
            "(and contributors)"
        ]
        for i, line in enumerate(credits_lines):
            surf = font_small.render(line, True, (200, 200, 200))
            rect = surf.get_rect(center=(self.screen.get_width() // 2, 250 + i * 40))
            self.screen.blit(surf, rect)
        esc_surf = font_small.render("Press ESC to return", True, (180, 180, 180))
        esc_rect = esc_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 100))
        self.screen.blit(esc_surf, esc_rect)

    def _draw_version_overlay(self):
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))
        font = self.font_large
        text = "VERSION"
        text_surf = font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(text_surf, text_rect)
        font_small = self.font_small
        version_str = getattr(self, 'VERSION', '0.8.2 Alpha')
        version_surf = font_small.render(f"v{version_str}", True, (200, 200, 200))
        version_rect = version_surf.get_rect(center=(self.screen.get_width() // 2, 300))
        self.screen.blit(version_surf, version_rect)
        esc_surf = font_small.render("Press ESC to return", True, (180, 180, 180))
        esc_rect = esc_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 100))
        self.screen.blit(esc_surf, esc_rect)

    def handle_overlay_escape(self):
        """Call this from event handler to exit overlays on ESC"""
        if self.showing_credits:
            self.showing_credits = False
            return True
        if self.showing_version:
            self.showing_version = False
            return True
        return False

    # Building interaction methods
    def try_interact_with_npc(self):
        """Attempt to interact with nearby NPCs"""
        for npc_obj in self.npcs:
            # Calculate distance between player and NPC
            distance = ((self.player.rect.centerx - npc_obj.rect.centerx) ** 2 + 
                       (self.player.rect.centery - npc_obj.rect.centery) ** 2) ** 0.5
            
            if distance <= 60:  # Interaction range in pixels
                self.game_state = GameState.INTERACTING
                self.current_npc = npc_obj
                self.chat_manager.message = ""
                break

    def handle_building_interaction(self):
        """Handle entering/exiting buildings"""
        if self.building_manager.is_inside_building():
            # Player is inside - try to exit
            if self.building_manager.check_building_exit(self.player.rect):
                success = self.building_manager.exit_building(self.player)
                if success:
                    # Ensure position is synchronized after exit
                    self.player.sync_position()
                    # Reset camera to follow player again
                    self.camera.follow(self.player)
                    print("Exited building")
        else:
            # Player is outside - try to enter building
            building = self.building_manager.check_building_entry(self.player.rect)
            if building:
                success = self.building_manager.enter_building(building, self.player)
                if success:
                    # Ensure position is synchronized after entry
                    self.player.sync_position()
                    # Track building entry for tips system
                    self._has_entered_building = True
                    print(f"Entered {building.building_type}")

    def exit_interaction(self):
        """Exit NPC interaction and return to gameplay - FIXED with proper lock checking"""
        # Check if chat is locked and prevent exit
        if hasattr(self.chat_manager, 'can_exit_chat'):
            if not self.chat_manager.can_exit_chat():
                print("Cannot exit chat - AI is processing or NPC is typing")
                return False  # Indicate that exit was blocked
        
        # Check legacy lock method as fallback
        elif hasattr(self.chat_manager, 'is_chat_locked'):
            if self.chat_manager.is_chat_locked():
                print("Cannot exit chat - system is locked")
                return False
        
        # Normal exit behavior
        self.game_state = GameState.PLAYING
        self.chat_manager.message = ""
        self.current_npc = None
        
        # Clear any pending AI responses
        if hasattr(self, '_pending_ai_response'):
            self._pending_ai_response = None
        
        print("Successfully exited chat interaction")
        return True

    def send_chat_message(self):
        """Send chat message and trigger AI response with FIXED locking"""
        if not self.current_npc:
            print("No current NPC to send message to")
            return
        
        if not self.chat_manager.can_send_message():
            print("Cannot send message - conditions not met")
            return
        
        # Send the message (this will lock the chat)
        sent_message = self.chat_manager.send_message(self.current_npc)
        if not sent_message:
            print("Failed to send message")
            return
        
        # Track that player has talked to NPC (for tips system)
        self._has_talked_to_npc = True
        
        print(f"Sent message: {sent_message}")
        
        # Get AI response asynchronously to avoid blocking
        self._get_ai_response_async(sent_message)

    def _get_ai_response_async(self, message: str):
        """Get AI response asynchronously and handle the response - SECURE VERSION"""
        import threading
        
        def ai_response_thread():
            try:
                # Build conversation context
                conversation_history = []
                for msg in self.current_npc.chat_history[-10:]:  # Last 10 messages for context
                    if isinstance(msg, tuple):
                        role, content = msg
                        conversation_history.append((role, content))
                
                # Use the SECURE prompt builder that prevents personality leaking
                prompt = self.build_improved_ai_prompt(self.current_npc, conversation_history, message)
                
                # Get AI response (this may take time)
                from functions.ai import get_ai_response
                ai_response = get_ai_response(prompt)
                
                if not ai_response:
                    ai_response = "That's interesting. Tell me more!"
                
                # Limit response length to prevent overly long responses
                ai_response = self.limit_npc_response(ai_response, max_sentences=3)
                
                # Schedule the response to be processed on the main thread
                self._pending_ai_response = ai_response
                
            except Exception as e:
                print(f"AI response error: {e}")
                # Fallback response
                self._pending_ai_response = "Sorry, I'm having trouble thinking right now."
        
        # Start the AI response thread
        thread = threading.Thread(target=ai_response_thread, daemon=True)
        thread.start()

    def _build_improved_ai_prompt(self, npc, conversation_history, message):
        """FIXED: Build AI prompt without personality leaking"""
        return self.build_improved_ai_prompt(npc, conversation_history, message)

    
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            pygame.mixer.music.set_volume(1.0)
        else:
            pygame.mixer.music.set_volume(0.0)

    def _find_safe_spawn_position(self, preferred_x, preferred_y, search_radius=100):
        """Find a safe spawn position that doesn't collide with buildings"""
        # Check if preferred position is safe
        test_rect = pygame.Rect(preferred_x - 16, preferred_y - 16, 32, 32)  # Player size
        
        # Check collision with all buildings
        for building in self.buildings:
            if building.check_collision(test_rect):
                # Try positions in a circle around the preferred position
                import math
                for angle in range(0, 360, 30):  # Check every 30 degrees
                    for distance in range(50, search_radius, 25):  # Check at different distances
                        offset_x = math.cos(math.radians(angle)) * distance
                        offset_y = math.sin(math.radians(angle)) * distance
                        
                        new_x = preferred_x + offset_x
                        new_y = preferred_y + offset_y
                        
                        test_rect = pygame.Rect(new_x - 16, new_y - 16, 32, 32)
                        
                        # Check if this position is safe
                        safe = True
                        for check_building in self.buildings:
                            if check_building.check_collision(test_rect):
                                safe = False
                                break
                        
                        if safe:
                            return int(new_x), int(new_y)
        
        # If no safe position found, return original
        return preferred_x, preferred_y