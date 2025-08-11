import pygame
import json
import os
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from .tilemap import Tile


class TilemapEditor:
    """Developer tool for editing tilemaps in real-time"""
    
    def __init__(self, game_ref):
        self.game = game_ref
        self.enabled = False
        
        self.selected_tile = Tile.NATURE
        self.brush_size = 1
        self.camera_speed = 300
        
        # Editor camera (separate from game camera)
        self.camera_x = 0
        self.camera_y = 0
        
        # Drag functionality
        self.is_dragging = False
        self.drag_start_tile = None
        self.drag_current_tile = None
        
        # Text input for tile selection
        self.text_input_active = False
        self.text_input_buffer = ""
        self.text_input_cursor_time = 0

        # Save notification
        self.save_message_timer = 0
        self.save_message_duration = 3.0
        self.save_message_fade_start = 2.0
        
        # Expanded tile names mapping for display including path tiles
        self.tile_names = {
            1: "NATURE", 2: "CITY", 3: "ROAD", 4: "NATURE_FLOWER",
            5: "NATURE_LOG", 6: "NATURE_BUSH", 
            7: "NATURE_ROCK", 8: "NATURE_FLOWER_RED"
        }
        
        # City tile subtypes for advanced editing
        self.city_tile_types = {
            0: "CITY_INTERIOR", 1: "CITY_TOP_LEFT", 2: "CITY_TOP_RIGHT",
            3: "CITY_BOTTOM_LEFT", 4: "CITY_BOTTOM_RIGHT", 5: "CITY_TOP_EDGE",
            6: "CITY_BOTTOM_EDGE", 7: "CITY_LEFT_EDGE", 8: "CITY_RIGHT_EDGE",
            9: "CITY_INNER_TOP", 10: "CITY_INNER_BOTTOM", 11: "CITY_INNER_LEFT",
            12: "CITY_INNER_RIGHT", 13: "CITY_ISOLATED"
        }
        
        # Advanced mode for city tile editing
        self.advanced_city_mode = False
        self.selected_city_type = 0
        
    def _get_tile_value(self, tile) -> int:
        """Safely extract tile value from either enum or int"""
        if isinstance(tile, int):
            return tile
        elif hasattr(tile, 'value'):
            return tile.value
        else:
            return 0
            
    def _get_tile_name(self, tile) -> str:
        """Safely get tile name for display"""
        if hasattr(tile, 'name'):
            return tile.name
        else:
            tile_value = self._get_tile_value(tile)
            return self.tile_names.get(tile_value, f"Unknown_{tile_value}")
        
    def toggle_editor(self) -> bool:
        """Toggle the tilemap editor on/off"""
        self.enabled = not self.enabled
        
        if self.enabled:
            print("=== ENHANCED MAP EDITOR ENABLED ===")
            print("Basic Keys:")
            print("  1-8 = Basic tile types")
            print("  SPACE = Place tile at crosshair")
            print("  ENTER = Start/end drag selection")
            print("  B/N = Change brush size")
            print("")
            print("Advanced Keys:")
            print("  T = Toggle text input mode (type tile numbers)")
            print("  C = Toggle advanced city tile mode")
            print("  WASD = Move camera")
            print("  Ctrl+S = Save tilemap")
            print("  F10 = Exit editor")
            print("")
            print("Text Input: Type tile number (0-13 for city subtypes in city mode)")
            
            # Set editor camera to current player position
            self.camera_x = self.game.player.rect.centerx
            self.camera_y = self.game.player.rect.centery
        else:
            print("Map Editor disabled")
            # Reset state when disabling
            self.is_dragging = False
            self.drag_start_tile = None
            self.drag_current_tile = None
            self.text_input_active = False
            self.text_input_buffer = ""
            self.advanced_city_mode = False
            self.save_message_timer = 0
            
        return self.enabled
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """Handle editor input events with text input support"""
        if not self.enabled:
            return False
            
        if event.type == pygame.KEYDOWN:
            if self.text_input_active:
                return self._handle_text_input(event)
            else:
                return self._handle_keydown(event)
        
        return False
    
    def _handle_keydown(self, event: pygame.event.Event) -> bool:
        """Handle keydown events for editor"""
        
        # Text input activation
        if event.key == pygame.K_t:
            self.text_input_active = True
            self.text_input_buffer = ""
            mode_str = "city subtype" if self.advanced_city_mode else "tile type"
            print(f"Text input mode: Enter {mode_str} number")
            return True
        
        # Advanced city mode toggle
        elif event.key == pygame.K_c:
            self.advanced_city_mode = not self.advanced_city_mode
            mode_str = "ADVANCED CITY" if self.advanced_city_mode else "BASIC"
            print(f"Switched to {mode_str} mode")
            if self.advanced_city_mode:
                self.selected_tile = Tile.CITY
                print("City mode: Use T key to select city subtypes (0-13)")
            return True
        
        # Tile selection keys (basic mode only)
        elif not self.advanced_city_mode:
            tile_map = {
                pygame.K_1: Tile.NATURE,
                pygame.K_2: Tile.CITY, 
                pygame.K_3: Tile.ROAD,
                pygame.K_4: Tile.NATURE_FLOWER,
                pygame.K_5: Tile.NATURE_ROCK,
                pygame.K_6: Tile.NATURE_BUSH,
                pygame.K_7: Tile.NATURE_LOG,
                pygame.K_8: Tile.NATURE_FLOWER_RED
            }
            
            if event.key in tile_map:
                self.selected_tile = tile_map[event.key]
                tile_name = self._get_tile_name(self.selected_tile)
                print(f"Selected tile: {tile_name}")
                return True
        
        # Other controls remain the same
        if event.key == pygame.K_SPACE:
            self.place_tile_at_crosshair()
            return True
        elif event.key == pygame.K_RETURN:
            self.toggle_drag_mode()
            return True
        elif event.key == pygame.K_b:
            self.brush_size = min(5, self.brush_size + 1)
            print(f"Brush size: {self.brush_size}")
            return True
        elif event.key == pygame.K_n:
            self.brush_size = max(1, self.brush_size - 1)
            print(f"Brush size: {self.brush_size}")
            return True
        elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
            self.save_tilemap()
            return True
        
        return False
    
    def _process_text_input(self):
        """Process text input to select tile type"""
        if not self.text_input_buffer:
            print("No input provided")
            return
        
        try:
            tile_number = int(self.text_input_buffer)
            
            if self.advanced_city_mode:
                # In advanced city mode, select city subtype
                if 0 <= tile_number <= 13:
                    self.selected_tile = Tile.CITY
                    self.selected_city_type = tile_number
                    city_type_name = self.city_tile_types.get(tile_number, f"CITY_{tile_number}")
                    print(f"Selected: CITY - {city_type_name}")
                else:
                    print(f"Invalid city tile type: {tile_number} (valid: 0-13)")
            else:
                # Normal mode, select basic tile type
                if 0 <= tile_number <= 8:
                    tile_values = [
                        Tile.NATURE, Tile.CITY, Tile.ROAD, Tile.NATURE_FLOWER,
                        Tile.NATURE_FLOWER_RED, Tile.NATURE_LOG, Tile.NATURE_BUSH,
                        Tile.NATURE_ROCK, Tile.BUILDING
                    ]
                    self.selected_tile = tile_values[tile_number]
                    tile_name = self.tile_names.get(tile_number, f"Tile_{tile_number}")
                    print(f"Selected tile: {tile_name}")
                else:
                    print(f"Invalid tile number: {tile_number} (valid: 0-8)")
        
        except ValueError:
            print(f"Invalid input: '{self.text_input_buffer}' - numbers only")

    def _handle_text_input(self, event: pygame.event.Event) -> bool:
        """Handle text input for tile selection"""
        if event.key == pygame.K_RETURN:
            # Process the input
            self._process_text_input()
            self.text_input_active = False
            self.text_input_buffer = ""
            return True
        
        elif event.key == pygame.K_ESCAPE or event.key == pygame.K_t:
            # Cancel text input
            self.text_input_active = False
            self.text_input_buffer = ""
            print("Text input cancelled")
            return True
        
        elif event.key == pygame.K_BACKSPACE:
            # Remove last character
            if self.text_input_buffer:
                self.text_input_buffer = self.text_input_buffer[:-1]
            return True
        
        else:
            # Add character to buffer (numbers only)
            char = event.unicode
            if char.isdigit() and len(self.text_input_buffer) < 3:  # Max 3 digits
                self.text_input_buffer += char
                return True
        
        return False
    
    def get_crosshair_tile_coords(self) -> Tuple[int, int]:
        """Get tile coordinates at the crosshair (screen center)"""
        screen_center_x = self.game.screen.get_width() // 2
        screen_center_y = self.game.screen.get_height() // 2
        
        # Convert screen coordinates to world coordinates
        world_x = screen_center_x + self.game.camera.offset.x
        world_y = screen_center_y + self.game.camera.offset.y
        
        # Convert to tile coordinates
        tile_size = 32
        tile_x = int(world_x // tile_size)
        tile_y = int(world_y // tile_size)
        
        return tile_x, tile_y
    
    def place_tile_at_crosshair(self):
        """Place a single tile at the crosshair position with advanced city support"""
        if not hasattr(self.game, 'map_generator'):
            print("No map generator available for editing")
            return
        
        tile_x, tile_y = self.get_crosshair_tile_coords()

        # Prevent editing outside map boundaries
        if (tile_x < 0 or tile_x >= self.game.map_generator.tilemap.width or
            tile_y < 0 or tile_y >= self.game.map_generator.tilemap.height):
            print(f"Cannot edit outside map boundaries. Tile ({tile_x}, {tile_y}) is out of range.")
            return
        
        # Strict boundary check - exit immediately if out of bounds
        if (tile_x < 0 or tile_x >= self.game.map_generator.tilemap.width or
            tile_y < 0 or tile_y >= self.game.map_generator.tilemap.height):
            return  # Do nothing if outside bounds

        # Place the tile (we know we're in bounds now)
        tile_value = self._get_tile_value(self.selected_tile)
        self.game.map_generator.tilemap.set_tile(tile_x, tile_y, tile_value)

        # If in advanced city mode, also set the city tile type
        if self.advanced_city_mode and tile_value == 1:  # CITY tile
            self.game.map_generator.tilemap.city_tile_grid[tile_y][tile_x] = self.selected_city_type
            city_type_name = self.city_tile_types.get(self.selected_city_type, f"CITY_{self.selected_city_type}")
            print(f"Placed {city_type_name} at tile ({tile_x}, {tile_y})")
        else:
            tile_name = self._get_tile_name(self.selected_tile)
            print(f"Placed {tile_name} at tile ({tile_x}, {tile_y})")

        # Regenerate the visual surface
        self._regenerate_background()
    
    def toggle_drag_mode(self):
        """Toggle drag selection mode"""
        if not self.is_dragging:
            # Start dragging
            self.is_dragging = True
            self.drag_start_tile = self.get_crosshair_tile_coords()
            self.drag_current_tile = self.drag_start_tile
            print(f"Drag mode started at tile {self.drag_start_tile}")
        else:
            # End dragging and fill area
            if self.drag_start_tile and self.drag_current_tile:
                self.fill_drag_area()
            self.is_dragging = False
            self.drag_start_tile = None
            self.drag_current_tile = None
            print("Drag mode ended")
    
    def fill_drag_area(self):
        """Fill the rectangular area between drag start and current position"""
        if not hasattr(self.game, 'map_generator'):
            return
        
        start_x, start_y = self.drag_start_tile
        end_x, end_y = self.drag_current_tile
        
        # Check if entire drag area is out of bounds
        if (max(start_x, end_x) < 0 or min(start_x, end_x) >= self.game.map_generator.tilemap.width or
            max(start_y, end_y) < 0 or min(start_y, end_y) >= self.game.map_generator.tilemap.height):
            return  # Entire area is out of bounds

        # Clamp to valid coordinates only
        min_x = max(0, min(start_x, end_x))
        max_x = min(self.game.map_generator.tilemap.width - 1, max(start_x, end_x))
        min_y = max(0, min(start_y, end_y))
        max_y = min(self.game.map_generator.tilemap.height - 1, max(start_y, end_y))

        # Additional check to prevent any out-of-bounds operations
        if (min_x >= self.game.map_generator.tilemap.width or 
            min_y >= self.game.map_generator.tilemap.height or
            max_x < 0 or max_y < 0):
            print("Drag area is completely outside map boundaries.")
            return
        
        tile_value = self._get_tile_value(self.selected_tile)
        tile_name = self._get_tile_name(self.selected_tile)
        tiles_filled = 0
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                self.game.map_generator.tilemap.set_tile(x, y, tile_value)
                # If in advanced city mode, also set the city tile type for each tile
                if self.advanced_city_mode and tile_value == 1:  # CITY tile
                    self.game.map_generator.tilemap.city_tile_grid[y][x] = self.selected_city_type
                tiles_filled += 1
        
        print(f"Filled {tiles_filled} tiles with {tile_name} in area ({min_x},{min_y}) to ({max_x},{max_y})")
        
        # Regenerate the visual surface
        self._regenerate_background()
    
    def update(self, dt: float):
        """Update editor camera and text input cursor"""
        if not self.enabled:
            return
            
        keys = pygame.key.get_pressed()
        
        # Move editor camera with WASD
        if keys[pygame.K_w]:
            self.camera_y -= self.camera_speed * dt
        if keys[pygame.K_s]:
            self.camera_y += self.camera_speed * dt
        if keys[pygame.K_a]:
            self.camera_x -= self.camera_speed * dt
        if keys[pygame.K_d]:
            self.camera_x += self.camera_speed * dt
        
        # Update game camera to follow editor position
        self.game.camera.offset.x = self.camera_x - self.game.screen.get_width() // 2
        self.game.camera.offset.y = self.camera_y - self.game.screen.get_height() // 2
        
        # Update drag current position if dragging
        if self.is_dragging:
            self.drag_current_tile = self.get_crosshair_tile_coords()
        
        # Update text cursor blinking
        if self.text_input_active:
            self.text_input_cursor_time += dt

        # Update text cursor blinking
        if self.text_input_active:
            self.text_input_cursor_time += dt

        # Update save notification timer
        if self.save_message_timer > 0:
            self.save_message_timer -= dt
    
    def _regenerate_background(self):
        """Regenerate background after tile edits"""
        if hasattr(self.game, 'map_generator'):
            tile_size = 32
            base_surface = self.game.map_generator._create_tile_surface()
            self.game.background = self.game._apply_tile_textures(
                base_surface, self.game.map_generator, tile_size
            )
            print("Background regenerated")
    
    def save_tilemap(self):
        """Save current tilemap state to file"""
        if not hasattr(self.game, 'map_generator') or not self.game.map_generator:
            print("No map generator available for saving")
            return
        
        try:
            # Create saves directory if it doesn't exist
            saves_dir = "saves"
            os.makedirs(saves_dir, exist_ok=True)
            
            # Get next map number
            map_number = self._get_next_map_number(saves_dir)
            
            # Extract tilemap data
            tilemap_data, tile_counts = self._extract_tilemap_data()
            
            # Prepare save data
            save_data = {
                "metadata": {
                    "map_number": map_number,
                    "save_time": datetime.now().isoformat(),
                    "total_tiles": sum(tile_counts.values()),
                    "tile_counts": tile_counts,
                    "editor_version": "1.0"
                },
                "map_info": {
                    "width": self.game.map_generator.tilemap.width,
                    "height": self.game.map_generator.tilemap.height,
                    "tile_size": 32
                },
                "tilemap": tilemap_data,
                "building_positions": [
                    {"x": x * 32, "y": y * 32} 
                    for x, y in getattr(self.game.map_generator, 'building_positions', [])
                ],
                "city_tile_data": self._extract_city_tile_data() if hasattr(self.game.map_generator.tilemap, 'city_tile_grid') else [],
                "path_tile_data": self._extract_path_tile_data() if hasattr(self.game.map_generator.tilemap, 'path_tile_grid') else [],
                "tile_legend": self._get_tile_legend()
            }
            
            # Save to file
            filename = f"new_map_{map_number}.json"
            filepath = os.path.join(saves_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2)

            
            
            # Regenerate background
            self._regenerate_background()
            
            print(f"Map saved as {filename}")
            print(f"Map #{map_number} - {tile_counts.get('CITY', 0)} city tiles, {tile_counts.get('NATURE', 0)} nature tiles")
            
        except Exception as e:
            print(f"Error saving tilemap: {e}")
        
        # Always show save notification
        self.save_message_timer = self.save_message_duration
        
    def _get_next_map_number(self, saves_dir: str) -> int:
        """Find the next available map number"""
        existing_numbers = []
        
        if os.path.exists(saves_dir):
            for filename in os.listdir(saves_dir):
                if filename.startswith("new_map_") and filename.endswith(".json"):
                    try:
                        # Extract number from filename like "new_map_5.json"
                        number_str = filename[8:-5]  # Remove "new_map_" and ".json"
                        existing_numbers.append(int(number_str))
                    except ValueError:
                        continue
        
        # Return next available number (starting from 1)
        return max(existing_numbers, default=0) + 1
    
    def _extract_tilemap_data(self) -> Tuple[List[List[int]], Dict[str, int]]:
        """Extract tilemap data and count tiles"""
        tilemap_data = []
        tile_counts = {}
        
        for y in range(self.game.map_generator.tilemap.height):
            row = []
            for x in range(self.game.map_generator.tilemap.width):
                tile = self.game.map_generator.tilemap.get_tile(x, y)
                if isinstance(tile, int):
                    tile_value = tile
                else:
                    tile_value = self._get_tile_value(tile)
                row.append(tile_value)
                
                # Count tiles
                tile_name = self.tile_names.get(tile_value, f"Unknown_{tile_value}")
                tile_counts[tile_name] = tile_counts.get(tile_name, 0) + 1
            tilemap_data.append(row)
        
        return tilemap_data, tile_counts
    
    def _get_tile_legend(self) -> Dict[str, str]:
        """Get tile type legend for save data"""
        return {str(k): v for k, v in self.tile_names.items()}
    
    def _draw_tile_reference_panel(self, screen: pygame.Surface, font: pygame.font.Font):
        """Draw a reference panel showing tile numbers and types"""
        if self.text_input_active:
            panel_width = 300
            panel_height = 200
            panel_x = screen.get_width() - panel_width - 20
            panel_y = 20
            
            # Background
            panel_bg = pygame.Surface((panel_width, panel_height))
            panel_bg.fill((20, 20, 40))
            panel_bg.set_alpha(200)
            screen.blit(panel_bg, (panel_x, panel_y))
            
            # Title
            title = "ADVANCED CITY TILES" if self.advanced_city_mode else "BASIC TILE TYPES"
            title_surf = font.render(title, True, (255, 255, 100))
            screen.blit(title_surf, (panel_x + 10, panel_y + 10))
            
            # List tiles
            y_offset = 35
            if self.advanced_city_mode:
                for i, name in self.city_tile_types.items():
                    if i <= 13:  # Show first 14 city types
                        color = (255, 255, 255) if i != self.selected_city_type else (100, 255, 100)
                        text = f"{i}: {name}"
                        text_surf = font.render(text, True, color)
                        screen.blit(text_surf, (panel_x + 15, panel_y + y_offset))
                        y_offset += 12
            else:
                for i, name in self.tile_names.items():
                    if i <= 8:
                        color = (255, 255, 255)
                        text = f"{i}: {name}"
                        text_surf = font.render(text, True, color)
                        screen.blit(text_surf, (panel_x + 15, panel_y + y_offset))
                        y_offset += 12

    def _draw_save_notification(self, screen: pygame.Surface, font: pygame.font.Font):
        """Draw the save notification message with fade effect"""
        if self.save_message_timer <= 0:
            return
        
        # Calculate alpha based on remaining time
        if self.save_message_timer > self.save_message_fade_start:
            # Full opacity phase
            alpha = 255
        else:
            # Fading phase
            fade_progress = self.save_message_timer / self.save_message_fade_start
            alpha = int(255 * fade_progress)
        
        # Create the message text
        message_text = "MAP SAVED!"
        text_surface = font.render(message_text, True, (100, 255, 100))  # Bright green
        
        # Position at center-top of screen
        screen_width = screen.get_width()
        text_x = (screen_width - text_surface.get_width()) // 2
        text_y = 50
        
        # Create background for the text
        padding = 20
        bg_width = text_surface.get_width() + padding * 2
        bg_height = text_surface.get_height() + padding
        bg_x = text_x - padding
        bg_y = text_y - padding // 2
        
        # Draw background with alpha
        bg_surface = pygame.Surface((bg_width, bg_height))
        bg_surface.fill((0, 50, 0))  # Dark green background
        bg_surface.set_alpha(min(180, alpha))
        screen.blit(bg_surface, (bg_x, bg_y))
        
        # Draw border
        border_color = (*[int(100 * alpha / 255) for _ in range(3)], alpha)
        pygame.draw.rect(screen, (0, 255, 0), (bg_x, bg_y, bg_width, bg_height), 2)
        
        # Apply alpha to text and draw
        text_surface.set_alpha(alpha)
        screen.blit(text_surface, (text_x, text_y))

    def draw_ui(self, screen: pygame.Surface, font_small: pygame.font.Font, 
            font_smallest: pygame.font.Font):
        """Draw enhanced editor UI with text input support"""
        if not self.enabled:
            return
        
        # Prepare all text surfaces
        texts_to_render = []
        
        # Editor header with mode indicator
        mode_indicator = " [CITY]" if self.advanced_city_mode else ""
        texts_to_render.append(font_small.render(f"MAP EDITOR{mode_indicator}", True, (255, 255, 0)))
        
        # Current settings
        if self.advanced_city_mode:
            city_type_name = self.city_tile_types.get(self.selected_city_type, f"CITY_{self.selected_city_type}")
            texts_to_render.append(font_small.render(f"City Type: {city_type_name}", True, (255, 255, 255)))
        else:
            tile_name = self._get_tile_name(self.selected_tile)
            texts_to_render.append(font_small.render(f"Tile: {tile_name}", True, (255, 255, 255)))
        
        texts_to_render.append(font_small.render(f"Brush: {self.brush_size}", True, (255, 255, 255)))
        
        # Text input status
        if self.text_input_active:
            input_mode = "city subtype" if self.advanced_city_mode else "tile type"
            texts_to_render.append(font_small.render(f"INPUT MODE: {input_mode}", True, (255, 100, 255)))
            
            # Show current input with blinking cursor
            cursor = "|" if (self.text_input_cursor_time % 1.0) < 0.5 else " "
            input_display = f"Number: {self.text_input_buffer}{cursor}"
            texts_to_render.append(font_small.render(input_display, True, (255, 150, 255)))
        
        # Drag mode status
        if self.is_dragging:
            texts_to_render.append(font_small.render("DRAG MODE ACTIVE", True, (255, 100, 100)))
            if self.drag_start_tile:
                drag_info = f"From: {self.drag_start_tile}"
                texts_to_render.append(font_smallest.render(drag_info, True, (255, 150, 150)))
        
        # Camera position
        texts_to_render.append(font_smallest.render(
            f"Cam: ({int(self.camera_x)}, {int(self.camera_y)})", 
            True, (200, 200, 200)
        ))
        
        # Instructions
        instructions = [
            "WASD: Move camera",
            "T: Text input mode",
            "C: Toggle city mode" if not self.advanced_city_mode else "C: Exit city mode",
            "1-8: Select tile (basic mode)" if not self.advanced_city_mode else "Text input: Select city subtype",
            "SPACE: Place tile",
            "ENTER: Drag selection",
            "B/N: Brush size", 
            "Ctrl+S: Save",
            "F10: Exit editor"
        ]
        
        for instruction in instructions:
            texts_to_render.append(font_smallest.render(instruction, True, (200, 200, 200)))
        
        # Calculate UI box size
        max_width = max(text.get_width() for text in texts_to_render)
        total_height = sum(text.get_height() for text in texts_to_render) + len(texts_to_render) * 3
        
        # Draw UI background
        padding = 15
        box_width = max_width + padding * 2
        box_height = total_height + padding * 2
        
        ui_bg = pygame.Surface((box_width, box_height))
        ui_bg.fill((0, 0, 0))
        ui_bg.set_alpha(180)
        screen.blit(ui_bg, (10, 10))
        
        # Draw all texts
        y_offset = 15
        for text in texts_to_render:
            screen.blit(text, (15, 10 + y_offset))
            y_offset += text.get_height() + 3
        
        # Draw tile reference panel
        self._draw_tile_reference_panel(screen, font_smallest)

        # Draw save notification if active
        if self.save_message_timer > 0:
            self._draw_save_notification(screen, font_small)
    
    def draw_crosshair(self, screen: pygame.Surface, font_smallest: pygame.font.Font):
        """Draw crosshair and coordinate info in editor mode"""
        if not self.enabled:
            return
        
        # Get screen center
        center_x = screen.get_width() // 2
        center_y = screen.get_height() // 2
        
        # Calculate world coordinates at crosshair
        world_x = center_x + self.game.camera.offset.x
        world_y = center_y + self.game.camera.offset.y
        
        # Calculate tile coordinates
        tile_size = 32
        tile_x = int(world_x // tile_size)
        tile_y = int(world_y // tile_size)

       # Check bounds for crosshair color
        out_of_bounds = (tile_x < 0 or tile_x >= self.game.map_generator.tilemap.width or
                        tile_y < 0 or tile_y >= self.game.map_generator.tilemap.height)

        if out_of_bounds:
            crosshair_color = (100, 100, 100)  # Dark gray for out of bounds
        elif self.is_dragging:
            crosshair_color = (255, 255, 0)    # Yellow when dragging
        else:
            crosshair_color = (255, 0, 0)      # Red for normal
        line_length = 15
        line_width = 2
        
        # Horizontal line
        pygame.draw.line(screen, crosshair_color, 
                        (center_x - line_length, center_y), 
                        (center_x + line_length, center_y), line_width)
        
        # Vertical line
        pygame.draw.line(screen, crosshair_color,
                        (center_x, center_y - line_length),
                        (center_x, center_y + line_length), line_width)
        
        # Draw tile highlight square
        tile_screen_x = (tile_x * tile_size) - self.game.camera.offset.x
        tile_screen_y = (tile_y * tile_size) - self.game.camera.offset.y
        
        tile_rect = pygame.Rect(tile_screen_x, tile_screen_y, tile_size, tile_size)
        pygame.draw.rect(screen, crosshair_color, tile_rect, 2)
        
        # Draw drag selection area if dragging
        if self.is_dragging and self.drag_start_tile and self.drag_current_tile:
            self.draw_drag_selection(screen)
        
        # Draw coordinate info
        bounds_status = " [OUT OF BOUNDS]" if out_of_bounds else ""
        coord_text = f"World: ({int(world_x)}, {int(world_y)}) | Tile: ({tile_x}, {tile_y}){bounds_status}"
        coord_surface = font_smallest.render(coord_text, True, (255, 255, 255))
        
        # Position text below crosshair with background
        text_x = center_x - coord_surface.get_width() // 2
        text_y = center_y + 30
        
        # Text background
        text_bg = pygame.Surface((coord_surface.get_width() + 10, coord_surface.get_height() + 4))
        text_bg.fill((0, 0, 0))
        text_bg.set_alpha(180)
        screen.blit(text_bg, (text_x - 5, text_y - 2))
        
        # Draw text
        screen.blit(coord_surface, (text_x, text_y))
    
    def draw_drag_selection(self, screen: pygame.Surface):
        """Draw the drag selection rectangle"""
        if not self.drag_start_tile or not self.drag_current_tile:
            return
        
        tile_size = 32
        start_x, start_y = self.drag_start_tile
        end_x, end_y = self.drag_current_tile
        
        # Calculate screen positions
        start_screen_x = (start_x * tile_size) - self.game.camera.offset.x
        start_screen_y = (start_y * tile_size) - self.game.camera.offset.y
        end_screen_x = (end_x * tile_size) - self.game.camera.offset.x
        end_screen_y = (end_y * tile_size) - self.game.camera.offset.y
        
        # Calculate rectangle bounds
        left = min(start_screen_x, end_screen_x)
        top = min(start_screen_y, end_screen_y)
        width = abs(end_screen_x - start_screen_x) + tile_size
        height = abs(end_screen_y - start_screen_y) + tile_size
        
        # Draw selection rectangle
        selection_rect = pygame.Rect(left, top, width, height)
        pygame.draw.rect(screen, (255, 255, 0), selection_rect, 3)
        
        # Draw semi-transparent fill
        fill_surface = pygame.Surface((width, height))
        fill_surface.fill((255, 255, 0))
        fill_surface.set_alpha(50)
        screen.blit(fill_surface, (left, top))

    def _extract_city_tile_data(self) -> List[List[Optional[int]]]:
        """Extract city tile data for saving"""
        city_tile_data = []
        for y in range(self.game.map_generator.tilemap.height):
            row = []
            for x in range(self.game.map_generator.tilemap.width):
                city_type = self.game.map_generator.tilemap.city_tile_grid[y][x]
                row.append(city_type)
            city_tile_data.append(row)
        return city_tile_data

    def _extract_path_tile_data(self) -> List[List[Optional[str]]]:
        """Extract path tile data for saving"""
        path_tile_data = []
        for y in range(self.game.map_generator.tilemap.height):
            row = []
            for x in range(self.game.map_generator.tilemap.width):
                path_type = self.game.map_generator.tilemap.path_tile_grid[y][x]
                row.append(path_type)
            path_tile_data.append(row)
        return path_tile_data


class TilemapLoader:
    """Utility class for loading saved tilemaps"""
    
    @staticmethod
    def load_tilemap(filepath: str) -> Optional[Dict[str, Any]]:
        """Load a saved tilemap from file"""
        try:
            with open(filepath, 'r') as f:
                save_data = json.load(f)
            return save_data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading tilemap from {filepath}: {e}")
            return None
    
    @staticmethod
    def list_saved_maps(saves_dir: str = "saves") -> List[Dict[str, Any]]:
        """List all saved maps with their metadata"""
        if not os.path.exists(saves_dir):
            return []
        
        saved_maps = []
        
        # Look for new_map_*.json files
        for filename in os.listdir(saves_dir):
            if filename.startswith("new_map_") and filename.endswith(".json"):
                filepath = os.path.join(saves_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        save_data = json.load(f)
                    
                    # Extract map info
                    map_info = {
                        'filename': filename,
                        'filepath': filepath,
                        'map_number': save_data.get('metadata', {}).get('map_number', 0),
                        'save_time': save_data.get('metadata', {}).get('save_time', 'Unknown'),
                        'width': save_data.get('map_info', {}).get('width', 0),
                        'height': save_data.get('map_info', {}).get('height', 0),
                        'total_tiles': save_data.get('metadata', {}).get('total_tiles', 0),
                        'tile_counts': save_data.get('metadata', {}).get('tile_counts', {}),
                        'num_buildings': len(save_data.get('building_positions', []))
                    }
                    saved_maps.append(map_info)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error reading map info from {filename}: {e}")
                    continue
        
        # Sort by map number
        saved_maps.sort(key=lambda x: x['map_number'])
        return saved_maps
    
    @staticmethod
    def print_available_maps(saves_dir: str = "saves"):
        """Print a formatted list of available maps"""
        maps = TilemapLoader.list_saved_maps(saves_dir)
        
        if not maps:
            print("No saved maps found in saves/ directory")
            return
        
        print("\n=== AVAILABLE SAVED MAPS ===")
        print(f"{'Map':<6} {'Size':<10} {'Buildings':<10} {'Saved':<20}")
        print("-" * 50)
        
        for map_info in maps:
            map_num = map_info['map_number']
            size = f"{map_info['width']}x{map_info['height']}"
            buildings = map_info['num_buildings']
            
            # Format save time
            save_time = map_info['save_time']
            if save_time != 'Unknown':
                try:
                    dt = datetime.fromisoformat(save_time.replace('Z', '+00:00'))
                    save_time = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            print(f"{map_num:<6} {size:<10} {buildings:<10} {save_time:<20}")
        
        print(f"\nFound {len(maps)} saved maps")
    
    @staticmethod
    def load_map_by_number(map_number: int, saves_dir: str = "saves") -> Optional[Dict[str, Any]]:
        """Load a map by its number"""
        filename = f"new_map_{map_number}.json"
        filepath = os.path.join(saves_dir, filename)
        return TilemapLoader.load_tilemap(filepath)
    
    @staticmethod
    def apply_loaded_tilemap(game_ref, save_data: Dict[str, Any]) -> bool:
        """Apply a loaded tilemap to the game"""
        try:
            if not hasattr(game_ref, 'map_generator'):
                print("No map generator available")
                return False
            
            tilemap_data = save_data.get('tilemap')
            if not tilemap_data:
                print("No tilemap data found in save file")
                return False
            
            # Apply tilemap data
            for y, row in enumerate(tilemap_data):
                for x, tile_value in enumerate(row):
                    if (0 <= x < game_ref.map_generator.tilemap.width and 
                        0 <= y < game_ref.map_generator.tilemap.height):
                        game_ref.map_generator.tilemap.set_tile(x, y, tile_value)
            
            # Update building positions if available
            building_positions = save_data.get('building_positions', [])
            game_ref.map_generator.building_positions = [
                (pos['x'] // 32, pos['y'] // 32) for pos in building_positions
            ]
            
            # Regenerate background
            tile_size = 32
            base_surface = game_ref.map_generator._create_tile_surface()
            game_ref.background = game_ref._apply_tile_textures(
                base_surface, game_ref.map_generator, tile_size
            )
            
            map_number = save_data.get('metadata', {}).get('map_number', 'Unknown')
            print(f"Successfully loaded Map #{map_number} with {len(tilemap_data)}x{len(tilemap_data[0])} tiles")
            return True
            
        except Exception as e:
            print(f"Error applying loaded tilemap: {e}")
            return False
        



class MapGenerationMenu:
    """Menu system for choosing map generation options"""
    
    @staticmethod
    def show_generation_menu():
        return "random", None
            
    @staticmethod
    def list_available_maps():
        """List all available saved maps"""
        saves_dir = "saves"
        available_maps = []
        
        if not os.path.exists(saves_dir):
            return available_maps
        
        for filename in os.listdir(saves_dir):
            if filename.startswith("new_map_") and filename.endswith(".json"):
                try:
                    number_str = filename[8:-5]  # Remove "new_map_" and ".json"
                    map_number = int(number_str)
                    available_maps.append(f"Map #{map_number} ({filename})")
                except ValueError:
                    continue
        
        return available_maps
    
    @staticmethod
    def _handle_load_choice() -> Tuple[str, Optional[int]]:
        """Handle loading a specific map"""
        maps = TilemapLoader.list_saved_maps()
        
        if not maps:
            print("No saved maps available. Falling back to random generation.")
            return ("random", None)
        
        while True:
            try:
                map_input = input("Enter map number to load: ").strip()
                map_number = int(map_input)
                
                # Check if map exists
                if any(m['map_number'] == map_number for m in maps):
                    return ("load", map_number)
                else:
                    available_numbers = [m['map_number'] for m in maps]
                    print(f"Map #{map_number} not found. Available maps: {available_numbers}")
                    
            except ValueError:
                print("Please enter a valid map number.")
            except KeyboardInterrupt:
                print("\nCancelled. Falling back to random generation.")
                return ("random", None)