"""
UI management and rendering utilities
"""
import pygame
import datetime
import math
from typing import List, Tuple

from functions import app
from config.settings import SETTINGS_MENU_OPTIONS

class UIManager:
    """Handles all UI rendering"""
    
    def __init__(self, screen, font_small, font_large, font_chat):
        self.screen = screen
        self.font_small = font_small
        self.font_large = font_large
        self.font_chat = font_chat
        
        # Animation variables for settings menu
        self.button_animations = {}
        self.hovered_button_index = None
        
        # Initialize button animations
        for i in range(len(SETTINGS_MENU_OPTIONS)):
            self.button_animations[i] = {"scale": 1.0, "glow": 0.0}
    
    def draw_game_time_ui(self):
        """Draw the time and temperature UI in top-right corner"""
        time_str, temperature = self._compute_game_time_and_temp()
        ui_text = f"Time: {time_str}   Temp: {temperature}°C"
        ui_surf = self.font_small.render(ui_text, True, (255, 255, 255))
        pos = (app.WIDTH - ui_surf.get_width() - 10, 10)
        self.screen.blit(ui_surf, pos)
    
    def _compute_game_time_and_temp(self) -> Tuple[str, float]:
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
        """Draw the settings menu overlay with hover effects like title screen"""
        from functions import app
        from config.settings import SETTINGS_MENU_OPTIONS
        
        # Dark overlay
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Title with glow effect
        title_surf = self.font_large.render("Settings", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 200))
        
        # Add title glow
        glow_surf = pygame.transform.scale(title_surf, (title_surf.get_width() + 6, title_surf.get_height() + 6))
        glow_surf.set_alpha(50)
        glow_rect = glow_surf.get_rect(center=title_rect.center)
        self.screen.blit(glow_surf, glow_rect)
        self.screen.blit(title_surf, title_rect)
        
        # Button configuration
        button_width = 320
        button_height = 60
        button_spacing = 20
        start_y = app.HEIGHT // 2 - 100
        
        # Get mouse position for hover detection
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_button_index = None
        
        # Create buttons with hover effects
        buttons = []
        for i, option in enumerate(SETTINGS_MENU_OPTIONS):
            # Calculate button rectangle
            rect = pygame.Rect(
                app.WIDTH // 2 - button_width // 2,
                start_y + i * (button_height + button_spacing),
                button_width,
                button_height
            )
            
            # Check if hovered
            is_hovered = rect.collidepoint(mouse_pos)
            if is_hovered:
                self.hovered_button_index = i
            
            # Update animations
            self._update_button_animation(i, is_hovered)
            
            # Draw button with animations
            self._draw_animated_settings_button(rect, option["label"], i)
            
            buttons.append((rect, option["action"]))
        
        return buttons
    
    def _update_button_animation(self, button_index, is_hovered):
        """Update button animation states"""
        animation_speed = 0.15
        anim = self.button_animations[button_index]
        
        if is_hovered:
            # Animate to hover state
            anim["scale"] = min(anim["scale"] + animation_speed * 0.5, 1.05)
            anim["glow"] = min(anim["glow"] + animation_speed, 1.0)
        else:
            # Animate to normal state
            anim["scale"] = max(anim["scale"] - animation_speed * 0.5, 1.0)
            anim["glow"] = max(anim["glow"] - animation_speed, 0.0)

    def _draw_button(self, rect: pygame.Rect, text: str, bg_color=(70, 70, 70), border_color=(255, 255, 255), text_color=(255, 255, 255)):
        """Draw a button with text and custom colors"""
        pygame.draw.rect(self.screen, bg_color, rect)
        pygame.draw.rect(self.screen, border_color, rect, 2)
        text_surf = self.font_small.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)
    
    def _draw_animated_settings_button(self, rect, text, button_index):
        """Draw animated settings button similar to title screen"""
        anim = self.button_animations[button_index]
        
        # Calculate scaled rect
        scale = anim["scale"]
        scaled_width = int(rect.width * scale)
        scaled_height = int(rect.height * scale)
        scaled_rect = pygame.Rect(
            rect.centerx - scaled_width // 2,
            rect.centery - scaled_height // 2,
            scaled_width,
            scaled_height
        )
        
        # Determine colors based on hover state
        glow_intensity = anim["glow"]
        base_r = int(50 + glow_intensity * 50)
        base_g = int(50 + glow_intensity * 70)
        base_b = int(80 + glow_intensity * 70)
        
        base_color = (base_r, base_g, base_b)
        border_color = (150 + int(glow_intensity * 105), 
                       150 + int(glow_intensity * 105), 
                       150 + int(glow_intensity * 105))
        text_color = (200 + int(glow_intensity * 55), 
                     200 + int(glow_intensity * 55), 
                     200 + int(glow_intensity * 55))
        
        # Draw gradient background
        self._draw_gradient_button(scaled_rect, base_color, glow_intensity)
        
        # Draw border with glow effect
        border_width = 2 + int(glow_intensity * 2)
        pygame.draw.rect(self.screen, border_color, scaled_rect, border_width)
        
        # Draw glow effect around button
        if glow_intensity > 0:
            self._draw_button_glow(scaled_rect, border_color, glow_intensity)
        
        # Draw button text
        text_surf = self.font_small.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        self.screen.blit(text_surf, text_rect)

    def _draw_gradient_button(self, rect, base_color, glow_intensity):
        """Draw a button with gradient background"""
        # Create gradient surface
        gradient_surf = pygame.Surface((rect.width, rect.height))
        
        for y in range(rect.height):
            # Create vertical gradient
            progress = y / rect.height
            
            # Darker at top, lighter at bottom
            r = int(base_color[0] * (0.7 + 0.3 * progress))
            g = int(base_color[1] * (0.7 + 0.3 * progress))
            b = int(base_color[2] * (0.7 + 0.3 * progress))
            
            # Add glow effect
            if glow_intensity > 0:
                r = min(255, int(r + glow_intensity * 30))
                g = min(255, int(g + glow_intensity * 30))
                b = min(255, int(b + glow_intensity * 30))
            
            color = (r, g, b)
            pygame.draw.line(gradient_surf, color, (0, y), (rect.width, y))
        
        self.screen.blit(gradient_surf, rect)

    def _draw_button_glow(self, rect, color, intensity):
        """Draw glow effect around button"""
        glow_size = int(10 * intensity)
        glow_alpha = int(100 * intensity)
        
        # Create glow surface
        glow_surf = pygame.Surface((rect.width + glow_size * 2, rect.height + glow_size * 2), pygame.SRCALPHA)
        
        # Draw multiple glow layers
        for i in range(glow_size):
            alpha = int(glow_alpha * (1 - i / glow_size))
            glow_color = (*color, alpha)
            glow_rect = pygame.Rect(glow_size - i, glow_size - i, 
                                  rect.width + i * 2, rect.height + i * 2)
            pygame.draw.rect(glow_surf, glow_color, glow_rect, 1)
        
        # Blit glow surface
        glow_pos = (rect.x - glow_size, rect.y - glow_size)
        self.screen.blit(glow_surf, glow_pos)

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