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
        """Draw the settings menu overlay using SETTINGS_MENU_OPTIONS, with animated buttons"""
        # Dark overlay
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title_surf = self.font_large.render("Settings", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 150))
        self.screen.blit(title_surf, title_rect)
        
        # Dynamically create buttons from SETTINGS_MENU_OPTIONS
        button_width = 300
        button_height = 50
        button_spacing = 20
        start_y = app.HEIGHT // 2 - 50
        buttons = []
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        hovered_index = None
        clicked_index = None
        for i, option in enumerate(SETTINGS_MENU_OPTIONS):
            rect = pygame.Rect(
                app.WIDTH // 2 - button_width // 2,
                start_y + i * (button_height + button_spacing),
                button_width,
                button_height
            )
            is_hovered = rect.collidepoint(mouse_pos)
            is_clicked = is_hovered and mouse_pressed
            # Animate: lighter when hovered, darker when clicked
            if is_clicked:
                bg_color = (40, 40, 60)  # Darker when clicked
                border_color = (120, 120, 180)
                text_color = (200, 200, 255)
            elif is_hovered:
                bg_color = (100, 120, 180)  # Lighter when hovered
                border_color = (255, 255, 255)
                text_color = (255, 255, 255)
            else:
                bg_color = (60, 60, 90)  # Normal
                border_color = (180, 180, 180)
                text_color = (220, 220, 220)
            self._draw_button(rect, option["label"], bg_color, border_color, text_color)
            buttons.append((rect, option["action"]))
        return buttons
    
    def _draw_button(self, rect: pygame.Rect, text: str, bg_color=(70, 70, 70), border_color=(255, 255, 255), text_color=(255, 255, 255)):
        """Draw a button with text and custom colors"""
        pygame.draw.rect(self.screen, bg_color, rect)
        pygame.draw.rect(self.screen, border_color, rect, 2)
        text_surf = self.font_small.render(text, True, text_color)
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