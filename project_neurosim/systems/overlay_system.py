"""
Overlay system for displaying version information, credits, and other modal content
"""
import pygame
from typing import Optional, Tuple, List
import textwrap


class OverlaySystem:
    """Manages overlay screens like version info and credits"""
    
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
        
        # Colors
        self.bg_color = (0, 0, 0, 180)  # Semi-transparent black
        self.text_color = (255, 255, 255)
        self.accent_color = (0, 255, 255)  # Cyan for highlights
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
    
    def draw_version_overlay(self) -> Optional[pygame.Rect]:
        """
        Draw the version information overlay
        
        Returns:
            pygame.Rect: Close button rect for click detection, or None
        """
        # Create semi-transparent background
        overlay_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay_surface.set_alpha(180)
        overlay_surface.fill((0, 0, 0))
        self.screen.blit(overlay_surface, (0, 0))
        
        # Calculate content area
        content_width = 600
        content_height = 500
        content_x = (self.screen.get_width() - content_width) // 2
        content_y = (self.screen.get_height() - content_height) // 2
        
        # Draw content background
        content_rect = pygame.Rect(content_x, content_y, content_width, content_height)
        pygame.draw.rect(self.screen, (40, 40, 40), content_rect)
        pygame.draw.rect(self.screen, self.accent_color, content_rect, 3)
        
        # Draw close button (X)
        close_button_size = 30
        close_x = content_x + content_width - close_button_size - 10
        close_y = content_y + 10
        close_rect = pygame.Rect(close_x, close_y, close_button_size, close_button_size)
        
        # Check if mouse is hovering over close button
        mouse_pos = pygame.mouse.get_pos()
        close_hover = close_rect.collidepoint(mouse_pos)
        close_color = self.button_hover_color if close_hover else self.button_color
        
        pygame.draw.rect(self.screen, close_color, close_rect)
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
        
        # Draw version content
        current_y = content_y + 20
        
        # Title
        title_surface = self.font_large.render(self.version_info["title"], True, self.accent_color)
        title_x = content_x + (content_width - title_surface.get_width()) // 2
        self.screen.blit(title_surface, (title_x, current_y))
        current_y += title_surface.get_height() + 10
        
        # Version
        version_surface = self.font_small.render(self.version_info["version"], True, self.text_color)
        version_x = content_x + (content_width - version_surface.get_width()) // 2
        self.screen.blit(version_surface, (version_x, current_y))
        current_y += version_surface.get_height() + 20
        
        # System info
        info_items = [
            f"Build Date: {self.version_info['build_date']}",
            f"Engine: {self.version_info['engine']}",
            f"Python: {self.version_info['python_version']}"
        ]
        
        for item in info_items:
            item_surface = self.font_chat.render(item, True, self.text_color)
            item_x = content_x + 40
            self.screen.blit(item_surface, (item_x, current_y))
            current_y += item_surface.get_height() + 8
        
        current_y += 20
        
        # Features section
        features_title = self.font_small.render("KEY FEATURES:", True, self.accent_color)
        self.screen.blit(features_title, (content_x + 40, current_y))
        current_y += features_title.get_height() + 10
        
        for feature in self.version_info["features"]:
            feature_surface = self.font_chat.render(f"• {feature}", True, self.text_color)
            self.screen.blit(feature_surface, (content_x + 60, current_y))
            current_y += feature_surface.get_height() + 6
        
        # Instructions
        current_y = content_y + content_height - 40
        instruction_text = "Press ESC or click X to close"
        instruction_surface = self.font_chat.render(instruction_text, True, (150, 150, 150))
        instruction_x = content_x + (content_width - instruction_surface.get_width()) // 2
        self.screen.blit(instruction_surface, (instruction_x, current_y))
        
        return close_rect
    
    def draw_credits_overlay(self) -> Optional[pygame.Rect]:
        """
        Draw the credits overlay
        
        Returns:
            pygame.Rect: Close button rect for click detection, or None
        """
        # Create semi-transparent background
        overlay_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay_surface.set_alpha(180)
        overlay_surface.fill((0, 0, 0))
        self.screen.blit(overlay_surface, (0, 0))
        
        # Calculate content area (wider for credits)
        content_width = 700
        content_height = 600
        content_x = (self.screen.get_width() - content_width) // 2
        content_y = (self.screen.get_height() - content_height) // 2
        
        # Draw content background
        content_rect = pygame.Rect(content_x, content_y, content_width, content_height)
        pygame.draw.rect(self.screen, (40, 40, 40), content_rect)
        pygame.draw.rect(self.screen, self.accent_color, content_rect, 3)
        
        # Draw close button (X)
        close_button_size = 30
        close_x = content_x + content_width - close_button_size - 10
        close_y = content_y + 10
        close_rect = pygame.Rect(close_x, close_y, close_button_size, close_button_size)
        
        # Check if mouse is hovering over close button
        mouse_pos = pygame.mouse.get_pos()
        close_hover = close_rect.collidepoint(mouse_pos)
        close_color = self.button_hover_color if close_hover else self.button_color
        
        pygame.draw.rect(self.screen, close_color, close_rect)
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
        
        # Title
        title_surface = self.font_large.render(self.credits_info["title"], True, self.accent_color)
        title_x = content_x + (content_width - title_surface.get_width()) // 2
        self.screen.blit(title_surface, (title_x, current_y))
        current_y += title_surface.get_height() + 20
        
        # Credits sections
        for section in self.credits_info["sections"]:
            # Section category
            category_surface = self.font_small.render(section["category"], True, self.accent_color)
            self.screen.blit(category_surface, (content_x + 40, current_y))
            current_y += category_surface.get_height() + 8
            
            # Section entries
            for entry in section["entries"]:
                entry_surface = self.font_chat.render(f"• {entry}", True, self.text_color)
                self.screen.blit(entry_surface, (content_x + 60, current_y))
                current_y += entry_surface.get_height() + 4
            
            current_y += 15  # Space between sections
        
        # Instructions
        instruction_y = content_y + content_height - 40
        instruction_text = "Press ESC or click X to close"
        instruction_surface = self.font_chat.render(instruction_text, True, (150, 150, 150))
        instruction_x = content_x + (content_width - instruction_surface.get_width()) // 2
        self.screen.blit(instruction_surface, (instruction_x, instruction_y))
        
        return close_rect
    
    def draw_corner_version(self):
        """Draw version number in corner with semi-transparent background"""
        version_text = self.version_info["version"]
        padding = 10
        
        # Render text
        version_surface = self.font_chat.render(version_text, True, self.text_color)
        text_width = version_surface.get_width()
        text_height = version_surface.get_height()
        
        # Position in bottom-right corner
        bg_width = text_width + padding * 2
        bg_height = text_height + padding * 2
        bg_x = self.screen.get_width() - bg_width - 10
        bg_y = self.screen.get_height() - bg_height - 10
        
        # Draw semi-transparent background
        bg_surface = pygame.Surface((bg_width, bg_height))
        bg_surface.set_alpha(120)
        bg_surface.fill((0, 0, 0))
        self.screen.blit(bg_surface, (bg_x, bg_y))
        
        # Draw border
        bg_rect = pygame.Rect(bg_x, bg_y, bg_width, bg_height)
        pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 1)
        
        # Draw text
        text_x = bg_x + padding
        text_y = bg_y + padding
        self.screen.blit(version_surface, (text_x, text_y))
    
    def handle_overlay_click(self, pos: Tuple[int, int], overlay_type: str) -> bool:
        """
        Handle clicks on overlay elements
        
        Args:
            pos: Mouse click position (x, y)
            overlay_type: Type of overlay ("version" or "credits")
            
        Returns:
            bool: True if overlay should be closed, False otherwise
        """
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
    """Generic modal overlay for displaying information"""
    
    def __init__(self, screen: pygame.Surface, title: str, content: List[str], 
                 font_large: pygame.font.Font, font_small: pygame.font.Font):
        """
        Initialize a generic modal overlay
        
        Args:
            screen: Game screen surface
            title: Modal title
            content: List of content lines
            font_large: Large font for title
            font_small: Small font for content
        """
        self.screen = screen
        self.title = title
        self.content = content
        self.font_large = font_large
        self.font_small = font_small
        
        self.bg_color = (0, 0, 0, 180)
        self.text_color = (255, 255, 255)
        self.accent_color = (0, 255, 255)
        self.button_color = (60, 60, 60)
        self.button_hover_color = (80, 80, 80)
    
    def draw(self) -> Optional[pygame.Rect]:
        """
        Draw the modal overlay
        
        Returns:
            pygame.Rect: Close button rect for click detection
        """
        # Create semi-transparent background
        overlay_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay_surface.set_alpha(180)
        overlay_surface.fill((0, 0, 0))
        self.screen.blit(overlay_surface, (0, 0))
        
        # Calculate content dimensions
        max_width = 600
        line_height = self.font_small.get_height() + 5
        content_height = len(self.content) * line_height + 100  # Extra space for title and padding
        
        content_x = (self.screen.get_width() - max_width) // 2
        content_y = (self.screen.get_height() - content_height) // 2
        
        # Draw content background
        content_rect = pygame.Rect(content_x, content_y, max_width, content_height)
        pygame.draw.rect(self.screen, (40, 40, 40), content_rect)
        pygame.draw.rect(self.screen, self.accent_color, content_rect, 3)
        
        # Draw close button
        close_button_size = 30
        close_x = content_x + max_width - close_button_size - 10
        close_y = content_y + 10
        close_rect = pygame.Rect(close_x, close_y, close_button_size, close_button_size)
        
        mouse_pos = pygame.mouse.get_pos()
        close_hover = close_rect.collidepoint(mouse_pos)
        close_color = self.button_hover_color if close_hover else self.button_color
        
        pygame.draw.rect(self.screen, close_color, close_rect)
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
        
        # Draw title
        current_y = content_y + 20
        title_surface = self.font_large.render(self.title, True, self.accent_color)
        title_x = content_x + (max_width - title_surface.get_width()) // 2
        self.screen.blit(title_surface, (title_x, current_y))
        current_y += title_surface.get_height() + 20
        
        # Draw content
        for line in self.content:
            line_surface = self.font_small.render(line, True, self.text_color)
            self.screen.blit(line_surface, (content_x + 20, current_y))
            current_y += line_height
        
        return close_rect