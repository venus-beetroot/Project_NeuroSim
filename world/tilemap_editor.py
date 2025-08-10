import pygame
import json
import os
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from world.map_generator import TileType, Tile


class TilemapEditor:
    """Developer tool for editing tilemaps in real-time"""
    
    def __init__(self, game_ref):
        self.game = game_ref
        self.enabled = False
        
        from world.map_generator import TileType  # Import at the top of the file
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
        
        # Tile names mapping for display
        self.tile_names = {
            0: "NATURE", 1: "CITY", 2: "ROAD", 3: "NATURE_FLOWER",
            4: "NATURE_FLOWER_RED", 5: "NATURE_LOG", 6: "NATURE_BUSH", 
            7: "NATURE_ROCK", 8: "BUILDING"
        }
        
    def _get_tile_value(self, tile) -> int:
        """Safely extract tile value from either enum or int"""
        print(f"DEBUG: _get_tile_value called with: {tile}, type: {type(tile)}")
        if isinstance(tile, int):
            return tile
        elif hasattr(tile, 'value'):
            return tile.value
        else:
            return 0  # Default to NATURE
            
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
            print("Map Editor enabled - Use WASD to move camera")
            print("Keys: 1=Nature, 2=City, 3=Road, 4=Flower, 5=Rock, 6=Bush, 7=Log")
            print("SPACE = place tile at crosshair, ENTER = start/end drag selection")
            print("B key = increase brush size, N key = decrease brush size")
            print("Ctrl+S key = save current tilemap")
            
            # Set editor camera to current player position
            self.camera_x = self.game.player.rect.centerx
            self.camera_y = self.game.player.rect.centery
        else:
            print("Map Editor disabled")
            # Reset drag state when disabling
            self.is_dragging = False
            self.drag_start_tile = None
            self.drag_current_tile = None
            
        return self.enabled
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """
        Handle editor input events
        Returns True if event was consumed by editor
        """
        if not self.enabled:
            return False
            
        if event.type == pygame.KEYDOWN:
            return self._handle_keydown(event)
            
        return False
    
    def _handle_keydown(self, event: pygame.event.Event) -> bool:
        """Handle keydown events for editor"""
        # Tile selection keys
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
        
        elif event.key == pygame.K_SPACE:
            # Place single tile at crosshair
            self.place_tile_at_crosshair()
            return True
        
        elif event.key == pygame.K_RETURN:
            # Toggle drag mode
            self.toggle_drag_mode()
            return True
        
        elif event.key == pygame.K_b:
            self.brush_size = min(5, self.brush_size + 1)
            print(f"Brush size: {self.brush_size}")
            return True
        
        elif event.key == pygame.K_n:  # N for decrease brush size
            self.brush_size = max(1, self.brush_size - 1)
            print(f"Brush size: {self.brush_size}")
            return True
        
        elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
            self.save_tilemap()
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
        """Place a single tile at the crosshair position"""
        if not hasattr(self.game, 'map_generator'):
            print("No map generator available for editing")
            return
        
        tile_x, tile_y = self.get_crosshair_tile_coords()
        
        if (0 <= tile_x < self.game.map_generator.tilemap.width and 
            0 <= tile_y < self.game.map_generator.tilemap.height):
            
            tile_value = self._get_tile_value(self.selected_tile)
            tile_name = self._get_tile_name(self.selected_tile)
            
            self.game.map_generator.tilemap.set_tile(tile_x, tile_y, tile_value)
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
        
        # Ensure we have valid coordinates
        min_x = max(0, min(start_x, end_x))
        max_x = min(self.game.map_generator.tilemap.width - 1, max(start_x, end_x))
        min_y = max(0, min(start_y, end_y))
        max_y = min(self.game.map_generator.tilemap.height - 1, max(start_y, end_y))
        
        tile_value = self._get_tile_value(self.selected_tile)
        tile_name = self._get_tile_name(self.selected_tile)
        tiles_filled = 0
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                self.game.map_generator.tilemap.set_tile(x, y, tile_value)
                tiles_filled += 1
        
        print(f"Filled {tiles_filled} tiles with {tile_name} in area ({min_x},{min_y}) to ({max_x},{max_y})")
        
        # Regenerate the visual surface
        self._regenerate_background()
    
    def update(self, dt: float):
        """Update editor camera based on input"""
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
        """Save the current tilemap state with metadata"""
        if not hasattr(self.game, 'map_generator'):
            print("No map generator to save from")
            return
        
        # Create saves directory if it doesn't exist
        saves_dir = "saves"
        os.makedirs(saves_dir, exist_ok=True)
        
        # Get current tilemap data and statistics
        tilemap_data, tile_counts = self._extract_tilemap_data()
        
        # Create comprehensive save data
        save_data = {
            "metadata": {
                "save_time": datetime.now().isoformat(),
                "version": "0.8.2",
                "total_tiles": self.game.map_generator.tilemap.width * self.game.map_generator.tilemap.height,
                "tile_counts": tile_counts
            },
            "map_info": {
                "width": self.game.map_generator.tilemap.width,
                "height": self.game.map_generator.tilemap.height,
                "tile_size": 32,
                "map_pixel_width": self.game.map_size,
                "map_pixel_height": self.game.map_size
            },
            "building_positions": [
                {"x": pos[0] * 32, "y": pos[1] * 32} 
                for pos in self.game.map_generator.building_positions
            ],
            "tilemap": tilemap_data,
            "tile_legend": self._get_tile_legend()
        }
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"custom_map_{timestamp}.json"
        filepath = os.path.join(saves_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"Tilemap saved to: {filepath}")
        print(f"Map size: {self.game.map_generator.tilemap.width}x{self.game.map_generator.tilemap.height}")
        print(f"Tile counts: {tile_counts}")
    
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
    
    def draw_ui(self, screen: pygame.Surface, font_small: pygame.font.Font, 
            font_smallest: pygame.font.Font):
        """Draw editor UI overlay"""
        if not self.enabled:
            return
        
        # Prepare all text surfaces
        texts_to_render = []
        
        # Editor header
        texts_to_render.append(font_small.render("MAP EDITOR", True, (255, 255, 0)))
        
        # Current settings
        tile_name = self._get_tile_name(self.selected_tile)
        texts_to_render.append(font_small.render(f"Tile: {tile_name}", True, (255, 255, 255)))
        texts_to_render.append(font_small.render(f"Brush: {self.brush_size}", True, (255, 255, 255)))
        
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
            "1-8: Select tile type",
            "SPACE: Place tile at crosshair",
            "ENTER: Start/End drag selection",
            "B/N: Change brush size", 
            "Ctrl+S: Save tilemap",
            "F10: Exit editor"
        ]
        
        for instruction in instructions:
            texts_to_render.append(font_smallest.render(instruction, True, (200, 200, 200)))
        
        # Calculate UI box size
        max_width = max(text.get_width() for text in texts_to_render)
        total_height = sum(text.get_height() for text in texts_to_render) + len(texts_to_render) * 5
        
        # Draw UI background
        padding = 20
        box_width = max_width + padding * 2
        box_height = total_height + padding * 2
        
        ui_bg = pygame.Surface((box_width, box_height))
        ui_bg.fill((0, 0, 0))
        ui_bg.set_alpha(180)
        screen.blit(ui_bg, (10, 10))
        
        # Draw all texts
        y_offset = 20
        for text in texts_to_render:
            screen.blit(text, (20, 10 + y_offset))
            y_offset += text.get_height() + 5
    
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
        
        # Draw crosshair lines
        crosshair_color = (255, 0, 0) if not self.is_dragging else (255, 255, 0)  # Yellow when dragging
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
        coord_text = f"World: ({int(world_x)}, {int(world_y)}) | Tile: ({tile_x}, {tile_y})"
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
    def list_saved_tilemaps(saves_dir: str = "saves") -> List[str]:
        """List all saved tilemap files"""
        if not os.path.exists(saves_dir):
            return []
        
        tilemap_files = []
        for filename in os.listdir(saves_dir):
            if filename.startswith("custom_map_") and filename.endswith(".json"):
                tilemap_files.append(os.path.join(saves_dir, filename))
        
        return sorted(tilemap_files)
    
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
            
            # Regenerate background
            tile_size = 32
            base_surface = game_ref.map_generator._create_tile_surface()
            game_ref.background = game_ref._apply_tile_textures(
                base_surface, game_ref.map_generator, tile_size
            )
            
            print(f"Successfully loaded tilemap with {len(tilemap_data)}x{len(tilemap_data[0])} tiles")
            return True
            
        except Exception as e:
            print(f"Error applying loaded tilemap: {e}")
            return False