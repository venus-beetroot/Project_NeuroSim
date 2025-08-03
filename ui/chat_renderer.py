import pygame
from typing import List, Tuple, TYPE_CHECKING
import sys
import os
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions import app

if TYPE_CHECKING:
    from managers.ui_manager import UIManager
    from managers.chat_manager import ChatManager
    from entities.npc import NPC

class ChatRenderer:
    """Handles chat box rendering with speech bubbles and smooth scrolling"""
    
    def __init__(self, ui_manager: 'UIManager'):
        self.ui = ui_manager
        self.loading_rotation = 0  # For spinning loading icon
        self.thinking_animation_timer = 0  # For thinking dots animation
        self.thinking_dots = 0  # Number of dots to show (0-3)
        
        # Lock animation variables (kept for potential future use)
        self.lock_pulse_timer = 0
        self.lock_alpha = 0

        self.cursor_blink_timer = 0
        self.cursor_visible = True
        
        # Auto-scroll settings
        self.auto_scroll_enabled = True
        self.last_message_count = 0
        
        # Simplified smooth scrolling variables
        self.target_scroll_offset = 0
        self.current_scroll_offset = 0.0
        self.scroll_velocity = 0.0
        self.scroll_smoothing = 0.12  # Slightly reduced for more responsive feel

    
    def draw_chat_interface(self, current_npc: 'NPC', chat_manager: 'ChatManager', player=None):
        """Draw the complete chat interface"""
        self.player = player  # Store player reference for sprite drawing
        self._draw_overlay()
        self._draw_header(current_npc.name)
        self._draw_chat_history(current_npc, chat_manager)
        self._draw_input_box(chat_manager.message, chat_manager)
        
        # Update animations
        self.loading_rotation += 5  # Rotate 5 degrees per frame
        if self.loading_rotation >= 360:
            self.loading_rotation = 0
            
        # Update thinking animation (change dots every 30 frames = 0.5 seconds at 60 FPS)
        self.thinking_animation_timer += 1
        if self.thinking_animation_timer >= 30:
            self.thinking_animation_timer = 0
            self.thinking_dots = (self.thinking_dots + 1) % 4  # Cycle 0,1,2,3,0,1,2,3...
        
        # Update cursor blinking (every 30 frames = 0.5 seconds)
        self.cursor_blink_timer += 1
        if self.cursor_blink_timer >= 30:
            self.cursor_blink_timer = 0
            self.cursor_visible = not self.cursor_visible
        
        # Update smooth scrolling
        self._update_smooth_scrolling(chat_manager)
    
    def _update_smooth_scrolling(self, chat_manager: 'ChatManager'):
        """Update smooth scrolling animation without bounce - pure lerp version"""
        # Initialize scroll offset if it doesn't exist
        if not hasattr(chat_manager, 'scroll_offset') or chat_manager.scroll_offset is None:
            chat_manager.scroll_offset = 0
            self.target_scroll_offset = 0
            self.current_scroll_offset = 0.0
        
        # Update target from chat_manager
        if hasattr(chat_manager, 'target_scroll_offset'):
            self.target_scroll_offset = chat_manager.target_scroll_offset
        else:
            self.target_scroll_offset = chat_manager.scroll_offset
        
        # Get bounds
        max_scroll = 0
        if hasattr(chat_manager, 'content_height') and hasattr(chat_manager, 'view_height'):
            max_scroll = max(0, chat_manager.content_height - chat_manager.view_height)
        
        # Clamp target to valid bounds
        self.target_scroll_offset = max(0, min(self.target_scroll_offset, max_scroll))
        
        # Simple lerp - no velocity, no overshoot possible
        diff = self.target_scroll_offset - self.current_scroll_offset
        if abs(diff) > 0.5:
            # Smooth interpolation toward target
            self.current_scroll_offset += diff * 0.15  # Direct lerp
        else:
            # Snap to target when close
            self.current_scroll_offset = self.target_scroll_offset

        # Update chat_manager's scroll_offset
        chat_manager.scroll_offset = int(self.current_scroll_offset)
    
    def _draw_overlay(self):
        """Draw dark overlay behind chat"""
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.ui.screen.blit(overlay, (0, 0))
    
    def _draw_header(self, npc_name: str):
        """Draw chat header with NPC name"""
        header_text = f"Chat with {npc_name}:"
        header_surf = self.ui.font_large.render(header_text, True, (255, 255, 255))
        header_rect = header_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 400))
        self.ui.screen.blit(header_surf, header_rect)
    
    def _draw_chat_history(self, current_npc: 'NPC', chat_manager: 'ChatManager'):
        """Draw the chat history box with speech bubbles and smooth scrolling"""
        # Box dimensions
        box_width, box_height = app.WIDTH - 350, 450
        box_x, box_y = 175, app.HEIGHT - box_height - 170
        
        # Create complementary gradient background
        gradient_surf = pygame.Surface((box_width, box_height))
        for y in range(box_height):
            progress = y / box_height
            if chat_manager.is_chat_locked():
                # Darker warm gradient when locked
                r = int(25 + progress * 10)  # 25 to 35
                g = int(15 + progress * 10)  # 15 to 25
                b = int(20 + progress * 10)  # 20 to 30
            else:
                # Warm purple/burgundy gradient (complementary to cool blue input)
                r = int(35 + progress * 15)  # 35 to 50
                g = int(20 + progress * 15)  # 20 to 35
                b = int(45 + progress * 20)  # 45 to 65
            
            color = (r, g, b)
            pygame.draw.line(gradient_surf, color, (0, y), (box_width, y))
        
        self.ui.screen.blit(gradient_surf, (box_x, box_y))
        
        # Enhanced border with complementary glow (keeping main border)
        if chat_manager.is_chat_locked():
            border_color = (120, 100, 140)  # Muted purple when locked
            glow_color = (60, 50, 70, 40)
        else:
            border_color = (180, 120, 200)  # Warm purple/magenta
            glow_color = (140, 80, 160, 50)
        
        # Outer glow effect
        for i in range(3):
            glow_rect = pygame.Rect(box_x - i - 1, box_y - i - 1, 
                                box_width + 2*(i + 1), box_height + 2*(i + 1))
            glow_alpha = int(30 * (1 - i/3))
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            glow_surf.fill((*glow_color[:3], glow_alpha))
            self.ui.screen.blit(glow_surf, glow_rect.topleft)
        
        # Main border
        pygame.draw.rect(self.ui.screen, border_color, (box_x, box_y, box_width, box_height), 3)
        
        # Add decorative patterns (removed circles and complex patterns)
        self._draw_chat_decorative_patterns(box_x, box_y, box_width, box_height, chat_manager.is_chat_locked())
        
        # Calculate message dimensions and handle auto-scroll
        padding = 20
        available_width = box_width - 2 * padding
        available_height = box_height - 2 * padding
        
        # Build all messages (including live message)
        all_messages = self._build_all_messages(current_npc.chat_history, chat_manager.live_message)
        
        # Check if new message was added for auto-scroll
        current_message_count = len(all_messages)
        if current_message_count > self.last_message_count and self.auto_scroll_enabled:
            # Auto-scroll to bottom when new message arrives - do it immediately
            chat_manager.scroll_to_bottom = True
            # Prevent any intermediate scrolling calculations
            self.scroll_velocity = 0.0
        self.last_message_count = current_message_count
        
        # Calculate total height needed for all messages
        total_height = self._calculate_total_messages_height(all_messages, available_width)
        
        # Initialize scroll offset if it doesn't exist
        if not hasattr(chat_manager, 'scroll_offset') or chat_manager.scroll_offset is None:
            chat_manager.scroll_offset = 0
            self.target_scroll_offset = 0
            self.current_scroll_offset = 0.0
        
        # Store content dimensions for scrolling
        chat_manager.content_height = total_height
        chat_manager.view_height = available_height
        
        # Handle scrolling with proper bounds checking
        max_scroll = max(0, total_height - available_height)
        
        # Clamp target scroll offset to valid bounds
        if hasattr(chat_manager, 'target_scroll_offset'):
            chat_manager.target_scroll_offset = max(0, min(chat_manager.target_scroll_offset, max_scroll))
            self.target_scroll_offset = chat_manager.target_scroll_offset
        else:
            self.target_scroll_offset = max(0, min(self.target_scroll_offset, max_scroll))
        
        # Auto-scroll to bottom for new messages
        if hasattr(chat_manager, 'scroll_to_bottom') and chat_manager.scroll_to_bottom:
            self.target_scroll_offset = max_scroll
            self.current_scroll_offset = max_scroll  # Instant scroll for new messages
            chat_manager.target_scroll_offset = max_scroll  # Also update chat_manager's target
            chat_manager.scroll_offset = max_scroll  # And current offset
            chat_manager.scroll_to_bottom = False
        
        # Check if we should re-enable auto-scroll (user scrolled to bottom)
        if self.target_scroll_offset >= max_scroll - 10:  # Within 10 pixels of bottom
            self.auto_scroll_enabled = True
        
        # Set clipping for message area - EXPANDED to include label area
        label_margin = 25  # Space above chat box for labels
        clip_rect = pygame.Rect(box_x + padding, box_y + padding, 
                            available_width, available_height)
        original_clip = self.ui.screen.get_clip()
        self.ui.screen.set_clip(clip_rect)
        
        try:
            # Draw messages with proper scrolling
            self._draw_messages_with_bubbles(all_messages, box_x + padding, box_y + padding, 
                                           available_width, available_height, 
                                           chat_manager.scroll_offset, current_npc, 
                                           chat_manager.is_chat_locked())
        finally:
            self.ui.screen.set_clip(original_clip)
        
        # Always draw scrollbar (removed condition)
        self._draw_enhanced_scrollbar(box_x + box_width - 15, box_y + padding,
                        available_height, total_height, available_height,
                        chat_manager.scroll_offset, chat_manager.is_chat_locked())

    def _build_all_messages(self, chat_history: List, live_message: str = None) -> List[Tuple[str, str]]:
        """Build a complete list of messages including live message"""
        all_messages = []
        
        # Add chat history
        for entry in chat_history:
            if isinstance(entry, tuple):
                speaker, message = entry
            else:
                speaker, message = "npc", entry
            all_messages.append((speaker, message))
        
        # Add live message if exists
        if live_message and live_message.strip():
            all_messages.append(("npc", live_message))
        
        return all_messages

    def _calculate_total_messages_height(self, messages: List[Tuple[str, str]], available_width: int) -> int:
        """Calculate the total height needed for all messages including labels"""
        total_height = 0
        message_spacing = 15
        bubble_padding = 20
        label_height = 20  # Height for sender labels
        
        for speaker, message in messages:
            # Calculate bubble width (different for player vs NPC)
            if speaker == "player":
                bubble_width = min(available_width * 0.7, available_width - 100)
            else:
                bubble_width = min(available_width * 0.8, available_width - 80)
            
            # Calculate text area width inside bubble
            text_width = bubble_width - bubble_padding
            
            # Wrap text and calculate height
            wrapped_lines = self._robust_wrap_text(message, self.ui.font_chat, text_width)
            line_height = self.ui.font_chat.get_height() + 2
            message_height = len(wrapped_lines) * line_height + bubble_padding
            
            # Add label height and bubble height
            total_height += label_height + message_height + message_spacing
        
        return total_height

    def _draw_messages_with_bubbles(self, messages: List[Tuple[str, str]], start_x: int, start_y: int,
                                  available_width: int, available_height: int, scroll_offset: int,
                                  current_npc: 'NPC', is_locked: bool = False):
        """Draw messages as speech bubbles with proper positioning"""
        y_offset = start_y - scroll_offset
        message_spacing = 15
        bubble_padding = 20
        label_height = 20  # Space for sender labels
        
        for speaker, message in messages:
            # Skip if this message would be completely above visible area
            if y_offset + 100 < start_y - 25:  # Account for label space
                # Still need to calculate actual height to update y_offset
                if speaker == "player":
                    bubble_width = min(available_width * 0.7, available_width - 100)
                else:
                    bubble_width = min(available_width * 0.8, available_width - 80)
                
                text_width = bubble_width - bubble_padding
                wrapped_lines = self._robust_wrap_text(message, self.ui.font_chat, text_width)
                line_height = self.ui.font_chat.get_height() + 2
                message_height = len(wrapped_lines) * line_height + bubble_padding
                y_offset += label_height + message_height + message_spacing
                continue
            
            # Skip if this message would be completely below visible area
            if y_offset > start_y + available_height:
                break
            
            # Draw the message bubble (now includes label drawing)
            message_height = self._draw_single_message_bubble(speaker, message, start_x, y_offset,
                                                            available_width, current_npc, is_locked)
            y_offset += label_height + message_height + message_spacing

    def _draw_single_message_bubble(self, speaker: str, message: str, start_x: int, y_pos: int,
                                  available_width: int, current_npc: 'NPC', is_locked: bool = False) -> int:
        """Draw a single message as a speech bubble and return its height - NO BORDERS VERSION"""
        bubble_padding = 20
        corner_radius = 15
        label_height = 20  # Space for sender labels
        
        # Draw sender label FIRST (above the bubble)
        self._draw_sender_label(speaker, start_x, y_pos, available_width, current_npc, is_locked)
        
        # Adjust bubble position to be below the label
        bubble_y_pos = y_pos + label_height
        
        # Determine bubble properties based on speaker
        if speaker == "player":
            # Player messages on the right (blue)
            bubble_width = min(available_width * 0.7, available_width - 100)
            bubble_x = start_x + available_width - bubble_width
            if is_locked:
                bubble_color = (40, 60, 100)
                text_color = (150, 170, 200)
            else:
                bubble_color = (70, 130, 180)
                text_color = (255, 255, 255)
        else:
            # NPC messages on the left (gray/green)
            bubble_width = min(available_width * 0.8, available_width - 80)
            bubble_x = start_x
            if is_locked:
                bubble_color = (60, 60, 60)
                text_color = (180, 180, 180)
            else:
                bubble_color = (80, 80, 80)
                text_color = (255, 255, 255)
        
        # Calculate text dimensions
        text_width = bubble_width - bubble_padding
        wrapped_lines = self._robust_wrap_text(message, self.ui.font_chat, text_width)
        line_height = self.ui.font_chat.get_height() + 2
        text_height = len(wrapped_lines) * line_height
        bubble_height = text_height + bubble_padding
        
        # Draw bubble background with rounded corners and gradient (NO BORDER)
        bubble_rect = pygame.Rect(bubble_x, bubble_y_pos, bubble_width, bubble_height)
        self._draw_rounded_rect_with_gradient(self.ui.screen, bubble_color, bubble_rect, corner_radius)
        
        # Draw speech bubble tail (NO BORDER)
        self._draw_bubble_tail(speaker, bubble_x, bubble_y_pos, bubble_width, bubble_height, bubble_color)
        
        # Draw text inside bubble
        text_x = bubble_x + bubble_padding // 2
        text_y = bubble_y_pos + bubble_padding // 2
        
        for i, line in enumerate(wrapped_lines):
            line_surf = self.ui.font_chat.render(line, True, text_color)
            self.ui.screen.blit(line_surf, (text_x, text_y + i * line_height))
        
        return bubble_height

    def _draw_rounded_rect_with_gradient(self, surface, base_color, rect, radius, width=0):
        """Draw a rounded rectangle with gradient effect - NO BORDER VERSION"""
        # Create a surface for the rounded rectangle with per-pixel alpha
        rounded_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Create gradient background
        for y in range(rect.height):
            progress = y / rect.height
            # Subtle gradient from lighter to darker
            r = int(base_color[0] * (1.0 + 0.2 * (1 - progress)))
            g = int(base_color[1] * (1.0 + 0.2 * (1 - progress)))
            b = int(base_color[2] * (1.0 + 0.2 * (1 - progress)))
            
            # Clamp values
            r = min(255, max(0, r))
            g = min(255, max(0, g))
            b = min(255, max(0, b))
            
            gradient_color = (r, g, b)
            pygame.draw.line(rounded_surf, gradient_color, (0, y), (rect.width, y))
        
        # Apply rounded corner mask
        self._apply_rounded_mask(rounded_surf, radius)
        
        surface.blit(rounded_surf, (rect.x, rect.y))
    
    def _apply_rounded_mask(self, surface, radius):
        """Apply rounded corner mask to a surface"""
        width, height = surface.get_size()
        
        # Create mask for each corner
        for x in range(width):
            for y in range(height):
                # Check if pixel is in a corner region
                in_corner = False
                corner_center_x, corner_center_y = 0, 0
                
                if x < radius and y < radius:
                    # Top-left corner
                    corner_center_x, corner_center_y = radius, radius
                    in_corner = True
                elif x >= width - radius and y < radius:
                    # Top-right corner
                    corner_center_x, corner_center_y = width - radius, radius
                    in_corner = True
                elif x < radius and y >= height - radius:
                    # Bottom-left corner
                    corner_center_x, corner_center_y = radius, height - radius
                    in_corner = True
                elif x >= width - radius and y >= height - radius:
                    # Bottom-right corner
                    corner_center_x, corner_center_y = width - radius, height - radius
                    in_corner = True
                
                if in_corner:
                    # Calculate distance from corner center
                    distance = math.sqrt((x - corner_center_x)**2 + (y - corner_center_y)**2)
                    if distance > radius:
                        # Outside radius, make transparent
                        surface.set_at((x, y), (0, 0, 0, 0))

    def _draw_bubble_tail(self, speaker: str, bubble_x: int, bubble_y: int, bubble_width: int, 
                         bubble_height: int, bubble_color):
        """Draw the speech bubble tail pointing to the speaker - NO BORDER VERSION"""
        tail_size = 10
        
        if speaker == "player":
            # Tail on the right side pointing right
            tail_points = [
                (bubble_x + bubble_width, bubble_y + bubble_height // 2),
                (bubble_x + bubble_width + tail_size, bubble_y + bubble_height // 2 - tail_size // 2),
                (bubble_x + bubble_width + tail_size, bubble_y + bubble_height // 2 + tail_size // 2)
            ]
        else:
            # Tail on the left side pointing left
            tail_points = [
                (bubble_x, bubble_y + bubble_height // 2),
                (bubble_x - tail_size, bubble_y + bubble_height // 2 - tail_size // 2),
                (bubble_x - tail_size, bubble_y + bubble_height // 2 + tail_size // 2)
            ]
        
        # Draw filled tail only (no border)
        pygame.draw.polygon(self.ui.screen, bubble_color, tail_points)

    def _draw_sender_label(self, speaker: str, start_x: int, y_pos: int, available_width: int,
                          current_npc: 'NPC', is_locked: bool = False):
        """Draw sender label (You/NPC name) above the bubble area"""
        label_margin = 5
        
        if speaker == "player":
            label_text = "You"
            label_color = (150, 200, 255) if not is_locked else (100, 140, 180)
            # Position label above right side of where bubble will be
            bubble_width = min(available_width * 0.7, available_width - 100)
            bubble_x = start_x + available_width - bubble_width
            label_surf = self.ui.font_small.render(label_text, True, label_color)
            label_x = bubble_x + bubble_width - label_surf.get_width()
            label_y = y_pos
        else:
            label_text = current_npc.name
            label_color = (200, 200, 200) if not is_locked else (140, 140, 140)
            # Position label above left side of where bubble will be
            label_surf = self.ui.font_small.render(label_text, True, label_color)
            label_x = start_x
            label_y = y_pos
        
        self.ui.screen.blit(label_surf, (label_x, label_y))

    def _draw_chat_decorative_patterns(self, box_x, box_y, box_width, box_height, is_locked):
        """Draw simplified decorative patterns for the chat history box - NO CIRCLES"""
        if is_locked:
            pattern_color = (60, 50, 70, 80)
            accent_color = (80, 70, 90, 120)
        else:
            pattern_color = (120, 80, 140, 100)
            accent_color = (160, 100, 180, 150)
        
        pattern_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        
        # Top border decorative line with simple dots
        dot_spacing = 60
        gem_y = 8
        for x in range(dot_spacing, box_width - dot_spacing, dot_spacing):
            # Simple dots instead of diamonds
            pygame.draw.circle(pattern_surf, accent_color, (x, gem_y), 2)
        
        # Side decorative elements - simple vertical lines
        line_height = box_height // 4
        for i in range(3):
            y_start = 50 + i * line_height
            y_end = y_start + line_height - 20
            
            # Left side simple lines
            if y_end < box_height - 20:
                pygame.draw.line(pattern_surf, pattern_color, (8, y_start), (8, y_end), 1)
            
            # Right side simple lines
            if y_end < box_height - 20:
                pygame.draw.line(pattern_surf, pattern_color, (box_width - 8, y_start), (box_width - 8, y_end), 1)
        
        # Bottom decorative border - simple horizontal line
        bottom_y = box_height - 10
        pygame.draw.line(pattern_surf, pattern_color, (20, bottom_y), (box_width - 20, bottom_y), 1)
        
        self.ui.screen.blit(pattern_surf, (box_x, box_y))
    
    def _robust_wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """Robust text wrapping that handles edge cases"""
        if not text.strip():
            return [""]
        
        lines = []
        words = text.split(' ')
        current_line = ""
        
        for word in words:
            # Test if adding this word would exceed width
            test_line = current_line + (" " if current_line else "") + word
            test_width = font.size(test_line)[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                # Current line is full, start new line
                if current_line:
                    lines.append(current_line)
                
                # Check if single word is too long
                if font.size(word)[0] > max_width:
                    # Break long word into chunks
                    while word:
                        # Find max chars that fit
                        for i in range(len(word), 0, -1):
                            if font.size(word[:i])[0] <= max_width:
                                lines.append(word[:i])
                                word = word[i:]
                                break
                        else:
                            # Even single character doesn't fit, force it
                            lines.append(word[0])
                            word = word[1:]
                    current_line = ""
                else:
                    current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [""]
    
    def _draw_input_box(self, message: str, chat_manager: 'ChatManager'):
        """Draw the message input box with enhanced styling and 'You' label"""
        box_width, box_height = app.WIDTH - 350, 100
        box_x, box_y = 175, app.HEIGHT - box_height - 50
        
        # Create gradient background
        gradient_surf = pygame.Surface((box_width, box_height))
        for y in range(box_height):
            progress = y / box_height
            # Dark blue to darker blue gradient
            r = int(15 + progress * 10)  # 15 to 25
            g = int(25 + progress * 15)  # 25 to 40
            b = int(45 + progress * 20)  # 45 to 65
            color = (r, g, b)
            pygame.draw.line(gradient_surf, color, (0, y), (box_width, y))
        
        self.ui.screen.blit(gradient_surf, (box_x, box_y))
        
        # Enhanced border with glow effect
        border_color = (100, 150, 255)
        pygame.draw.rect(self.ui.screen, border_color, (box_x, box_y, box_width, box_height), 3)
        
        # Add inner glow
        inner_glow_color = (50, 100, 200, 30)
        glow_surf = pygame.Surface((box_width - 6, box_height - 6), pygame.SRCALPHA)
        glow_surf.fill(inner_glow_color)
        self.ui.screen.blit(glow_surf, (box_x + 3, box_y + 3))
        
        # Add corner decorations
        self._draw_input_corner_patterns(box_x, box_y, box_width, box_height)
        
        # Draw typed message with cursor
        text_margin_left = 15
        text_margin_right = 140
        text_margin_top = 10  # Back to original since no "You" label
        text_margin_bottom = 35
        
        text_area_x = box_x + text_margin_left
        text_area_y = box_y + text_margin_top
        text_area_width = box_width - text_margin_left - text_margin_right
        text_area_height = box_height - text_margin_top - text_margin_bottom
        
        if message or not chat_manager.waiting_for_response:
            # Set clipping rectangle
            clip_rect = pygame.Rect(text_area_x, text_area_y, text_area_width, text_area_height)
            original_clip = self.ui.screen.get_clip()
            self.ui.screen.set_clip(clip_rect)
            
            try:
                display_message = message if message else ""
                wrapped_lines = self._robust_wrap_text(display_message, self.ui.font_small, text_area_width)
                
                line_height = self.ui.font_small.get_height() + 2
                max_lines = max(1, text_area_height // line_height)
                
                if len(wrapped_lines) > max_lines:
                    wrapped_lines = wrapped_lines[:max_lines]
                    if wrapped_lines:
                        last_line = wrapped_lines[-1]
                        while self.ui.font_small.size(last_line + "...")[0] > text_area_width and len(last_line) > 0:
                            last_line = last_line[:-1]
                        wrapped_lines[-1] = last_line + "..."
                
                # Draw text with enhanced colors
                start_y = text_area_y + (text_area_height - len(wrapped_lines) * line_height) // 2
                
                for i, line in enumerate(wrapped_lines):
                    if line.strip() or i == len(wrapped_lines) - 1:  # Show cursor on last line even if empty
                        # Enhanced text color with slight glow
                        text_color = (150, 200, 255)
                        line_surf = self.ui.font_small.render(line, True, text_color)
                        
                        line_width = line_surf.get_width()
                        text_x = text_area_x + 5  # Left align with small margin
                        text_y = start_y + (i * line_height)
                        
                        if text_y >= text_area_y and text_y + line_height <= text_area_y + text_area_height:
                            self.ui.screen.blit(line_surf, (text_x, text_y))
                            
                            # Draw blinking cursor at end of last line
                            if (i == len(wrapped_lines) - 1 and self.cursor_visible and 
                                not chat_manager.waiting_for_response):
                                cursor_x = text_x + line_width + 2
                                cursor_y = text_y
                                cursor_height = line_height - 2
                                cursor_color = (200, 220, 255)
                                pygame.draw.line(self.ui.screen, cursor_color, 
                                            (cursor_x, cursor_y), 
                                            (cursor_x, cursor_y + cursor_height), 2)
                                
            finally:
                self.ui.screen.set_clip(original_clip)
        
        # Enhanced bottom UI elements
        self._draw_enhanced_input_status(box_x, box_y, box_width, box_height, chat_manager)

    def _draw_input_corner_patterns(self, box_x, box_y, box_width, box_height):
        """Draw decorative patterns in input box corners"""
        pattern_color = (80, 120, 180, 100)
        corner_size = 20
        
        # Create pattern surface
        pattern_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        
        # Top-left corner pattern
        for i in range(3):
            pygame.draw.arc(pattern_surf, pattern_color,
                        (5 + i*3, 5 + i*3, corner_size - i*6, corner_size - i*6),
                        0, math.pi/2, 1)
        
        # Top-right corner pattern
        for i in range(3):
            pygame.draw.arc(pattern_surf, pattern_color,
                        (box_width - corner_size - 5 + i*3, 5 + i*3, corner_size - i*6, corner_size - i*6),
                        math.pi/2, math.pi, 1)
        
        # Bottom corners - small dots
        for i in range(5):
            dot_x = 10 + i * 8
            dot_y = box_height - 10
            pygame.draw.circle(pattern_surf, pattern_color, (dot_x, dot_y), 2)
            
            dot_x = box_width - 50 + i * 8
            pygame.draw.circle(pattern_surf, pattern_color, (dot_x, dot_y), 2)
        
        self.ui.screen.blit(pattern_surf, (box_x, box_y))

    def _draw_enhanced_input_status(self, box_x, box_y, box_width, box_height, chat_manager):
        """Draw enhanced status indicators with gradients and effects"""
        bottom_right_x = box_x + box_width - 15
        bottom_right_y = box_y + box_height - 30
        
        if hasattr(chat_manager, 'waiting_for_response') and chat_manager.waiting_for_response:
            # Enhanced thinking indicator
            thinking_dots = self._get_thinking_dots()
            thinking_text = f"AI is thinking{thinking_dots}"
            
            # Create gradient text effect
            base_color = (120, 180, 255)
            glow_color = (60, 120, 200)
            
            # Draw glow first
            glow_surf = self.ui.font_chat.render(thinking_text, True, glow_color)
            glow_x = bottom_right_x - glow_surf.get_width() - 30
            self.ui.screen.blit(glow_surf, (glow_x + 1, bottom_right_y - 6))
            
            # Draw main text
            thinking_surf = self.ui.font_chat.render(thinking_text, True, base_color)
            thinking_x = bottom_right_x - thinking_surf.get_width() - 30
            self.ui.screen.blit(thinking_surf, (thinking_x, bottom_right_y - 7))
            
            # Add pulsing loading icon
            pulse_size = 4 + int(2 * math.sin(self.loading_rotation * 0.1))
            pygame.draw.circle(self.ui.screen, base_color, 
                            (thinking_x - 15, bottom_right_y - 2), pulse_size)
            
        else:
            # Enhanced send prompt with icon
            send_text = "Press ENTER to send"
            
            # Gradient background for prompt
            prompt_surf = self.ui.font_chat.render(send_text, True, (180, 220, 255))
            prompt_width = prompt_surf.get_width() + 30
            prompt_height = 20
            prompt_x = bottom_right_x - prompt_width
            prompt_y = bottom_right_y - 15
            
            # Draw prompt background with gradient
            prompt_bg = pygame.Surface((prompt_width, prompt_height), pygame.SRCALPHA)
            for y in range(prompt_height):
                alpha = int(40 * (1 - y / prompt_height))
                color = (50, 100, 150, alpha)
                pygame.draw.line(prompt_bg, color, (0, y), (prompt_width, y))
            
            self.ui.screen.blit(prompt_bg, (prompt_x, prompt_y))
            
            # Draw prompt text
            text_x = prompt_x + 5
            self.ui.screen.blit(prompt_surf, (text_x, bottom_right_y - 7))
            
            # Enhanced send arrow with glow
            arrow_x = bottom_right_x - 20
            arrow_y = bottom_right_y - 6
            self._draw_enhanced_send_arrow(arrow_x, arrow_y)

    def _draw_enhanced_send_arrow(self, x: int, y: int, size: int = 12):
        """Draw enhanced send arrow with glow effect"""
        # Arrow glow
        glow_points = [
            (x - 1, y + size // 2),
            (x + size - 3, y + 1),
            (x + size - 3, y + size // 2 - 3),
            (x + size + 1, y + size // 2),
            (x + size - 3, y + size // 2 + 3),
            (x + size - 3, y + size - 1),
        ]
        pygame.draw.polygon(self.ui.screen, (100, 150, 200), glow_points)
        
        # Main arrow
        points = [
            (x, y + size // 2),
            (x + size - 4, y + 2),
            (x + size - 4, y + size // 2 - 2),
            (x + size, y + size // 2),
            (x + size - 4, y + size // 2 + 2),
            (x + size - 4, y + size - 2),
        ]
        pygame.draw.polygon(self.ui.screen, (180, 220, 255), points)

    def _get_thinking_dots(self) -> str:
        """Get animated thinking dots based on current animation state"""
        if self.thinking_dots == 0:
            return ""
        elif self.thinking_dots == 1:
            return "."
        elif self.thinking_dots == 2:
            return ".."
        else:  # self.thinking_dots == 3
            return "..."
    
    def _draw_enhanced_scrollbar(self, bar_x: int, bar_y: int, visible_height: int,
                            total_height: int, view_height: int, scroll_offset: int, is_locked: bool = False):
        """Draw enhanced scrollbar that adapts to conversation length like a normal chat"""
        bar_width = 10
        corner_radius = 5
        
        # Create rounded track background (always show)
        track_surf = pygame.Surface((bar_width, visible_height), pygame.SRCALPHA)
        self._draw_rounded_rect_gradient(track_surf, pygame.Rect(0, 0, bar_width, visible_height), 
                                       corner_radius, is_locked, is_track=True)
        self.ui.screen.blit(track_surf, (bar_x, bar_y))
        
        # Calculate thumb properties based on conversation length
        if total_height <= view_height:
            # No content or content fits entirely - thumb fills entire track
            thumb_height = visible_height - 4  # Small margin from track edges
            thumb_y = bar_y + 2
            scroll_ratio = 0  # No scroll position needed
        else:
            # Content is larger than view - calculate proportional thumb
            # Thumb height represents the visible portion of total content
            thumb_height_ratio = view_height / total_height
            thumb_height = max(20, int(visible_height * thumb_height_ratio))  # Minimum 20px
            
            # Calculate thumb position based on scroll
            max_scroll = total_height - view_height
            scroll_ratio = scroll_offset / max_scroll if max_scroll > 0 else 0
            scroll_ratio = max(0, min(1, scroll_ratio))  # Clamp to 0-1
            
            # Position thumb within track
            max_thumb_travel = visible_height - thumb_height
            thumb_y = bar_y + int(max_thumb_travel * scroll_ratio)
        
        # Ensure thumb stays within track bounds
        thumb_y = max(bar_y, min(thumb_y, bar_y + visible_height - thumb_height))
        
        # Create rounded thumb with gradient
        thumb_surf = pygame.Surface((bar_width - 2, thumb_height), pygame.SRCALPHA)
        thumb_rect = pygame.Rect(0, 0, bar_width - 2, thumb_height)
        self._draw_rounded_rect_gradient(thumb_surf, thumb_rect, corner_radius - 1, is_locked, is_track=False)
        self.ui.screen.blit(thumb_surf, (bar_x + 1, thumb_y))
        
        # Enhanced thumb border with rounded corners
        thumb_border_color = (200, 150, 220) if not is_locked else (120, 100, 140)
        self._draw_rounded_rect_border(self.ui.screen, 
                                     pygame.Rect(bar_x + 1, thumb_y, bar_width - 2, thumb_height),
                                     thumb_border_color, corner_radius - 1, 1)
        
        # Add grip lines on thumb (if thumb is tall enough)
        if thumb_height > 30:  # Only show grip lines on taller thumbs
            self._draw_thumb_grip_lines(bar_x + 1, thumb_y, bar_width - 2, thumb_height, thumb_border_color)
    
    def _draw_rounded_rect_gradient(self, surface, rect, radius, is_locked, is_track=True):
        """Draw a rounded rectangle with gradient fill"""
        if is_track:
            # Track colors
            if is_locked:
                start_color = (40, 30, 45)
                end_color = (50, 40, 55)
            else:
                start_color = (60, 40, 70)
                end_color = (80, 60, 95)
        else:
            # Thumb colors
            if is_locked:
                start_color = (100, 80, 120)
                end_color = (150, 120, 180)
            else:
                start_color = (150, 100, 180)
                end_color = (200, 150, 230)
        
        # Create gradient
        for y in range(rect.height):
            progress = y / rect.height if rect.height > 0 else 0
            r = int(start_color[0] + (end_color[0] - start_color[0]) * progress)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * progress)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * progress)
            color = (r, g, b)
            pygame.draw.line(surface, color, (0, y), (rect.width, y))
        
        # Apply rounded corner mask
        self._apply_scrollbar_rounded_mask(surface, radius)
    
    def _draw_rounded_rect_border(self, surface, rect, color, radius, width):
        """Draw a rounded rectangle border"""
        # Create a temporary surface for the border
        border_surf = pygame.Surface((rect.width + width * 2, rect.height + width * 2), pygame.SRCALPHA)
        
        # Draw outer rounded rect
        self._draw_solid_rounded_rect(border_surf, color, 
                                    pygame.Rect(0, 0, border_surf.get_width(), border_surf.get_height()), 
                                    radius + width)
        
        # Draw inner rounded rect (transparent) to create border effect
        if rect.width > width * 2 and rect.height > width * 2:
            inner_rect = pygame.Rect(width, width, rect.width, rect.height)
            self._draw_solid_rounded_rect(border_surf, (0, 0, 0, 0), inner_rect, radius, blend_mode=pygame.BLEND_ALPHA_SDL2)
        
        surface.blit(border_surf, (rect.x - width, rect.y - width))
    
    def _draw_solid_rounded_rect(self, surface, color, rect, radius, blend_mode=None):
        """Draw a solid color rounded rectangle"""
        temp_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        temp_surf.fill(color)
        self._apply_scrollbar_rounded_mask(temp_surf, radius)
        
        if blend_mode:
            surface.blit(temp_surf, (rect.x, rect.y), special_flags=blend_mode)
        else:
            surface.blit(temp_surf, (rect.x, rect.y))
    
    def _apply_scrollbar_rounded_mask(self, surface, radius):
        """Apply rounded corner mask specifically for scrollbar elements"""
        width, height = surface.get_size()
        
        if radius <= 0 or width <= 0 or height <= 0:
            return
        
        # Limit radius to prevent issues
        radius = min(radius, width // 2, height // 2)
        
        # Create mask for each corner
        for x in range(width):
            for y in range(height):
                # Check if pixel is in a corner region
                in_corner = False
                corner_center_x, corner_center_y = 0, 0
                
                if x < radius and y < radius:
                    # Top-left corner
                    corner_center_x, corner_center_y = radius, radius
                    in_corner = True
                elif x >= width - radius and y < radius:
                    # Top-right corner
                    corner_center_x, corner_center_y = width - radius, radius
                    in_corner = True
                elif x < radius and y >= height - radius:
                    # Bottom-left corner
                    corner_center_x, corner_center_y = radius, height - radius
                    in_corner = True
                elif x >= width - radius and y >= height - radius:
                    # Bottom-right corner
                    corner_center_x, corner_center_y = width - radius, height - radius
                    in_corner = True
                
                if in_corner:
                    # Calculate distance from corner center
                    distance = math.sqrt((x - corner_center_x)**2 + (y - corner_center_y)**2)
                    if distance > radius:
                        # Outside radius, make transparent
                        surface.set_at((x, y), (0, 0, 0, 0))
    
    def _draw_thumb_grip_lines(self, thumb_x, thumb_y, thumb_width, thumb_height, color):
        """Draw grip lines on the scrollbar thumb"""
        center_y = thumb_y + thumb_height // 2
        line_spacing = 3
        line_width = thumb_width - 4
        line_start_x = thumb_x + 2
        
        # Draw 3 horizontal grip lines
        for i in range(-1, 2):
            line_y = center_y + i * line_spacing
            if line_y >= thumb_y + 3 and line_y <= thumb_y + thumb_height - 3:
                pygame.draw.line(self.ui.screen, color, 
                               (line_start_x, line_y), 
                               (line_start_x + line_width, line_y), 1)
    
    def handle_scroll_wheel(self, chat_manager, scroll_direction: int):
        """Handle mouse wheel scrolling with proper bounds checking"""
        scroll_speed = 50
        
        # Initialize scroll offset if it doesn't exist
        if not hasattr(chat_manager, 'scroll_offset') or chat_manager.scroll_offset is None:
            chat_manager.scroll_offset = 0
            chat_manager.target_scroll_offset = 0
            self.target_scroll_offset = 0
        
        # Get content bounds
        max_scroll = 0
        if hasattr(chat_manager, 'content_height') and hasattr(chat_manager, 'view_height'):
            max_scroll = max(0, chat_manager.content_height - chat_manager.view_height)
        
        # Get current target scroll position
        current_target = getattr(chat_manager, 'target_scroll_offset', chat_manager.scroll_offset)
        
        # Calculate new target position
        if scroll_direction > 0:  # Scroll up
            new_target = current_target - scroll_speed
            self.auto_scroll_enabled = False  # Disable auto-scroll when user scrolls up
        elif scroll_direction < 0:  # Scroll down
            new_target = current_target + scroll_speed
        else:
            return

        # Clamp to valid bounds
        new_target = max(0, min(new_target, max_scroll))
        
        # Update targets
        chat_manager.target_scroll_offset = new_target
        self.target_scroll_offset = new_target
        
        # Check if we're near the bottom to re-enable auto-scroll
        if new_target >= max_scroll - 10:  # Within 10 pixels of bottom
            self.auto_scroll_enabled = True

    def enable_auto_scroll(self):
        """Re-enable auto-scroll (call when user scrolls to bottom)"""
        self.auto_scroll_enabled = True