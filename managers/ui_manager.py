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
        
        # Button styling
        self.button_corner_radius = 15
        
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
        """Draw the settings menu overlay with enhanced styling"""
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
        button_width = 380  # Extended to accommodate icons and text
        button_height = 65
        button_spacing = 25

        # Calculate starting position below the title
        total_buttons = len(SETTINGS_MENU_OPTIONS)
        total_height = total_buttons * button_height + (total_buttons - 1) * button_spacing
        title_bottom = app.HEIGHT // 2 - 200 + 50  # Title center + approximate title height
        start_y = title_bottom + 30  # Add some spacing below title
        
        # Get mouse position for hover detection
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_button_index = None
        
        # Create buttons with enhanced styling
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
            
            # Draw enhanced button
            self._draw_enhanced_settings_button(rect, option["label"], i)
            
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
    
    def _get_settings_icon_type(self, button_text):
        """Get icon type based on button text"""
        text_lower = button_text.lower()
        
        if "quit" in text_lower or "exit" in text_lower:
            return "quit"
        elif "audio" in text_lower or "sound" in text_lower or "volume" in text_lower:
            return "audio"
        elif "video" in text_lower or "display" in text_lower or "graphics" in text_lower:
            return "video"
        elif "control" in text_lower or "input" in text_lower or "key" in text_lower:
            return "controls"
        elif "game" in text_lower or "gameplay" in text_lower:
            return "gameplay"
        elif "back" in text_lower or "return" in text_lower or "close" in text_lower:
            return "back"
        elif "reset" in text_lower or "default" in text_lower:
            return "reset"
        elif "save" in text_lower or "apply" in text_lower:
            return "save"
        else:
            return "generic"
    
    def _draw_settings_icon(self, surface, icon_type, rect, color):
        """Draw clean, modern icons for settings buttons"""
        # Icon positioning - left side of button with proper padding
        icon_size = 20
        icon_padding = 20
        icon_x = rect.x + icon_padding
        icon_y = rect.centery
        
        # Set line thickness for consistent look
        line_width = 2
        
        if icon_type == "audio":
            # Single quaver note (eighth note)
            note_x = icon_x + 8
            note_y = icon_y + 3
            
            # Note head (filled circle)
            pygame.draw.circle(surface, color, (note_x, note_y), 4)
            
            # Note stem (vertical line going up)
            pygame.draw.line(surface, color, 
                        (note_x + 4, note_y), 
                        (note_x + 4, note_y - 12), line_width + 1)
            
            # Flag/beam (curved hook at top of stem)
            flag_points = [
                (note_x + 4, note_y - 12),
                (note_x + 8, note_y - 10),
                (note_x + 10, note_y - 8),
                (note_x + 8, note_y - 6)
            ]
            pygame.draw.lines(surface, color, False, flag_points, line_width)
            
        elif icon_type == "video":
            # Clean monitor icon
            # Screen outline
            screen_rect = pygame.Rect(icon_x, icon_y - 7, 16, 11)
            pygame.draw.rect(surface, color, screen_rect, line_width)
            
            # Screen content (small rectangle inside)
            content_rect = pygame.Rect(icon_x + 3, icon_y - 4, 10, 5)
            pygame.draw.rect(surface, color, content_rect)
            
            # Stand base
            stand_width = 8
            stand_x = icon_x + (16 - stand_width) // 2
            pygame.draw.line(surface, color, 
                           (stand_x, icon_y + 5), 
                           (stand_x + stand_width, icon_y + 5), line_width + 1)
            
            # Stand stem
            pygame.draw.line(surface, color, 
                           (icon_x + 8, icon_y + 4), 
                           (icon_x + 8, icon_y + 5), line_width)
            
        elif icon_type == "controls":
            # Modern gamepad icon
            # Main body (rounded rectangle shape using lines)
            body_rect = pygame.Rect(icon_x + 1, icon_y - 5, 14, 10)
            pygame.draw.rect(surface, color, body_rect, line_width, border_radius=3)
            
            # D-pad (left side) - cross shape
            # Horizontal bar
            pygame.draw.line(surface, color, 
                           (icon_x + 3, icon_y), 
                           (icon_x + 7, icon_y), line_width + 1)
            # Vertical bar
            pygame.draw.line(surface, color, 
                           (icon_x + 5, icon_y - 2), 
                           (icon_x + 5, icon_y + 2), line_width + 1)
            
            # Action buttons (right side) - clean circles
            button_positions = [
                (icon_x + 11, icon_y - 2),  # Top button
                (icon_x + 13, icon_y),      # Right button
                (icon_x + 11, icon_y + 2),  # Bottom button
                (icon_x + 9, icon_y)        # Left button
            ]
            
            for btn_x, btn_y in button_positions:
                pygame.draw.circle(surface, color, (btn_x, btn_y), 2, line_width)
            
        elif icon_type == "gameplay":
            # Clean gear icon
            center_x, center_y = icon_x + 8, icon_y
            outer_radius = 8
            inner_radius = 3
            teeth_count = 8
            
            # Draw gear teeth as lines radiating outward
            for i in range(teeth_count):
                angle = math.radians(i * (360 / teeth_count))
                
                # Inner point (on circle)
                inner_x = center_x + math.cos(angle) * (inner_radius + 2)
                inner_y = center_y + math.sin(angle) * (inner_radius + 2)
                
                # Outer point (tooth tip)
                outer_x = center_x + math.cos(angle) * outer_radius
                outer_y = center_y + math.sin(angle) * outer_radius
                
                pygame.draw.line(surface, color, (inner_x, inner_y), (outer_x, outer_y), line_width)
            
            # Center circle
            pygame.draw.circle(surface, color, (center_x, center_y), inner_radius, line_width)
            
        elif icon_type == "back":
            # Clean left arrow
            arrow_size = 6
            # Arrow shaft
            pygame.draw.line(surface, color, 
                           (icon_x + 2, icon_y), 
                           (icon_x + 14, icon_y), line_width + 1)
            
            # Arrow head (two lines forming a point)
            pygame.draw.line(surface, color, 
                           (icon_x + 2, icon_y), 
                           (icon_x + 2 + arrow_size, icon_y - arrow_size), line_width + 1)
            pygame.draw.line(surface, color, 
                           (icon_x + 2, icon_y), 
                           (icon_x + 2 + arrow_size, icon_y + arrow_size), line_width + 1)
            
        elif icon_type == "reset":
            # Clean refresh/circular arrow
            center_x, center_y = icon_x + 8, icon_y
            radius = 7
            
            # Main arc (3/4 circle)
            arc_rect = (center_x - radius, center_y - radius, radius * 2, radius * 2)
            pygame.draw.arc(surface, color, arc_rect, 
                           math.pi/4, 2*math.pi - math.pi/8, line_width + 1)
            
            # Arrow head at the end
            tip_angle = -math.pi/8
            tip_x = center_x + math.cos(tip_angle) * radius
            tip_y = center_y + math.sin(tip_angle) * radius
            
            # Two lines forming arrow head
            head_size = 4
            pygame.draw.line(surface, color, 
                           (tip_x, tip_y), 
                           (tip_x - head_size, tip_y - head_size/2), line_width)
            pygame.draw.line(surface, color, 
                           (tip_x, tip_y), 
                           (tip_x - head_size/2, tip_y + head_size), line_width)
            
        elif icon_type == "save":
            # Modern save/download icon
            # Downward arrow
            arrow_x = icon_x + 8
            arrow_top = icon_y - 6
            arrow_bottom = icon_y + 2
            
            # Arrow shaft
            pygame.draw.line(surface, color, 
                           (arrow_x, arrow_top), 
                           (arrow_x, arrow_bottom), line_width + 1)
            
            # Arrow head
            head_size = 4
            pygame.draw.line(surface, color, 
                           (arrow_x, arrow_bottom), 
                           (arrow_x - head_size, arrow_bottom - head_size), line_width + 1)
            pygame.draw.line(surface, color, 
                           (arrow_x, arrow_bottom), 
                           (arrow_x + head_size, arrow_bottom - head_size), line_width + 1)
            
            # Base line (representing ground/save location)
            pygame.draw.line(surface, color, 
                           (icon_x + 2, icon_y + 6), 
                           (icon_x + 14, icon_y + 6), line_width + 1)
            
        elif icon_type == "quit":
            # X mark for quit/exit
            line_width = 3
            offset = icon_size//3
            
            # Draw X with two lines
            pygame.draw.line(surface, color, 
                           (icon_x + offset, icon_y - offset), 
                           (icon_x + icon_size - offset, icon_y + offset), 
                           line_width)
            pygame.draw.line(surface, color, 
                           (icon_x + offset, icon_y + offset), 
                           (icon_x + icon_size - offset, icon_y - offset), 
                           line_width)
            
        else:  # generic
            # Simple settings/options icon (three horizontal lines)
            line_length = 12
            line_spacing = 3
            start_x = icon_x + 2
            
            for i in range(3):
                line_y = icon_y - line_spacing + (i * line_spacing)
                # Vary line lengths slightly for visual interest
                current_length = line_length - (i % 2) * 2
                pygame.draw.line(surface, color, 
                               (start_x, line_y), 
                               (start_x + current_length, line_y), line_width)
    
    def _draw_floral_decoration(self, surface, rect, color, alpha=100):
        """Draw floral decorations on button corners"""
        decoration_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Corner decorations
        corner_size = 12
        petal_size = 6
        
        corners = [
            (corner_size, corner_size),  # Top-left
            (rect.width - corner_size, corner_size),  # Top-right
            (corner_size, rect.height - corner_size),  # Bottom-left
            (rect.width - corner_size, rect.height - corner_size)  # Bottom-right
        ]
        
        for corner_x, corner_y in corners:
            # Draw small floral pattern
            center = (corner_x, corner_y)
            
            # Draw petals around center
            for i in range(4):
                angle = math.radians(i * 90)
                petal_x = corner_x + math.cos(angle) * petal_size
                petal_y = corner_y + math.sin(angle) * petal_size
                
                # Draw petal as small circle
                petal_color = (*color, alpha)
                petal_surf = pygame.Surface((petal_size*2, petal_size*2), pygame.SRCALPHA)
                pygame.draw.circle(petal_surf, petal_color, (petal_size, petal_size), petal_size//2)
                decoration_surf.blit(petal_surf, (petal_x - petal_size, petal_y - petal_size))
            
            # Center dot
            center_color = (*color, alpha + 50)
            pygame.draw.circle(decoration_surf, center_color, center, 2)
        
        # Edge decorations (small dots along the border)
        dot_spacing = 20
        dot_size = 2
        
        # Top and bottom edges
        for x in range(dot_spacing, rect.width - dot_spacing, dot_spacing):
            dot_color = (*color, alpha//2)
            # Top edge
            pygame.draw.circle(decoration_surf, dot_color, (x, 5), dot_size)
            # Bottom edge
            pygame.draw.circle(decoration_surf, dot_color, (x, rect.height - 5), dot_size)
        
        # Left and right edges
        for y in range(dot_spacing, rect.height - dot_spacing, dot_spacing):
            dot_color = (*color, alpha//2)
            # Left edge
            pygame.draw.circle(decoration_surf, dot_color, (5, y), dot_size)
            # Right edge
            pygame.draw.circle(decoration_surf, dot_color, (rect.width - 5, y), dot_size)
        
        surface.blit(decoration_surf, (0, 0))
    
    def _draw_rounded_rect(self, surface, color, rect, corner_radius):
        """Draw a rounded rectangle"""
        # Draw main rectangle
        main_rect = pygame.Rect(rect.x, rect.y + corner_radius, rect.width, rect.height - 2*corner_radius)
        pygame.draw.rect(surface, color, main_rect)
        
        # Draw top and bottom rectangles
        top_rect = pygame.Rect(rect.x + corner_radius, rect.y, rect.width - 2*corner_radius, corner_radius)
        bottom_rect = pygame.Rect(rect.x + corner_radius, rect.bottom - corner_radius, rect.width - 2*corner_radius, corner_radius)
        pygame.draw.rect(surface, color, top_rect)
        pygame.draw.rect(surface, color, bottom_rect)
        
        # Draw corner circles
        pygame.draw.circle(surface, color, (rect.x + corner_radius, rect.y + corner_radius), corner_radius)
        pygame.draw.circle(surface, color, (rect.right - corner_radius, rect.y + corner_radius), corner_radius)
        pygame.draw.circle(surface, color, (rect.x + corner_radius, rect.bottom - corner_radius), corner_radius)
        pygame.draw.circle(surface, color, (rect.right - corner_radius, rect.bottom - corner_radius), corner_radius)
    
    def _draw_gradient_rounded_button(self, surface, color1, color2, size, corner_radius):
        """Draw a rounded button with gradient background"""
        width, height = size
        
        for y in range(height):
            # Create vertical gradient
            progress = y / height
            
            # Interpolate between colors
            r = int(color1[0] * (1 - progress) + color2[0] * progress)
            g = int(color1[1] * (1 - progress) + color2[1] * progress)
            b = int(color1[2] * (1 - progress) + color2[2] * progress)
            color = (r, g, b)
            
            # Draw line with rounded corners consideration
            if y < corner_radius:
                # Top rounded section
                line_width = self._get_rounded_line_width(y, corner_radius, width)
                line_start = (width - line_width) // 2
                if line_width > 0:
                    pygame.draw.line(surface, color, (line_start, y), (line_start + line_width, y))
            elif y >= height - corner_radius:
                # Bottom rounded section
                dist_from_bottom = height - y - 1
                line_width = self._get_rounded_line_width(dist_from_bottom, corner_radius, width)
                line_start = (width - line_width) // 2
                if line_width > 0:
                    pygame.draw.line(surface, color, (line_start, y), (line_start + line_width, y))
            else:
                # Middle section - full width
                pygame.draw.line(surface, color, (0, y), (width, y))
    
    def _get_rounded_line_width(self, distance_from_edge, corner_radius, full_width):
        """Calculate line width for rounded corners"""
        if distance_from_edge >= corner_radius:
            return full_width
        
        # Use circle equation to determine width
        y_offset = corner_radius - distance_from_edge
        if y_offset >= corner_radius:
            return 0
        
        # Calculate how much of the circle width we have at this y position
        circle_width = 2 * math.sqrt(corner_radius * corner_radius - y_offset * y_offset)
        return int(full_width - 2 * corner_radius + circle_width)
    
    def _draw_rounded_rect_border(self, surface, color, rect, corner_radius, border_width):
        """Draw border for rounded rectangle"""
        # Draw border as multiple rounded rectangles with decreasing size
        for i in range(border_width):
            border_rect = pygame.Rect(
                rect.x + i, 
                rect.y + i, 
                rect.width - 2*i, 
                rect.height - 2*i
            )
            
            if border_rect.width <= 0 or border_rect.height <= 0:
                break
                
            # Draw border outline (not filled)
            self._draw_rounded_rect_outline(surface, color, border_rect, max(1, corner_radius - i))
    
    def _draw_rounded_rect_outline(self, surface, color, rect, corner_radius):
        """Draw outline of rounded rectangle"""
        # Draw the four sides
        # Top
        pygame.draw.line(surface, color, 
                        (rect.x + corner_radius, rect.y), 
                        (rect.right - corner_radius, rect.y))
        # Bottom
        pygame.draw.line(surface, color, 
                        (rect.x + corner_radius, rect.bottom - 1), 
                        (rect.right - corner_radius, rect.bottom - 1))
        # Left
        pygame.draw.line(surface, color, 
                        (rect.x, rect.y + corner_radius), 
                        (rect.x, rect.bottom - corner_radius))
        # Right
        pygame.draw.line(surface, color, 
                        (rect.right - 1, rect.y + corner_radius), 
                        (rect.right - 1, rect.bottom - corner_radius))
        
        # Draw corner arcs (approximated with small lines)
        self._draw_corner_arc(surface, color, rect.x + corner_radius, rect.y + corner_radius, corner_radius, 180, 270)
        self._draw_corner_arc(surface, color, rect.right - corner_radius, rect.y + corner_radius, corner_radius, 270, 360)
        self._draw_corner_arc(surface, color, rect.x + corner_radius, rect.bottom - corner_radius, corner_radius, 90, 180)
        self._draw_corner_arc(surface, color, rect.right - corner_radius, rect.bottom - corner_radius, corner_radius, 0, 90)
    
    def _draw_corner_arc(self, surface, color, center_x, center_y, radius, start_angle, end_angle):
        """Draw a corner arc"""
        points = []
        for angle in range(int(start_angle), int(end_angle) + 1, 2):
            rad = math.radians(angle)
            x = center_x + math.cos(rad) * radius
            y = center_y + math.sin(rad) * radius
            points.append((int(x), int(y)))
        
        if len(points) > 1:
            pygame.draw.lines(surface, color, False, points)
    
    def _draw_enhanced_settings_button(self, rect, text, button_index):
        """Draw enhanced settings button with proper icon and text positioning"""
        anim = self.button_animations[button_index]
        is_hovered = self.hovered_button_index == button_index
        
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
        
        # Define color schemes (same as title screen)
        if is_hovered:
            # Enhanced colors for hover
            bg_color1 = (25, 35, 55)    # Dark blue-gray
            bg_color2 = (15, 25, 45)    # Darker blue-gray
            border_color = (120, 180, 255)  # Bright blue
            text_color = (220, 240, 255)    # Light blue-white
            icon_color = (120, 180, 255)
            decoration_color = (80, 140, 200)
        else:
            # Normal state - dark background with complementary colors
            bg_color1 = (30, 25, 45)    # Dark purple-gray
            bg_color2 = (20, 15, 35)    # Darker purple-gray
            border_color = (100, 120, 160)  # Muted blue
            text_color = (200, 220, 255)    # Light blue-white
            icon_color = (150, 170, 200)
            decoration_color = (70, 85, 120)
        
        # Create button surface for rounded corners
        button_surf = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
        
        # Draw gradient background with rounded corners
        self._draw_gradient_rounded_button(button_surf, bg_color1, bg_color2, scaled_rect.size, self.button_corner_radius)
        
        # Add floral decorations
        self._draw_floral_decoration(button_surf, pygame.Rect(0, 0, scaled_rect.width, scaled_rect.height), 
                                   decoration_color, alpha=60 + int(anim["glow"] * 40))
        
        # Draw border with rounded corners
        border_width = 2 + int(anim["glow"] * 2)
        self._draw_rounded_rect_border(button_surf, border_color, 
                                     pygame.Rect(0, 0, scaled_rect.width, scaled_rect.height),
                                     self.button_corner_radius, border_width)
        
        # Blit button surface to screen
        self.screen.blit(button_surf, scaled_rect)
        
        # Draw glow effect around button
        if anim["glow"] > 0:
            self._draw_button_glow(scaled_rect, border_color, anim["glow"])
        
        # Get and draw icon (positioned on left side with proper padding)
        icon_type = self._get_settings_icon_type(text)
        self._draw_settings_icon(self.screen, icon_type, scaled_rect, icon_color)
        
        # Draw button text (positioned to the right of icon with proper spacing)
        text_surf = self.font_small.render(text, True, text_color)
        text_rect = text_surf.get_rect()
        
        # Position text to avoid icon overlap
        icon_area_width = 70  # Increased space reserved for icon
        text_rect.x = scaled_rect.x + icon_area_width
        text_rect.centery = scaled_rect.centery
        
        # Ensure text doesn't go beyond button bounds
        max_text_width = scaled_rect.width - icon_area_width - 25  # Increased right padding
        if text_rect.width > max_text_width:
            # If text is too long, center it without icon consideration
            text_rect.centerx = scaled_rect.centerx
        
        self.screen.blit(text_surf, text_rect)
    
    def _draw_button_glow(self, rect, color, intensity):
        """Draw glow effect around button"""
        glow_size = int(12 * intensity)
        glow_alpha = int(80 * intensity)
        
        # Create glow surface
        glow_surf = pygame.Surface((rect.width + glow_size * 2, rect.height + glow_size * 2), pygame.SRCALPHA)
        
        # Draw multiple glow layers
        for i in range(glow_size):
            alpha = int(glow_alpha * (1 - i / glow_size))
            glow_color = (*color, alpha)
            
            glow_rect = pygame.Rect(glow_size - i, glow_size - i, 
                                  rect.width + i * 2, rect.height + i * 2)
            
            # Draw rounded glow
            self._draw_rounded_rect(glow_surf, glow_color, glow_rect, self.button_corner_radius + i)
        
        # Blit glow surface
        glow_pos = (rect.x - glow_size, rect.y - glow_size)
        self.screen.blit(glow_surf, glow_pos)

    def _draw_button(self, rect: pygame.Rect, text: str, bg_color=(70, 70, 70), border_color=(255, 255, 255), text_color=(255, 255, 255)):
        """Draw a button with text and custom colors (legacy method)"""
        pygame.draw.rect(self.screen, bg_color, rect)
        pygame.draw.rect(self.screen, border_color, rect, 2)
        text_surf = self.font_small.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)
    
    def _draw_animated_settings_button(self, rect, text, button_index):
        """Legacy method - now uses enhanced version"""
        self._draw_enhanced_settings_button(rect, text, button_index)

    def _draw_gradient_button(self, rect, base_color, glow_intensity):
        """Legacy gradient button method"""
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