"""
UI management and rendering utilities
"""
import pygame
import datetime
import math
from typing import List, Tuple

from functions.assets import app

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
    
    def _draw_button(self, rect: pygame.Rect, text: str):
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