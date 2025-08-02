"""
Enhanced overlay system with glowing, pulsing RGB effects for pixel game aesthetics
"""
import pygame
import math
import time
from typing import Optional, Tuple, List
import textwrap


class OverlaySystem:
    """Manages overlay screens with fancy glowing effects"""
    
    def __init__(self, screen: pygame.Surface, font_large: pygame.font.Font, 
                 font_small: pygame.font.Font, font_chat: pygame.font.Font):
        """
        Initialize the overlay system
        
        Args:
            screen: Main game screen surface
            font_large: Large font for titles
            font_small: Small font for body text
            font_chat: Chat font for details
        """
        self.screen = screen
        self.font_large = font_large
        self.font_small = font_small
        self.font_chat = font_chat
        
        # Animation timing
        self.start_time = time.time()
        
        # Base colors
        self.bg_color = (0, 0, 0, 180)
        self.text_color = (170, 170, 170)
        self.button_color = (60, 60, 60)
        self.button_hover_color = (80, 80, 80)
        
        # Version information
        self.version_info = {
            "title": "PROJECT NEUROSIM",
            "version": "v0.8.2 Alpha",
            "build_date": "May/June 2025",
            "engine": "Pygame 2.5.2",
            "python_version": "Python 3.9+",
            "features": [
                "AI-Powered NPC Conversations",
                "Dynamic Building System",
                "Procedural Map Generation",
                "Real-time Chat Interface",
                "Interactive Tutorial System"
            ]
        }
        
        # Credits information
        self.credits_info = {
            "title": "CREDITS",
            "sections": [
                {
                    "category": "DEVELOPMENT",
                    "entries": [
                        "Project Manager: Angus Shui",
                        "Lead Programming: Haoran Fang",
                        "Lead Art: Lucas Guo",
                        "Architecture: Modular Python System",
                        "Tools: Pygame, Python 3.9+, GitHub, VSCode, ",
                        "CursorAI, Claude Sonnet 4, ChatGPT-o4"
                    ]
                },
                {
                    "category": "TECHNOLOGY",
                    "entries": [
                        "Game Engine: Pygame",
                        "AI Model: Llama3.2",
                        "Graphics: Pixel Art Style",
                        "Font: Press Start 2P"
                    ]
                },
                {
                    "category": "SPECIAL THANKS",
                    "entries": [
                        "Pygame Community",
                        "Python Software Foundation",
                        "Beta Testers & Feedback Providers",
                        "AI Club Members",
                        "AI Club President Alex Cai"
                    ]
                }
            ]
        }
    
    def get_rgb_color(self, speed: float = 1.0, brightness: float = 1.0) -> Tuple[int, int, int]:
        """Generate cycling RGB color for neon effects"""
        current_time = time.time() - self.start_time
        hue = (current_time * speed) % 6.0
        
        # Create smooth RGB transitions
        if hue < 1:
            r, g, b = 255, int(255 * hue), 0
        elif hue < 2:
            r, g, b = int(255 * (2 - hue)), 255, 0
        elif hue < 3:
            r, g, b = 0, 255, int(255 * (hue - 2))
        elif hue < 4:
            r, g, b = 0, int(255 * (4 - hue)), 255
        elif hue < 5:
            r, g, b = int(255 * (hue - 4)), 0, 255
        else:
            r, g, b = 255, 0, int(255 * (6 - hue))
        
        # Apply brightness
        r = int(r * brightness)
        g = int(g * brightness)
        b = int(b * brightness)
        
        return (r, g, b)
    
    def get_pulse_intensity(self, speed: float = 2.0, min_intensity: float = 0.3) -> float:
        """Get pulsing intensity value"""
        current_time = time.time() - self.start_time
        pulse = (math.sin(current_time * speed) + 1) / 2  # 0 to 1
        return min_intensity + pulse * (1 - min_intensity)
    
    def draw_glowing_rect(self, rect: pygame.Rect, glow_size: int = 8, color: Optional[Tuple[int, int, int]] = None):
        """Draw a rectangle with glowing border effect"""
        if color is None:
            color = self.get_rgb_color(1.5)
        
        pulse = self.get_pulse_intensity(3.0, 0.4)
        
        # Draw multiple layers for glow effect
        for i in range(glow_size, 0, -1):
            alpha = int(30 * pulse * (glow_size - i + 1) / glow_size)
            glow_color = (*color, alpha)
            
            # Create glow surface
            glow_surface = pygame.Surface((rect.width + i * 2, rect.height + i * 2), pygame.SRCALPHA)
            glow_rect = pygame.Rect(0, 0, rect.width + i * 2, rect.height + i * 2)
            pygame.draw.rect(glow_surface, glow_color, glow_rect, max(1, i // 2))
            
            # Blit glow
            glow_x = rect.x - i
            glow_y = rect.y - i
            self.screen.blit(glow_surface, (glow_x, glow_y), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def draw_glowing_text(self, text: str, font: pygame.font.Font, pos: Tuple[int, int], 
                         color: Optional[Tuple[int, int, int]] = None, glow_size: int = 3) -> pygame.Surface:
        """Draw text with glowing effect"""
        if color is None:
            color = self.get_rgb_color(2.0, 0.75)
        
        pulse = self.get_pulse_intensity(2.5, 0.5)
        
        # Render main text
        text_surface = font.render(text, True, (255, 255, 255))
        
        # Create glow layers
        for i in range(glow_size, 0, -1):
            alpha = int(80 * pulse * (glow_size - i + 1) / glow_size)
            glow_color = (*color, alpha)
            
            # Create glow surface
            glow_surface = pygame.Surface((text_surface.get_width() + i * 2, 
                                         text_surface.get_height() + i * 2), pygame.SRCALPHA)
            
            # Draw glow text multiple times with slight offsets
            for dx in range(-i, i + 1):
                for dy in range(-i, i + 1):
                    if dx * dx + dy * dy <= i * i:  # Circular glow
                        glow_text = font.render(text, True, glow_color)
                        glow_surface.blit(glow_text, (i + dx, i + dy), special_flags=pygame.BLEND_ALPHA_SDL2)
            
            # Blit glow to screen
            self.screen.blit(glow_surface, (pos[0] - i, pos[1] - i), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Draw main text
        self.screen.blit(text_surface, pos)
        return text_surface
    
    def draw_animated_background(self, rect: pygame.Rect):
        """Draw animated pixel-style background with flowing effects"""
        # Base dark background
        pygame.draw.rect(self.screen, (20, 20, 30), rect)
        
        current_time = time.time() - self.start_time
        
        # Draw flowing pixel grid
        grid_size = 20
        for x in range(rect.x, rect.x + rect.width, grid_size):
            for y in range(rect.y, rect.y + rect.height, grid_size):
                # Create wave pattern
                wave_offset = math.sin((x + y) * 0.02 + current_time * 2) * 0.5 + 0.5
                
                # Different colors based on position and time
                hue = ((x + y) * 0.01 + current_time * 0.5) % 6.0
                if hue < 2:
                    base_color = (int(50 + wave_offset * 30), int(20 + wave_offset * 15), int(80 + wave_offset * 40))
                elif hue < 4:
                    base_color = (int(20 + wave_offset * 15), int(50 + wave_offset * 30), int(80 + wave_offset * 40))
                else:
                    base_color = (int(80 + wave_offset * 40), int(20 + wave_offset * 15), int(50 + wave_offset * 30))
                
                # Draw small pixels
                if wave_offset > 0.7:  # Only draw bright pixels
                    pixel_rect = pygame.Rect(x, y, 2, 2)
                    pygame.draw.rect(self.screen, base_color, pixel_rect)
    
    def draw_version_overlay(self) -> Optional[pygame.Rect]:
        """Draw the enhanced version information overlay"""
        # Create semi-transparent background with starfield effect
        overlay_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay_surface.set_alpha(170)
        overlay_surface.fill((0, 0, 0))
        self.screen.blit(overlay_surface, (0, 0))
        
        # Add twinkling stars
        current_time = time.time() - self.start_time
        for i in range(50):
            star_x = (i * 137) % self.screen.get_width()  # Pseudo-random positions
            star_y = (i * 211) % self.screen.get_height()
            twinkle = math.sin(current_time * 2 + i) * 0.5 + 0.5
            if twinkle > 0.6:
                star_color = self.get_rgb_color(1.0, twinkle)
                pygame.draw.circle(self.screen, star_color, (star_x, star_y), 1)
        
        # Calculate content area
        content_width = 600
        content_height = 500
        content_x = (self.screen.get_width() - content_width) // 2
        content_y = (self.screen.get_height() - content_height) // 2
        
        # Draw animated background
        content_rect = pygame.Rect(content_x, content_y, content_width, content_height)
        self.draw_animated_background(content_rect)
        
        # Draw glowing border
        self.draw_glowing_rect(content_rect, 12)
        
        # Draw close button with glow
        close_button_size = 30
        close_x = content_x + content_width - close_button_size - 10
        close_y = content_y + 10
        close_rect = pygame.Rect(close_x, close_y, close_button_size, close_button_size)
        
        mouse_pos = pygame.mouse.get_pos()
        close_hover = close_rect.collidepoint(mouse_pos)
        
        if close_hover:
            self.draw_glowing_rect(close_rect, 6, (255, 100, 100))
        
        pygame.draw.rect(self.screen, self.button_hover_color if close_hover else self.button_color, close_rect)
        pygame.draw.rect(self.screen, self.text_color, close_rect, 2)
        
        # Draw X in close button
        x_size = 8
        x_center = close_rect.center
        pygame.draw.line(self.screen, self.text_color, 
                        (x_center[0] - x_size, x_center[1] - x_size),
                        (x_center[0] + x_size, x_center[1] + x_size), 2)
        pygame.draw.line(self.screen, self.text_color,
                        (x_center[0] + x_size, x_center[1] - x_size),
                        (x_center[0] - x_size, x_center[1] + x_size), 2)
        
        # Draw version content with glowing effects
        current_y = content_y + 20
        
        # Title with rainbow glow
        title_surface = self.draw_glowing_text(
            self.version_info["title"], 
            self.font_large, 
            (content_x + (content_width - self.font_large.size(self.version_info["title"])[0]) // 2, current_y),
            glow_size=5
        )
        current_y += title_surface.get_height() + 10
        
        # Version with cyan glow
        version_pos = (content_x + (content_width - self.font_small.size(self.version_info["version"])[0]) // 2, current_y)
        self.draw_glowing_text(self.version_info["version"], self.font_small, version_pos, (0, 160, 160), 3)
        current_y += self.font_small.get_height() + 20
        
        # System info with subtle glow
        info_items = [
            f"Build Date: {self.version_info['build_date']}",
            f"Engine: {self.version_info['engine']}",
            f"Python: {self.version_info['python_version']}"
        ]
        
        for item in info_items:
            self.draw_glowing_text(item, self.font_chat, (content_x + 40, current_y), (60, 120, 160), 2)
            current_y += self.font_chat.get_height() + 8
        
        current_y += 20
        
        # Features section with alternating colors
        features_title_pos = (content_x + 40, current_y)
        self.draw_glowing_text("KEY FEATURES:", self.font_small, features_title_pos, (220, 220, 0), 3)
        current_y += self.font_small.get_height() + 10
        
        for i, feature in enumerate(self.version_info["features"]):
            # Alternate between different glow colors
            colors = [(180, 80, 180), (80, 180, 80), (180, 110, 80), (80, 180, 180)]
            color = colors[i % len(colors)]
            
            feature_text = f"• {feature}"
            self.draw_glowing_text(feature_text, self.font_chat, (content_x + 60, current_y), color, 2)
            current_y += self.font_chat.get_height() + 6
        
        # Instructions with pulsing glow
        current_y = content_y + content_height - 40
        instruction_text = "Press ESC or click X to close"
        instruction_x = content_x + (content_width - self.font_chat.size(instruction_text)[0]) // 2
        pulse_color = tuple(int(150 * self.get_pulse_intensity(1.5, 0.5)) for _ in range(3))
        self.draw_glowing_text(instruction_text, self.font_chat, (instruction_x, current_y), pulse_color, 2)
        
        return close_rect
    
    def draw_credits_overlay(self) -> Optional[pygame.Rect]:
        """Draw the enhanced credits overlay"""
        # Create semi-transparent background
        overlay_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay_surface.set_alpha(200)
        overlay_surface.fill((0, 0, 0))
        self.screen.blit(overlay_surface, (0, 0))
        
        # Add matrix-style falling pixels
        current_time = time.time() - self.start_time
        for i in range(30):
            x = (i * 73) % self.screen.get_width()
            y = int((current_time * 50 + i * 100) % (self.screen.get_height() + 200))
            alpha = max(0, 255 - (y % 200))
            color = self.get_rgb_color(0.5, alpha / 255.0)
            if alpha > 50:
                pygame.draw.rect(self.screen, color, (x, y, 2, 8))
        
        # Calculate content area (wider for credits)
        content_width = 700
        content_height = 600
        content_x = (self.screen.get_width() - content_width) // 2
        content_y = (self.screen.get_height() - content_height) // 2
        
        # Draw animated background
        content_rect = pygame.Rect(content_x, content_y, content_width, content_height)
        self.draw_animated_background(content_rect)
        
        # Draw glowing border
        self.draw_glowing_rect(content_rect, 15)
        
        # Draw close button
        close_button_size = 30
        close_x = content_x + content_width - close_button_size - 10
        close_y = content_y + 10
        close_rect = pygame.Rect(close_x, close_y, close_button_size, close_button_size)
        
        mouse_pos = pygame.mouse.get_pos()
        close_hover = close_rect.collidepoint(mouse_pos)
        
        if close_hover:
            self.draw_glowing_rect(close_rect, 6, (255, 100, 100))
        
        pygame.draw.rect(self.screen, self.button_hover_color if close_hover else self.button_color, close_rect)
        pygame.draw.rect(self.screen, self.text_color, close_rect, 2)
        
        # Draw X in close button
        x_size = 8
        x_center = close_rect.center
        pygame.draw.line(self.screen, self.text_color, 
                        (x_center[0] - x_size, x_center[1] - x_size),
                        (x_center[0] + x_size, x_center[1] + x_size), 2)
        pygame.draw.line(self.screen, self.text_color,
                        (x_center[0] + x_size, x_center[1] - x_size),
                        (x_center[0] - x_size, x_center[1] + x_size), 2)
        
        # Draw credits content
        current_y = content_y + 20
        
        # Title with spectacular glow
        title_pos = (content_x + (content_width - self.font_large.size(self.credits_info["title"])[0]) // 2, current_y)
        self.draw_glowing_text(self.credits_info["title"], self.font_large, title_pos, glow_size=6)
        current_y += self.font_large.get_height() + 20
        
        # Credits sections with themed colors
        section_colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255)]
        
        for section_idx, section in enumerate(self.credits_info["sections"]):
            section_color = section_colors[section_idx % len(section_colors)]
            
            # Section category with glow
            category_pos = (content_x + 40, current_y)
            self.draw_glowing_text(section["category"], self.font_small, category_pos, section_color, 4)
            current_y += self.font_small.get_height() + 8
            
            # Section entries with subtle glow
            for entry in section["entries"]:
                entry_text = f"• {entry}"
                entry_color = tuple(int(c * 0.7) for c in section_color)  # Dimmer version
                self.draw_glowing_text(entry_text, self.font_chat, (content_x + 60, current_y), entry_color, 2)
                current_y += self.font_chat.get_height() + 4
            
            current_y += 15  # Space between sections
        
        # Instructions
        instruction_y = content_y + content_height - 40
        instruction_text = "Press ESC or click X to close"
        instruction_x = content_x + (content_width - self.font_chat.size(instruction_text)[0]) // 2
        pulse_color = tuple(int(150 * self.get_pulse_intensity(1.5, 0.5)) for _ in range(3))
        self.draw_glowing_text(instruction_text, self.font_chat, (instruction_x, instruction_y), pulse_color, 2)
        
        return close_rect
    
    def draw_corner_version(self):
        """Draw version number in corner with glowing effect"""
        version_text = self.version_info["version"]
        padding = 12
        
        # Position in bottom-right corner
        text_size = self.font_chat.size(version_text)
        bg_width = text_size[0] + padding * 2
        bg_height = text_size[1] + padding * 2
        bg_x = self.screen.get_width() - bg_width - 15
        bg_y = self.screen.get_height() - bg_height - 15
        
        # Draw glowing background
        bg_rect = pygame.Rect(bg_x, bg_y, bg_width, bg_height)
        self.draw_glowing_rect(bg_rect, 5, (0, 180, 180))
        
        # Draw semi-transparent background
        bg_surface = pygame.Surface((bg_width, bg_height))
        bg_surface.set_alpha(150)
        bg_surface.fill((0, 0, 0))
        self.screen.blit(bg_surface, (bg_x, bg_y))
        
        # Draw glowing text
        text_x = bg_x + padding
        text_y = bg_y + padding
        self.draw_glowing_text(version_text, self.font_chat, (text_x, text_y), (0, 180, 180), 2)
    
    def handle_overlay_click(self, pos: Tuple[int, int], overlay_type: str) -> bool:
        """Handle clicks on overlay elements"""
        if overlay_type == "version":
            close_rect = self.draw_version_overlay()
        elif overlay_type == "credits":
            close_rect = self.draw_credits_overlay()
        else:
            return False
        
        # Check if close button was clicked
        if close_rect and close_rect.collidepoint(pos):
            return True
        
        return False


class ModalOverlay:
    """Enhanced generic modal overlay with glowing effects"""
    
    def __init__(self, screen: pygame.Surface, title: str, content: List[str], 
                 font_large: pygame.font.Font, font_small: pygame.font.Font):
        """Initialize a generic modal overlay with effects"""
        self.screen = screen
        self.title = title
        self.content = content
        self.font_large = font_large
        self.font_small = font_small
        
        # Animation timing
        self.start_time = time.time()
        
        self.bg_color = (0, 0, 0, 180)
        self.text_color = (170, 170, 170)
        self.button_color = (60, 60, 60)
        self.button_hover_color = (80, 80, 80)
    
    def get_rgb_color(self, speed: float = 1.0) -> Tuple[int, int, int]:
        """Generate cycling RGB color with darker tones"""
        current_time = time.time() - self.start_time
        hue = (current_time * speed) % 0.6

        scale = 0.6  # Scale factor to darken all colors (0.0 = black, 1.0 = full brightness)

        if hue < 1:
            r, g, b = 255, int(255 * hue), 0
        elif hue < 2:
            r, g, b = int(255 * (2 - hue)), 180, 0
        elif hue < 3:
            r, g, b = 0, 180, int(255 * (hue - 2))
        elif hue < 4:
            r, g, b = 0, int(255 * (4 - hue)), 255
        elif hue < 5:
            r, g, b = int(255 * (hue - 4)), 0, 255
        else:
            r, g, b = 255, 0, int(255 * (6 - hue))

        # Apply brightness scaling
        r = int(r * scale)
        g = int(g * scale)
        b = int(b * scale)

        return (r, g, b)

    
    def draw_glowing_rect(self, rect: pygame.Rect, glow_size: int = 6):
        """Draw rectangle with glow effect"""
        color = self.get_rgb_color(1.5)
        pulse = (math.sin((time.time() - self.start_time) * 3) + 1) / 2 * 0.6 + 0.4
        
        for i in range(glow_size, 0, -1):
            alpha = int(40 * pulse * (glow_size - i + 1) / glow_size)
            glow_color = (*color, alpha)
            
            glow_surface = pygame.Surface((rect.width + i * 2, rect.height + i * 2), pygame.SRCALPHA)
            glow_rect = pygame.Rect(0, 0, rect.width + i * 2, rect.height + i * 2)
            pygame.draw.rect(glow_surface, glow_color, glow_rect, max(1, i // 2))
            
            self.screen.blit(glow_surface, (rect.x - i, rect.y - i), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def draw(self) -> Optional[pygame.Rect]:
        """Draw the enhanced modal overlay"""
        # Semi-transparent background
        overlay_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay_surface.set_alpha(200)
        overlay_surface.fill((0, 0, 0))
        self.screen.blit(overlay_surface, (0, 0))
        
        # Calculate content dimensions
        max_width = 600
        line_height = self.font_small.get_height() + 5
        content_height = len(self.content) * line_height + 120
        
        content_x = (self.screen.get_width() - max_width) // 2
        content_y = (self.screen.get_height() - content_height) // 2
        
        # Draw content background with glow
        content_rect = pygame.Rect(content_x, content_y, max_width, content_height)
        self.draw_glowing_rect(content_rect, 10)
        
        pygame.draw.rect(self.screen, (40, 40, 40), content_rect)
        
        # Draw close button
        close_button_size = 30
        close_x = content_x + max_width - close_button_size - 10
        close_y = content_y + 10
        close_rect = pygame.Rect(close_x, close_y, close_button_size, close_button_size)
        
        mouse_pos = pygame.mouse.get_pos()
        close_hover = close_rect.collidepoint(mouse_pos)
        
        if close_hover:
            self.draw_glowing_rect(close_rect, 4)
        
        pygame.draw.rect(self.screen, self.button_hover_color if close_hover else self.button_color, close_rect)
        pygame.draw.rect(self.screen, self.text_color, close_rect, 2)
        
        # Draw X
        x_size = 8
        x_center = close_rect.center
        pygame.draw.line(self.screen, self.text_color, 
                        (x_center[0] - x_size, x_center[1] - x_size),
                        (x_center[0] + x_size, x_center[1] + x_size), 2)
        pygame.draw.line(self.screen, self.text_color,
                        (x_center[0] + x_size, x_center[1] - x_size),
                        (x_center[0] - x_size, x_center[1] + x_size), 2)
        
        # Draw title with glow
        current_y = content_y + 20
        title_surface = self.font_large.render(self.title, True, self.text_color)
        title_x = content_x + (max_width - title_surface.get_width()) // 2
        
        # Glow effect for title
        glow_color = self.get_rgb_color(2.0)
        for i in range(3, 0, -1):
            glow_surface = self.font_large.render(self.title, True, glow_color)
            glow_surface.set_alpha(60 // i)
            self.screen.blit(glow_surface, (title_x - i, current_y - i), special_flags=pygame.BLEND_ALPHA_SDL2)
            self.screen.blit(glow_surface, (title_x + i, current_y + i), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        self.screen.blit(title_surface, (title_x, current_y))
        current_y += title_surface.get_height() + 20
        
        # Draw content
        for line in self.content:
            line_surface = self.font_small.render(line, True, self.text_color)
            self.screen.blit(line_surface, (content_x + 20, current_y))
            current_y += line_height
        
        return close_rect