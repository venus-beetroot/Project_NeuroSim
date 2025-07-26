import pygame
import random
import os
import math
from enum import Enum
from typing import List, Tuple, Optional
import datetime
from player import Player
import app
import npc
from camera import Camera
import building 
from building import Building
from ai import get_ai_response
from ui_utils import draw_text_box

class GameState(Enum):
    START_SCREEN = "start_screen"
    PLAYING = "playing"
    INTERACTING = "interacting"
    SETTINGS = "settings"


class ChatManager:
    """Handles all chat-related functionality"""
    
    def __init__(self, font_chat, font_small):  # Fixed: __init__ not **init**
        self.font_chat = font_chat
        self.font_small = font_small
        self.scroll_offset = 0
        self.cooldown_duration = 3000
        self.chat_cooldown = 0
        self.message = ""
        
        # NPC typing variables
        self.typing_active = False
        self.letter_timer = None
        self.response_start_time = None
        self.current_response = ""
        self.dialogue_index = 0
        self.live_message = ""
        self.input_block_time = None
    
    def update_cooldown(self, delta_time: int):
        """Update chat cooldown timer"""
        if self.chat_cooldown > 0:
            self.chat_cooldown -= delta_time
            if self.chat_cooldown < 0:
                self.chat_cooldown = 0
    
    def start_typing_animation(self, response_text: str):
        """Start the typing animation for NPC response"""
        self.typing_active = True
        self.response_start_time = pygame.time.get_ticks() + 2000
        self.current_response = ""
        self.dialogue_index = 0
        self.live_message = ""
        self.letter_timer = None
    
    def update_typing_animation(self, npc_dialogue: str) -> bool:
        """Update typing animation. Returns True if finished typing."""
        if not self.typing_active:
            return False
            
        current_time = pygame.time.get_ticks()
        
        if current_time < self.response_start_time:
            return False
            
        if self.letter_timer is None:
            self.letter_timer = current_time + 30
            
        if current_time >= self.letter_timer:
            dialogue_text = npc_dialogue.content if hasattr(npc_dialogue, "content") else str(npc_dialogue)
            
            if self.dialogue_index < len(dialogue_text):
                letter = dialogue_text[self.dialogue_index]
                self.current_response += letter
                self.dialogue_index += 1
                self.live_message = self.current_response
                
                # Calculate delay based on punctuation
                base_delay = 30
                extra_delay = 0
                if letter in [",", ";"]:
                    extra_delay = 100
                elif letter in [".", "!", "?"]:
                    extra_delay = 150
                    
                self.letter_timer = current_time + base_delay + extra_delay
            else:
                # Finished typing
                self.typing_active = False
                self.letter_timer = None
                self.response_start_time = None
                self.live_message = ""
                self.input_block_time = current_time + 500
                return True
        
        return False
    
    def can_send_message(self) -> bool:
        """Check if player can send a message"""
        current_time = pygame.time.get_ticks()
        
        # Clear expired input block
        if self.input_block_time and current_time >= self.input_block_time:
            self.input_block_time = None
            
        return (self.chat_cooldown <= 0 and 
                self.message.strip() != "" and 
                not self.typing_active and 
                not self.input_block_time)
    
    def send_message(self, current_npc) -> str:
        """Send message and return the message that was sent"""
        if not self.can_send_message():
            return ""
            
        sent_message = self.message
        current_npc.chat_history.append(("player", sent_message))
        self.chat_cooldown = self.cooldown_duration
        self.message = ""
        return sent_message
    
    def handle_scroll(self, direction: int, total_lines: int, visible_lines: int):
        """Handle chat scroll wheel input"""
        self.scroll_offset -= direction
        max_offset = max(0, total_lines - visible_lines)
        self.scroll_offset = max(0, min(self.scroll_offset, max_offset))


