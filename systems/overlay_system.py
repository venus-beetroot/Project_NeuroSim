import pygame
import math
import time
from typing import Optional, Tuple, List, Dict, Any
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

    def draw_floral_corner(self, rect: pygame.Rect, corner: str = "top_left", size: int = 30):
        """Draw subtle decorative pattern in corner"""
        current_time = time.time() - self.start_time
        
        # Calculate corner position with more padding
        padding = size // 3
        if corner == "top_left":
            cx, cy = rect.x + padding, rect.y + padding
        elif corner == "top_right":
            cx, cy = rect.x + rect.width - padding, rect.y + padding
        elif corner == "bottom_left":
            cx, cy = rect.x + padding, rect.y + rect.height - padding
        else:  # bottom_right
            cx, cy = rect.x + rect.width - padding, rect.y + rect.height - padding
        
        # Very subtle animated dots instead of flowers
        for i in range(3):  # Reduced from 6 to 3
            angle = (i * 120) + (current_time * 15) % 360  # Slower rotation
            dot_x = cx + math.cos(math.radians(angle)) * (size // 6)  # Smaller radius
            dot_y = cy + math.sin(math.radians(angle)) * (size // 6)
            
            pulse = self.get_pulse_intensity(1.5, 0.4)  # Gentler pulse
            dot_color = self.get_rgb_color(0.8, pulse * 0.3)  # Much dimmer
            
            # Smaller, more subtle dots
            pygame.draw.circle(self.screen, dot_color, (int(dot_x), int(dot_y)), 2)
            # Tiny highlight
            highlight_color = tuple(min(255, int(c + 40)) for c in dot_color)
            pygame.draw.circle(self.screen, highlight_color, (int(dot_x), int(dot_y)), 1)

    def draw_decorative_border(self, rect: pygame.Rect, thickness: int = 3):
        """Draw decorative border with flowing patterns"""
        current_time = time.time() - self.start_time
        
        # Draw flowing pattern along edges
        pattern_spacing = 15
        wave_amplitude = 3
        
        # Top and bottom edges
        for x in range(rect.x, rect.x + rect.width, pattern_spacing):
            wave_offset = math.sin((x * 0.02) + (current_time * 2)) * wave_amplitude
            color = self.get_rgb_color(0.5, 0.7)
            
            # Top edge pattern
            pygame.draw.circle(self.screen, color, 
                            (x, int(rect.y + wave_offset)), 2)
            
            # Bottom edge pattern
            pygame.draw.circle(self.screen, color, 
                            (x, int(rect.y + rect.height - wave_offset)), 2)
        
        # Left and right edges
        for y in range(rect.y, rect.y + rect.height, pattern_spacing):
            wave_offset = math.sin((y * 0.02) + (current_time * 2)) * wave_amplitude
            color = self.get_rgb_color(0.5, 0.7)
            
            # Left edge pattern
            pygame.draw.circle(self.screen, color, 
                            (int(rect.x + wave_offset), y), 2)
            
            # Right edge pattern  
            pygame.draw.circle(self.screen, color, 
                            (int(rect.x + rect.width - wave_offset), y), 2)

    def get_button_hover_scale(self, rect: pygame.Rect, mouse_pos: Tuple[int, int], 
                            base_scale: float = 1.0, hover_scale: float = 1.05) -> float:
        """Get scaling factor for button hover animation"""
        if rect.collidepoint(mouse_pos):
            pulse = self.get_pulse_intensity(4.0, 0.8)
            return base_scale + (hover_scale - base_scale) * pulse
        return base_scale

    def draw_enhanced_button(self, rect: pygame.Rect, base_color: Tuple[int, int, int], 
                            text: str, font: pygame.font.Font, is_hovered: bool = False,
                            is_pressed: bool = False, is_listening: bool = False):
        """Draw enhanced button with animations and decorative elements"""
        mouse_pos = pygame.mouse.get_pos()
        
        # Scale animation
        scale = self.get_button_hover_scale(rect, mouse_pos, 1.0, 1.03)
        if is_pressed:
            scale *= 0.95
        
        # Calculate scaled rect
        if scale != 1.0:
            scaled_width = int(rect.width * scale)
            scaled_height = int(rect.height * scale)
            scaled_rect = pygame.Rect(
                rect.centerx - scaled_width // 2,
                rect.centery - scaled_height // 2,
                scaled_width, scaled_height
            )
        else:
            scaled_rect = rect
        
        # Subtle yellow glow for hover/listening states
        if is_hovered or is_listening:
            pulse = self.get_pulse_intensity(2.0, 0.7)
            
            if is_listening:
                # Warmer yellow for listening state
                glow_color = (255, 220, 150)  # Warm yellow
                glow_size = int(8 * pulse)
                base_alpha = 60
            else:
                # Subtle yellow for hover
                glow_color = (255, 255, 200)  # Pale yellow
                glow_size = int(4 * pulse)
                base_alpha = 30
            
            # Draw subtle glow layers
            for i in range(glow_size, 0, -1):
                alpha = int(base_alpha * pulse * (glow_size - i + 1) / glow_size)
                glow_surface = pygame.Surface((scaled_rect.width + i * 4, scaled_rect.height + i * 4), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (*glow_color, alpha), glow_surface.get_rect(), border_radius=12)
                self.screen.blit(glow_surface, (scaled_rect.x - i * 2, scaled_rect.y - i * 2), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Button background with gradient effect
        button_surface = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
        
        # Fill with solid base color first
        button_surface.fill((0, 0, 0, 0))  # Clear to transparent
        pygame.draw.rect(button_surface, base_color, button_surface.get_rect(), border_radius=8)

        # Add gradient overlay
        gradient_overlay = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
        for i in range(scaled_rect.height):
            # Gradient from 30% brighter at top to base color at bottom
            brightness = 1.3 - (0.3 * i / scaled_rect.height)
            gradient_color = tuple(min(255, int(c * brightness)) for c in base_color)
            pygame.draw.rect(gradient_overlay, gradient_color, (0, i, scaled_rect.width, 1))

        # Create rounded mask and apply it
        mask = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=8)

        # Apply mask to gradient
        final_gradient = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
        final_gradient.blit(gradient_overlay, (0, 0))
        final_gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Apply to button
        button_surface.blit(final_gradient, (0, 0))

        # Add subtle hover highlight
        if is_hovered:
            pulse = self.get_pulse_intensity(2.0, 0.5)
            highlight_alpha = int(15 * pulse)
            highlight_overlay = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(highlight_overlay, (255, 255, 255, highlight_alpha), 
                            highlight_overlay.get_rect(), border_radius=8)
            button_surface.blit(highlight_overlay, (0, 0))
        
        # Border
        border_color = (255, 255, 255) if is_hovered else (170, 170, 170)
        pygame.draw.rect(button_surface, border_color, button_surface.get_rect(), 2, border_radius=8)

        self.screen.blit(button_surface, scaled_rect.topleft)

        # Decorative corners for larger buttons (draw AFTER blitting to screen)
        if scaled_rect.width > 120:  # Only on really large buttons
            self.draw_floral_corner(scaled_rect, "top_left", 15)  # Smaller size
            self.draw_floral_corner(scaled_rect, "bottom_right", 15)
        
        # Text rendering (keep existing scrolling logic but apply to scaled rect)
        # ... [keep the existing text rendering code from draw_button but use scaled_rect]
        
        return scaled_rect
    
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
        content_width = 850
        content_height = 650
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
        instruction_y = content_y + content_height - 35
        instruction_text = "Click a keybind to change it • ESC to close"  # Removed X reference
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
    

    def draw_keybind_overlay(self, keybind_manager, scroll_offset: int = 0,
                       listening_action: str = None, conflict_message: str = None) -> dict:
        """Draw the enhanced keybind configuration overlay with scrolling and UI improvements"""
        from config.settings import KEYBIND_CATEGORIES, KEYBIND_DISPLAY_NAMES, KEYBIND_MENU_SETTINGS

        button_height = 40
        button_spacing = 20
        panel_padding = 20

        if not hasattr(self, "current_scroll_offset"):
            self.current_scroll_offset = 0
            self.target_scroll_offset = 0

        interactive_elements = {
            "close_button": None, "keybind_buttons": {}, "reset_button": None,
            "save_button": None, "cancel_button": None, "scrollbar": None
        }

        # Create overlay background
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(160)
        overlay.fill((10, 10, 20, 160))
        self.screen.blit(overlay, (0, 0))

        # Matrix-style falling pixels (dimmed)
        now = time.time() - self.start_time
        for i in range(40):
            x = (i * 67) % self.screen.get_width()
            y = int((now * 60 + i * 120) % (self.screen.get_height() + 300))
            alpha = max(0, 180 - (y % 300))  # Reduced from 255 to 180
            col = self.get_rgb_color(0.3, alpha / 300.0)  # Dimmed further
            if alpha > 30:
                pygame.draw.rect(self.screen, col, (x, y, 4, 6))

        # Main panel dimensions and positioning
        w, h = 800, 670
        px = (self.screen.get_width() - w) // 2
        py = (self.screen.get_height() - h) // 2
        panel = pygame.Rect(px, py, w, h)
        
        # Store panel rect for click detection
        interactive_elements["panel_rect"] = panel
        
        self.draw_animated_background(panel)
        self.draw_glowing_rect(panel, 6)  # Reduced glow from 8 to 6

        # Add padding from panel edges
        panel_padding = 30
        y0 = py + panel_padding
        
        # Title with dimmed glow
        title = "KEYBIND SETTINGS"
        tx = px + (w - self.font_large.size(title)[0]) // 2
        self.draw_glowing_text(title, self.font_large, (tx, y0), self.get_rgb_color(1.0, 0.7), glow_size=2)  # Dimmed brightness
        y0 += self.font_large.get_height() + 20  # Add space after title

        # Conflict message with dimmed glow
        if conflict_message:
            cx = px + (w - self.font_small.size(conflict_message)[0]) // 2
            self.draw_glowing_text(conflict_message, self.font_small, (cx, y0), (200, 80, 80), 2)  # Dimmed red
            y0 += self.font_small.get_height() + 15

        # Content area calculations with proper padding
        start_y = y0 + 20  # Space between title and content
        area_h = h - (start_y - py) - 100  # Revert to original size
        # total_h = sum(
        #     KEYBIND_MENU_SETTINGS["category_height"] + len(v) * KEYBIND_MENU_SETTINGS["item_height"] + 10
        #     for v in KEYBIND_CATEGORIES.values()
        # )

        content_h = sum(
            KEYBIND_MENU_SETTINGS["category_height"]
            + len(v) * KEYBIND_MENU_SETTINGS["item_height"]
            + 10
            for v in KEYBIND_CATEGORIES.values()
        )

        extra_bottom_margin = KEYBIND_MENU_SETTINGS["item_height"]
        total_h = content_h + extra_bottom_margin

        # Add decorative elements to main panel
        self.draw_decorative_border(panel, 2)
        self.draw_floral_corner(panel, "top_left", 40)
        self.draw_floral_corner(panel, "top_right", 40) 
        self.draw_floral_corner(panel, "bottom_left", 40)
        self.draw_floral_corner(panel, "bottom_right", 40)
        
        # Smooth scrolling
        self.target_scroll_offset = max(0, min(total_h - area_h, scroll_offset))
        self.current_scroll_offset += (self.target_scroll_offset - self.current_scroll_offset) * 0.2

        # Scrollbar (if needed)
        content_padding = 25
        scrollbar_width = 20
        scrollbar_margin = 8  # Increased margin from edge to prevent border overlap
        
        if total_h > area_h:
            sbw = scrollbar_width
            sbx = px + w - content_padding - sbw - scrollbar_margin  # More space from edge
            bar = pygame.Rect(sbx, start_y, sbw, area_h)
            interactive_elements["scrollbar"] = bar
            pygame.draw.rect(self.screen, (60, 60, 60), bar, border_radius=10)
            pygame.draw.rect(self.screen, self.text_color, bar, 2, border_radius=10)
            max_scroll = total_h - area_h  # Remove extra padding to fix bottom scroll indication
            ratio = min(1.0, self.current_scroll_offset / max_scroll) if max_scroll > 0 else 0
            th = max(20, int(area_h * (area_h / total_h)))  # Fix thumb height calculation
            ty = start_y + int((area_h - th) * ratio)
            thumb = pygame.Rect(sbx + 2, ty, sbw - 4, th)
            pygame.draw.rect(self.screen, (80, 120, 200), thumb, border_radius=10)  # Dimmed blue
            self.draw_glowing_rect(thumb, 1, (80, 120, 200))  # Reduced glow
            
            # Arrow indicators for more content
            arrow_color = (150, 150, 200)
            arrow_size = 12
            arrow_x = sbx + sbw // 2
            
            # Up arrow if not at top
            if self.current_scroll_offset > 5:
                arrow_y = start_y - 15
                pygame.draw.polygon(self.screen, arrow_color, [
                    (arrow_x, arrow_y - arrow_size // 2),
                    (arrow_x - arrow_size // 2, arrow_y + arrow_size // 2),
                    (arrow_x + arrow_size // 2, arrow_y + arrow_size // 2)
                ])
            
            extra_bottom_space = 100

            # Down arrow if not at bottom - check against content height without extra space
            content_only_height = total_h + extra_bottom_space
            if self.current_scroll_offset < (content_only_height - area_h) - 5:
                arrow_y = start_y + area_h + 10
                pygame.draw.polygon(self.screen, arrow_color, [
                    (arrow_x, arrow_y + arrow_size // 2),
                    (arrow_x - arrow_size // 2, arrow_y - arrow_size // 2),
                    (arrow_x + arrow_size // 2, arrow_y - arrow_size // 2)
                ])

        # Content area with proper padding and space for scrollbar
        scrollbar_space = scrollbar_width + scrollbar_margin * 2 if total_h > area_h else 0
        content = pygame.Rect(px + content_padding, start_y, 
                             w - (content_padding * 2) - scrollbar_space, area_h)
        bg = pygame.Surface((content.width, content.height), pygame.SRCALPHA)
        bg.fill((20, 20, 30, 200))
        pygame.draw.rect(bg, (255, 255, 255, 30), bg.get_rect(), border_radius=10)  # Dimmed border
        self.screen.blit(bg, content.topleft)
        pygame.draw.rect(self.screen, (120, 120, 160), content, 2, border_radius=10)  # Dimmed border
        
        # Content clipping with internal padding - ensure text doesn't get cut off
        internal_padding = 15
        clip_rect = pygame.Rect(content.x + internal_padding, content.y + internal_padding, 
                               content.width - (internal_padding * 2), content.height - (internal_padding * 2))
        
        self.screen.set_clip(clip_rect)

        def draw_button(rect, base_col, hover, text, is_listening=False):
            """Enhanced button drawing with animations"""
            mouse_pos = pygame.mouse.get_pos()
            is_hovered = rect.collidepoint(mouse_pos) or hover
            is_pressed = pygame.mouse.get_pressed()[0] and is_hovered
            
            # Use enhanced button drawing
            scaled_rect = self.draw_enhanced_button(rect, base_col, text, self.font_chat, 
                                                is_hovered, is_pressed, is_listening)
            
            # Text rendering with enhanced effects
            edge_padding = 10
            ts = self.font_chat.render(text, True, (255, 255, 255))
            
            # Enhanced text scrolling for long text
            if ts.get_width() > rect.width - (edge_padding * 2):
                available_width = rect.width - (edge_padding * 2)
                scroll_speed = 100
                
                full_circle_distance = ts.get_width() + available_width
                scroll_time = full_circle_distance / scroll_speed
                
                text_hash = hash(text) % 1000 / 1000.0
                offset_time = text_hash * scroll_time
                current_time = (time.time() + offset_time) % scroll_time
                
                scroll_progress = current_time / scroll_time
                text_x = available_width + edge_padding - (full_circle_distance * scroll_progress)
                
                text_clip = pygame.Surface((available_width, rect.height), pygame.SRCALPHA)
                
                # Add glow effect to scrolling text
                if is_listening:
                    glow_text = self.font_chat.render(text, True, self.get_rgb_color(2.0, 0.8))
                    text_clip.blit(glow_text, (text_x - edge_padding + 1, (rect.height - ts.get_height()) // 2 + 1))
                
                text_clip.blit(ts, (text_x - edge_padding, (rect.height - ts.get_height()) // 2))
                self.screen.blit(text_clip, (rect.x + edge_padding, rect.y))
            else:
                text_y = (rect.height - ts.get_height()) // 2
                text_x = (rect.width - ts.get_width()) // 2
                
                # Add glow for centered text if listening
                if is_listening:
                    glow_text = self.font_chat.render(text, True, self.get_rgb_color(2.0, 0.8))
                    self.screen.blit(glow_text, (rect.x + text_x + 1, rect.y + text_y + 1))
                
                self.screen.blit(ts, (rect.x + text_x, rect.y + text_y))

        # Close button with proper padding
        cr = pygame.Rect(px + w - 35 - content_padding, py + panel_padding, 30, 30)
        interactive_elements['close_button'] = cr
        close_hover = cr.collidepoint(pygame.mouse.get_pos())
        draw_button(cr, (200, 80, 80), close_hover, 'X')  # Dimmed red

        # Draw keybind categories and items with proper spacing
        dy = start_y - self.current_scroll_offset + internal_padding
        for cat, acts in KEYBIND_CATEGORIES.items():
            if dy > start_y + area_h + 5:
                break
            
            # Category title with dimmed glow
            cat_color = self.get_rgb_color(1.0, 0.6)  # Dimmed brightness
            self.draw_glowing_text(cat, self.font_small, (content.x + internal_padding + 10, dy), cat_color, glow_size=1)
            dy += KEYBIND_MENU_SETTINGS['category_height']
            
            for act in acts:
                if dy > start_y + area_h:
                    break
                
                nm = KEYBIND_DISPLAY_NAMES.get(act, act)
                pos = (content.x + internal_padding + 20, dy + 15)
                
                # Check for conflicts
                conflicts = keybind_manager.has_conflicts()
                is_conflicted = act in conflicts or any(act in conf_list for conf_list in conflicts.values())
                
                if listening_action == act:
                    # Pulsing effect for listening action
                    pulse_intensity = 0.5 + 0.3 * math.sin(time.time() * 4)
                    pulse_color = tuple(int(c * pulse_intensity) for c in KEYBIND_MENU_SETTINGS['listening_color'])
                    self.draw_glowing_text(nm, self.font_chat, pos, pulse_color, 1)
                elif is_conflicted:
                    # Red highlight for conflicted keybinds
                    conflict_color = (255, 100, 100)
                    self.draw_glowing_text(nm, self.font_chat, pos, conflict_color, 2)
                    # Draw warning icon
                    warning_x = pos[0] - 15
                    warning_y = pos[1] + 2
                    pygame.draw.polygon(self.screen, (255, 200, 0), [
                        (warning_x, warning_y + 8),
                        (warning_x + 4, warning_y),
                        (warning_x + 8, warning_y + 8)
                    ])
                    pygame.draw.circle(self.screen, (0, 0, 0), (warning_x + 4, warning_y + 5), 1)
                else:
                    color = (255, 255, 255)
                    self.draw_glowing_text(nm, self.font_chat, pos, color, 0)

                # Keybind button with proper spacing from content edge
                button_margin = 20  # Space from right edge of content area
                br = pygame.Rect(content.x + content.width - 140 - button_margin, dy + 8, 140, 35)
                val = "Press Key..." if listening_action == act else keybind_manager.get_key_display_name(keybind_manager.get_display_key(act))
                is_listening = listening_action == act
                button_color = (200, 180, 80) if is_listening else (60, 60, 60)  # Dimmed colors
                draw_button(br, button_color, br.collidepoint(pygame.mouse.get_pos()), val, is_listening)
                interactive_elements['keybind_buttons'][act] = br
                dy += KEYBIND_MENU_SETTINGS['item_height']
            dy += 15  # Section spacing

        self.screen.set_clip(None)

        # Draw shadows to indicate scrollable content
        if total_h > area_h:
            shadow_height = 20  # Increased shadow height
            shadow_color_base = (0, 0, 0)
            
            # Top shadow if scrolled down
            if self.current_scroll_offset > 5:
                for i in range(shadow_height):
                    alpha = int(120 * (1 - i / shadow_height))  # Stronger fade from 120 to 0
                    shadow_surface = pygame.Surface((content.width, 1), pygame.SRCALPHA)
                    shadow_surface.fill((*shadow_color_base, alpha))
                    self.screen.blit(shadow_surface, (content.x, content.y + i))
            
            # Bottom shadow if not at bottom - only show if there's actual content to scroll to
            content_only_height = total_h - extra_bottom_space
            if self.current_scroll_offset < (content_only_height - area_h) - 5:
                for i in range(shadow_height):
                    alpha = int(120 * (i / shadow_height))  # Stronger fade from 0 to 120
                    shadow_surface = pygame.Surface((content.width, 1), pygame.SRCALPHA)
                    shadow_surface.fill((*shadow_color_base, alpha))
                    self.screen.blit(shadow_surface, (content.x, content.y + content.height - shadow_height + i))

        # Bottom buttons with proper padding
        by = py + h - panel_padding - 40
        bw, bh, sp = 130, 35, 15  # Better button spacing
        bx = px + (w - (bw * 3 + sp * 2)) // 2
        
        reset_text = "Confirm Reset?" if hasattr(self, 'keybind_overlay_handler') and getattr(self.keybind_overlay_handler, 'reset_confirmation', False) else "Reset"
        button_configs = [
            (reset_text, tuple(int(c * 0.8) for c in KEYBIND_MENU_SETTINGS['reset_button_color']), 'reset_button'),
            ('Save', tuple(int(c * 0.8) for c in KEYBIND_MENU_SETTINGS['save_button_color']), 'save_button'),
            ('Cancel', (100, 100, 100), 'cancel_button')  # Dimmed gray
        ]
        
        for txt, col, key in button_configs:
            rr = pygame.Rect(bx, by, bw, bh)
            # Special handling for save button - show "Saved!" briefly if save was clicked
            if key == 'save_button' and hasattr(self, '_save_feedback_time'):
                if time.time() - self._save_feedback_time < 1.0:  # Show for 1 second
                    display_text = "Saved!"
                    button_color = (60, 150, 60)  # Green feedback
                else:
                    display_text = txt
                    button_color = col
            else:
                display_text = txt
                button_color = col
                
            draw_button(rr, button_color, rr.collidepoint(pygame.mouse.get_pos()), display_text)
            interactive_elements[key] = rr
            bx += bw + sp

        return interactive_elements

def trigger_save_feedback(self):
    """Trigger visual feedback for save button"""
    self._save_feedback_time = time.time()


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