class StartScreen:
    """Handles the start screen with wallpaper and menu buttons"""
    
    def __init__(self, screen, font_large, font_small):
        self.screen = screen
        self.font_large = font_large
        self.font_small = font_small
        
        # Create or load wallpaper
        self.wallpaper = self._create_wallpaper()
        
        # Button properties
        self.button_width = 300
        self.button_height = 60
        self.button_spacing = 20
        
        # Calculate button positions (centered)
        center_x = app.WIDTH // 2
        start_y = app.HEIGHT // 2 + 50
        
        self.buttons = {
            "start": pygame.Rect(center_x - self.button_width//2, start_y, 
                               self.button_width, self.button_height),
            "settings": pygame.Rect(center_x - self.button_width//2, 
                                  start_y + self.button_height + self.button_spacing,
                                  self.button_width, self.button_height),
            "quit": pygame.Rect(center_x - self.button_width//2, 
                              start_y + 2*(self.button_height + self.button_spacing),
                              self.button_width, self.button_height)
        }
        
        # Button hover states
        self.hovered_button = None
        
        # Loading animation variables
        self.loading = False
        self.loading_button = None
        self.loading_start_time = 0
        self.loading_duration = 1500  # 1.5 seconds
        self.loading_dots = 0
        self.loading_dot_timer = 0
        
        # Animation variables
        self.title_pulse = 0
        self.particle_timer = 0
        self.particles = []
    
    def _create_wallpaper(self):
        """Load wallpaper from assets folder with fallback"""
        try:
            # Try to load wallpaper from assets
            wallpaper_path = os.path.join("assets", "loadingscr.png")
            wallpaper = pygame.image.load(wallpaper_path)
            
            # Scale to fit screen while maintaining aspect ratio
            wallpaper = self._scale_wallpaper_to_fit(wallpaper)
            
            print(f"Loaded wallpaper from: {wallpaper_path}")
            return wallpaper
            
        except (pygame.error, FileNotFoundError) as e:
            print(f"Could not load loadingscr.png from assets folder: {e}")
            print("Generating fallback wallpaper...")
            return self._create_fallback_wallpaper()
    
    def _scale_wallpaper_to_fit(self, wallpaper):
        """Scale wallpaper to fit screen while maintaining aspect ratio"""
        wallpaper_width, wallpaper_height = wallpaper.get_size()
        screen_width, screen_height = app.WIDTH, app.HEIGHT
        
        # Calculate scaling factors
        scale_x = screen_width / wallpaper_width
        scale_y = screen_height / wallpaper_height
        
        # Use the larger scale to ensure full coverage
        scale = max(scale_x, scale_y)
        
        # Calculate new dimensions
        new_width = int(wallpaper_width * scale)
        new_height = int(wallpaper_height * scale)
        
        # Scale the wallpaper
        scaled_wallpaper = pygame.transform.scale(wallpaper, (new_width, new_height))
        
        # Create a surface for the final wallpaper
        final_wallpaper = pygame.Surface((screen_width, screen_height))
        
        # Center the scaled wallpaper
        x_offset = (screen_width - new_width) // 2
        y_offset = (screen_height - new_height) // 2
        
        final_wallpaper.blit(scaled_wallpaper, (x_offset, y_offset))
        
        return final_wallpaper
    
    def _create_fallback_wallpaper(self):
        """Create a fallback wallpaper when PNG is not available"""
        wallpaper = pygame.Surface((app.WIDTH, app.HEIGHT))
        
        # Create a gradient background
        for y in range(app.HEIGHT):
            # Create a nice gradient from dark blue to lighter blue
            progress = y / app.HEIGHT
            r = int(20 + (60 * progress))
            g = int(30 + (80 * progress))
            b = int(80 + (120 * progress))
            color = (min(255, r), min(255, g), min(255, b))
            pygame.draw.line(wallpaper, color, (0, y), (app.WIDTH, y))
        
        # Add some decorative elements (optional)
        self._add_decorative_elements(wallpaper)
        
        return wallpaper
    
    def _add_decorative_elements(self, surface):
        """Add decorative elements to the wallpaper"""
        # Add some semi-transparent circles for atmosphere
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        
        for _ in range(20):
            x = random.randint(0, app.WIDTH)
            y = random.randint(0, app.HEIGHT)
            radius = random.randint(30, 100)
            alpha = random.randint(10, 30)
            color = (255, 255, 255, alpha)
            
            # Create a temporary surface for the circle
            circle_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, color, (radius, radius), radius)
            overlay.blit(circle_surf, (x-radius, y-radius))
        
        surface.blit(overlay, (0, 0))
    
    def update(self, mouse_pos):
        """Update start screen animations and hover states"""
        # Update title pulse animation
        self.title_pulse += 0.1
        
        # Update loading animation
        if self.loading:
            current_time = pygame.time.get_ticks()
            
            # Update loading dots animation
            self.loading_dot_timer += 1
            if self.loading_dot_timer > 20:  # Change dots every 20 frames
                self.loading_dot_timer = 0
                self.loading_dots = (self.loading_dots + 1) % 4
            
            # Check if loading is complete
            if current_time - self.loading_start_time > self.loading_duration:
                return self._finish_loading()
        
        # Only update hover state if not loading
        if not self.loading:
            self.hovered_button = None
            for button_name, button_rect in self.buttons.items():
                if button_rect.collidepoint(mouse_pos):
                    self.hovered_button = button_name
                    break
        
        # Update floating particles
        self.particle_timer += 1
        if self.particle_timer > 30:  # Add new particle every 30 frames
            self.particle_timer = 0
            self.particles.append({
                'x': random.randint(0, app.WIDTH),
                'y': app.HEIGHT + 10,
                'speed': random.uniform(0.5, 2.0),
                'size': random.randint(2, 5),
                'alpha': random.randint(100, 200)
            })
        
        # Update existing particles
        for particle in self.particles[:]:
            particle['y'] -= particle['speed']
            particle['alpha'] -= 1
            if particle['alpha'] <= 0 or particle['y'] < -10:
                self.particles.remove(particle)
    
    def handle_click(self, mouse_pos):
        """Handle mouse clicks on buttons"""
        # Don't handle clicks if already loading
        if self.loading:
            return None
            
        for button_name, button_rect in self.buttons.items():
            if button_rect.collidepoint(mouse_pos):
                # Start loading animation
                self.start_loading(button_name)
                return None  # Don't return the action immediately
        return None
    
    def start_loading(self, button_name):
        """Start the loading animation for a button"""
        self.loading = True
        self.loading_button = button_name
        self.loading_start_time = pygame.time.get_ticks()
        self.loading_dots = 0
        self.loading_dot_timer = 0

    def _finish_loading(self):
        """Finish loading and return the button action"""
        button_action = self.loading_button
        self.loading = False
        self.loading_button = None
        return button_action  # Return the action to be handled by the game
    
    def draw(self):
        """Draw the complete start screen"""
        # Draw wallpaper
        self.screen.blit(self.wallpaper, (0, 0))
        
        # Draw floating particles
        self._draw_particles()
        
        # Draw title with pulse effect
        self._draw_title()
        
        # Draw subtitle
        self._draw_subtitle()
        
        # Draw menu buttons
        self._draw_buttons()
        
        # Draw version info
        self._draw_version_info()
    
    def _draw_particles(self):
        """Draw floating particles for atmosphere"""
        for particle in self.particles:
            color = (255, 255, 255, particle['alpha'])
            # Create a small surface for the particle
            particle_surf = pygame.Surface((particle['size']*2, particle['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, color, (particle['size'], particle['size']), particle['size'])
            self.screen.blit(particle_surf, (particle['x']-particle['size'], particle['y']-particle['size']))
    
    def _draw_title(self):
        """Draw the main game title with pulse effect"""
        title_text = "PROJECT NEUROSIM"
        
        # Create pulse effect
        pulse_scale = 1.0 + 0.1 * math.sin(self.title_pulse)
        
        # Create title surface
        title_surf = self.font_large.render(title_text, True, (255, 255, 255))
        
        # Scale the title
        scaled_width = int(title_surf.get_width() * pulse_scale)
        scaled_height = int(title_surf.get_height() * pulse_scale)
        scaled_title = pygame.transform.scale(title_surf, (scaled_width, scaled_height))
        
        # Center and draw
        title_rect = scaled_title.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 150))
        
        # Add glow effect
        glow_surf = pygame.transform.scale(scaled_title, (scaled_width + 10, scaled_height + 10))
        glow_surf.set_alpha(50)
        glow_rect = glow_surf.get_rect(center=title_rect.center)
        self.screen.blit(glow_surf, glow_rect)
        
        # Draw main title
        self.screen.blit(scaled_title, title_rect)
    
    def _draw_subtitle(self):
        """Draw subtitle text"""
        subtitle_text = "A Neural Simulation Adventure"
        subtitle_surf = self.font_small.render(subtitle_text, True, (200, 200, 200))
        subtitle_rect = subtitle_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 100))
        self.screen.blit(subtitle_surf, subtitle_rect)
    
    def _draw_buttons(self):
        """Draw menu buttons with hover effects and loading animation"""
        button_texts = {
            "start": "Start Game",
            "settings": "Settings", 
            "quit": "Quit"
        }
        
        for button_name, button_rect in self.buttons.items():
            # Determine if this button is loading
            is_loading = self.loading and self.loading_button == button_name
            
            # Determine button colors
            if is_loading:
                bg_color = (80, 120, 80)    # Green tint when loading
                border_color = (100, 255, 100)
                text_color = (200, 255, 200)
                border_width = 3
            elif self.hovered_button == button_name and not self.loading:
                bg_color = (100, 100, 150)  # Lighter when hovered
                border_color = (255, 255, 255)
                text_color = (255, 255, 255)
                border_width = 3
            else:
                bg_color = (50, 50, 80)     # Darker normally
                border_color = (150, 150, 150)
                text_color = (200, 200, 200)
                border_width = 2
            
            # Disable other buttons during loading
            if self.loading and not is_loading:
                bg_color = (30, 30, 30)     # Very dark when disabled
                border_color = (80, 80, 80)
                text_color = (100, 100, 100)
                border_width = 1
            
            # Draw button background
            pygame.draw.rect(self.screen, bg_color, button_rect)
            pygame.draw.rect(self.screen, border_color, button_rect, border_width)
            
            # Draw button text with loading animation
            if is_loading:
                # Create loading text with animated dots
                dots = "." * self.loading_dots
                loading_text = f"Loading{dots}"
                text_surf = self.font_small.render(loading_text, True, text_color)
                
                # Add loading progress bar
                self._draw_loading_progress(button_rect, bg_color)
            else:
                text_surf = self.font_small.render(button_texts[button_name], True, text_color)
            
            text_rect = text_surf.get_rect(center=button_rect.center)
            self.screen.blit(text_surf, text_rect)
    
    def _draw_loading_progress(self, button_rect, bg_color):
        """Draw loading progress bar inside button"""
        current_time = pygame.time.get_ticks()
        progress = min(1.0, (current_time - self.loading_start_time) / self.loading_duration)
        
        # Progress bar dimensions
        bar_width = button_rect.width - 20
        bar_height = 4
        bar_x = button_rect.x + 10
        bar_y = button_rect.bottom - 15
        
        # Background bar
        pygame.draw.rect(self.screen, (100, 100, 100), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Progress bar
        progress_width = int(bar_width * progress)
        pygame.draw.rect(self.screen, (100, 255, 100), 
                        (bar_x, bar_y, progress_width, bar_height))
    
    def _draw_version_info(self):
        """Draw version information in corner"""
        version_text = "v1.0.0 - Alpha"
        version_surf = pygame.font.Font(None, 24).render(version_text, True, (150, 150, 150))
        version_rect = version_surf.get_rect(bottomright=(app.WIDTH - 10, app.HEIGHT - 10))
        self.screen.blit(version_surf, version_rect)

class UIManager:
    """Handles all UI rendering"""
    
    def __init__(self, screen, font_small, font_large, font_chat):  # Fixed: __init__
        self.screen = screen
        self.font_small = font_small
        self.font_large = font_large
        self.font_chat = font_chat
    
    def draw_game_time_ui(self):
        """Draw the time and temperature UI in top-right corner"""
        time_str, temperature = self._compute_game_time_and_temp()
        ui_text = f"Time: {time_str}   Temp: {temperature}°C"
        ui_surf = self.font_small.render(ui_text, True, (255, 255, 255))
        pos = (app.WIDTH - ui_surf.get_width() - 10, 10)
        self.screen.blit(ui_surf, pos)
    
    def _compute_game_time_and_temp(self) -> Tuple[str, float]:  # Fixed: _compute
        """Compute current game time and temperature"""
        now = datetime.datetime.now()
        hour, minute = now.hour, now.minute
        
        # Format 12-hour time
        ampm = "AM" if hour < 12 else "PM"
        display_hour = hour % 12 or 12
        time_str = f"{display_hour}:{minute:02d} {ampm}"
        
        # Temperature calculation
        avg_temp_c = 21
        amplitude = 5
        day_fraction = hour / 24 + minute / 1440
        shift = 4 / 24  # Coldest at 4 AM
        
        temp_c = avg_temp_c + amplitude * math.sin(2 * math.pi * (day_fraction - shift))
        return time_str, round(temp_c, 1)
    
    def draw_settings_menu(self):
        """Draw the settings menu overlay"""
        # Dark overlay
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title_surf = self.font_large.render("Settings", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 150))
        self.screen.blit(title_surf, title_rect)
        
        # Return button
        return_rect = pygame.Rect(app.WIDTH//2 - 150, app.HEIGHT//2 - 50, 300, 50)
        self._draw_button(return_rect, "Return to Title")
        
        # Quit button
        quit_rect = pygame.Rect(app.WIDTH//2 - 150, app.HEIGHT//2 + 10, 300, 50)
        self._draw_button(quit_rect, "Quit Game")
        
        return return_rect, quit_rect
    
    def _draw_button(self, rect: pygame.Rect, text: str):  # Fixed: _draw_button
        """Draw a button with text"""
        pygame.draw.rect(self.screen, (70, 70, 70), rect)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
        text_surf = self.font_small.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)
    
    def wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """Wrap text to fit within max_width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}" if current_line else word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
                
        if current_line:
            lines.append(current_line)
            
        return lines


class ChatRenderer:
    """Handles chat box rendering"""
    
    def __init__(self, ui_manager: UIManager):  # Fixed: __init__
        self.ui = ui_manager
    
    def draw_chat_interface(self, current_npc, chat_manager: ChatManager):
        """Draw the complete chat interface"""
        self._draw_overlay()
        self._draw_header(current_npc.name)
        self._draw_chat_history(current_npc, chat_manager)
        self._draw_input_box(chat_manager.message)
    
    def _draw_overlay(self):  # Fixed: _draw_overlay
        """Draw dark overlay behind chat"""
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.ui.screen.blit(overlay, (0, 0))
    
    def _draw_header(self, npc_name: str):  # Fixed: _draw_header
        """Draw chat header with NPC name"""
        header_text = f"Chat with {npc_name}:"
        header_surf = self.ui.font_large.render(header_text, True, (255, 255, 255))
        header_rect = header_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 400))
        self.ui.screen.blit(header_surf, header_rect)
    
    def _draw_chat_history(self, current_npc, chat_manager: ChatManager):  # Fixed: _draw_chat_history
        """Draw the chat history box with scrolling"""
        # Box dimensions
        box_width, box_height = app.WIDTH - 350, 450
        box_x, box_y = 175, app.HEIGHT - box_height - 170
        
        # Draw box background
        pygame.draw.rect(self.ui.screen, (30, 30, 30), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.ui.screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)
        
        # Text area setup
        text_margin_left, text_margin_right = 60, 20
        bubble_width = box_width - text_margin_left - text_margin_right
        
        # Build wrapped lines from chat history
        all_lines = self._build_chat_lines(current_npc.chat_history, bubble_width)
        
        # Calculate visible area
        top_padding, bottom_padding = 10, 10
        available_height = box_height - top_padding - bottom_padding
        line_height = self.ui.font_chat.get_height() + 5
        visible_lines = available_height // line_height
        
        # Update scroll offset
        chat_manager.handle_scroll(0, len(all_lines), visible_lines)
        
        # Draw visible lines
        self._draw_visible_lines(all_lines, chat_manager.scroll_offset, visible_lines,
                               box_x, box_y + top_padding, text_margin_left, bubble_width,
                               line_height, current_npc)
        
        # Draw live typing message
        if chat_manager.live_message:
            self._draw_live_message(chat_manager.live_message, box_x, box_y,
                                  text_margin_left, bubble_width, len(all_lines),
                                  visible_lines, line_height, top_padding)
        
        # Draw scrollbar
        if len(all_lines) > visible_lines:
            self._draw_scrollbar(box_x + box_width - 10, box_y + top_padding,
                               available_height, len(all_lines), visible_lines,
                               chat_manager.scroll_offset)
    
    def _build_chat_lines(self, chat_history: List, bubble_width: int) -> List[Tuple]:  # Fixed: _build_chat_lines
        """Build a flat list of wrapped lines from chat history"""
        all_lines = []
        for entry in chat_history:
            speaker, message = entry if isinstance(entry, tuple) else ("npc", entry)
            wrapped = self.ui.wrap_text(message, self.ui.font_chat, bubble_width)
            for idx, line in enumerate(wrapped):
                all_lines.append((speaker, line, idx == 0))
        return all_lines
    
    def _draw_visible_lines(self, all_lines: List, scroll_offset: int, visible_lines: int,  # Fixed: _draw_visible_lines
                          box_x: int, start_y: int, text_margin_left: int, bubble_width: int,
                          line_height: int, current_npc):
        """Draw the visible portion of chat lines"""
        y_offset = start_y
        visible_slice = all_lines[scroll_offset:scroll_offset + visible_lines]
        
        for speaker, line_text, is_first in visible_slice:
            text_color = (0, 0, 255) if speaker == "player" else (255, 255, 0)
            
            # Center text in bubble
            bubble_x = box_x + text_margin_left
            text_x = bubble_x + (bubble_width - self.ui.font_chat.size(line_text)[0]) // 2
            line_surf = self.ui.font_chat.render(line_text, True, text_color)
            self.ui.screen.blit(line_surf, (text_x, y_offset))
            
            # Draw sprite for first line of each message
            if is_first and line_text.strip():
                self._draw_message_sprite(speaker, box_x, y_offset, current_npc)
            
            y_offset += line_height
    
    def _draw_message_sprite(self, speaker: str, box_x: int, y_offset: int, current_npc):  # Fixed: _draw_message_sprite
        """Draw character sprite next to message"""
        if speaker == "player":
            # Assuming we have access to player image through some means
            # This would need to be passed in or accessed differently
            sprite_box = pygame.Rect(box_x + app.WIDTH - 350 - 60, y_offset, 40, 50)
            # player_sprite = pygame.transform.flip(pygame.transform.scale(player.image, (40, 50)), True, False)
            # self.ui.screen.blit(player_sprite, sprite_box.topleft)
        elif speaker == "npc":
            sprite_box = pygame.Rect(box_x + 10, y_offset, 40, 50)
            npc_sprite = pygame.transform.scale(current_npc.image, (40, 50))
            self.ui.screen.blit(npc_sprite, sprite_box.topleft)
    
    def _draw_live_message(self, live_message: str, box_x: int, box_y: int,  # Fixed: _draw_live_message
                         text_margin_left: int, bubble_width: int, total_lines: int,
                         visible_lines: int, line_height: int, top_padding: int):
        """Draw the currently typing message"""
        bubble_x = box_x + text_margin_left
        live_lines = self.ui.wrap_text(live_message, self.ui.font_chat, bubble_width)
        
        # Calculate starting Y position
        visible_area_height = visible_lines * line_height
        live_y = box_y + top_padding + visible_area_height
        
        for line in live_lines:
            text_x = bubble_x + (bubble_width - self.ui.font_chat.size(line)[0]) // 2
            line_surf = self.ui.font_chat.render(line, True, (255, 255, 0))
            self.ui.screen.blit(line_surf, (text_x, live_y))
            live_y += self.ui.font_chat.get_height() + 5
    
    def _draw_scrollbar(self, bar_x: int, bar_y: int, bar_height: int,  # Fixed: _draw_scrollbar
                       total_lines: int, visible_lines: int, scroll_offset: int):
        """Draw the chat scrollbar"""
        bar_width = 8
        # Background track
        pygame.draw.rect(self.ui.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        
        # Thumb
        thumb_height = max(20, bar_height * visible_lines // total_lines)
        max_scroll = max(1, total_lines - visible_lines)
        thumb_y = bar_y + (bar_height - thumb_height) * scroll_offset // max_scroll
        pygame.draw.rect(self.ui.screen, (200, 200, 200), (bar_x, thumb_y, bar_width, thumb_height))
    
    def _draw_input_box(self, message: str):  # Fixed: _draw_input_box
        """Draw the message input box"""
        box_width, box_height = app.WIDTH - 350, 100
        box_x, box_y = 175, app.HEIGHT - box_height - 50
        
        pygame.draw.rect(self.ui.screen, (50, 50, 50), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.ui.screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)
        
        if message:
            bubble_x = box_x + 60
            bubble_width = box_width - 120
            msg_surf = self.ui.font_small.render(message, True, (0, 0, 255))
            text_x = bubble_x + (bubble_width - msg_surf.get_width()) // 2
            text_y = box_y + (box_height - msg_surf.get_height()) // 2
            self.ui.screen.blit(msg_surf, (text_x, text_y))


class Game:
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
    
    def _init_building(self):  # Fixed: _init_building
        """Initialize buildings with hitboxes"""
        # Create buildings with hitboxes
        self.buildings = [
            Building(150, 450, "house", self.assets),
            Building(800, 450, "shop", self.assets)
        ]
        # Debug mode to see hitboxes
        self.debug_hitboxes = False  # Set to True to see hitbox outlines
    
    def _init_camera(self):  # Fixed: _init_camera
        """Initialize camera with smooth following"""
        # Initialize camera
        map_size = 3000
        self.camera = Camera(app.WIDTH, app.HEIGHT, map_size, map_size)
        
        # Optional: Enable smooth camera following
        self.camera.smooth_follow = True
        self.camera.smoothing = 0.05  # Adjust for desired smoothness
    
    def _init_display(self):  # Fixed: _init_display
        """Initialize the game display"""
        screen_width, screen_height = pygame.display.get_desktop_sizes()[0]
        self.screen = pygame.display.set_mode(
            (screen_width, screen_height), pygame.FULLSCREEN
        )
        pygame.display.set_caption("PROJECT NEUROSIM")
        self.clock = pygame.time.Clock()
    
    def _init_fonts(self):  # Fixed: _init_fonts
        """Initialize game fonts"""
        font_path = os.path.join("assets", "PressStart2P.ttf")
        self.font_small = pygame.font.Font(font_path, 18)
        self.font_large = pygame.font.Font(font_path, 32)
        self.font_chat = pygame.font.Font(font_path, 14)
    
    def _init_game_objects(self):  # Fixed: _init_game_objects
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
    
    def _init_managers(self):  # Fixed: _init_managers
        """Initialize manager classes"""
        self.chat_manager = ChatManager(self.font_chat, self.font_small)
        self.ui_manager = UIManager(self.screen, self.font_small, self.font_large, self.font_chat)
        self.chat_renderer = ChatRenderer(self.ui_manager)
    
    def _init_game_state(self):  # Fixed: _init_game_state
        """Initialize game state variables"""
        self.running = True
        self.game_over = False
        self.game_state = GameState.START_SCREEN  # START WITH START_SCREEN
        self.current_npc = None
        self.start_ticks = pygame.time.get_ticks()
    
    def _create_random_background(self, width: int, height: int) -> pygame.Surface:  # Fixed: _create_random_background
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
    
    def _handle_mouse_wheel(self, event):  # Fixed: _handle_mouse_wheel
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
    
    def _handle_playing_keys(self, event):  # Fixed: _handle_playing_keys
        """Handle keys during playing state"""
        if event.key == pygame.K_ESCAPE:
            self.game_state = GameState.SETTINGS
        elif event.key == pygame.K_RETURN:
            self._try_interact_with_npc()
        elif event.key == pygame.K_F1:  # Added: Toggle debug hitboxes
            self.toggle_debug_hitboxes()
    
    def _handle_interaction_keys(self, event):  # Fixed: _handle_interaction_keys
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
    
    def _handle_settings_keys(self, event):  # Fixed: _handle_settings_keys
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
    
    def _try_interact_with_npc(self):  # Fixed: _try_interact_with_npc
        """Try to interact with nearby NPCs"""
        for npc_obj in self.npcs:
            if self.player.rect.colliderect(npc_obj.rect):
                self.game_state = GameState.INTERACTING
                self.current_npc = npc_obj
                self.chat_manager.message = ""
                break
    
    def _exit_interaction(self):  # Fixed: _exit_interaction
        """Exit NPC interaction"""
        self.game_state = GameState.PLAYING
        self.chat_manager.message = ""
        self.current_npc = None
    
    def _send_chat_message(self):  # Fixed: _send_chat_message
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
    
    def _build_ai_prompt(self, npc_obj, new_message: str) -> str:  # Fixed: _build_ai_prompt
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