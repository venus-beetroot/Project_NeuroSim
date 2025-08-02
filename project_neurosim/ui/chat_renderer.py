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
    from project_neurosim.entities.npc import NPC

class ChatRenderer:
    """Handles chat box rendering with subtle lock feedback - FIXED to remove lock visuals"""
    
    def __init__(self, ui_manager: 'UIManager'):
        self.ui = ui_manager
        self.loading_rotation = 0  # For spinning loading icon
        self.thinking_animation_timer = 0  # For thinking dots animation
        self.thinking_dots = 0  # Number of dots to show (0-3)
        
        # Lock animation variables (kept for potential future use)
        self.lock_pulse_timer = 0
        self.lock_alpha = 0
    
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
        """Draw the chat history box with scrolling - FIXED with clipping protection"""
        # Box dimensions
        box_width, box_height = app.WIDTH - 350, 450
        box_x, box_y = 175, app.HEIGHT - box_height - 170
        
        # Determine background color based on lock status - ONLY darken background
        if chat_manager.is_chat_locked():
            bg_color = (20, 20, 20)  # Darker when locked
            border_color = (150, 150, 150)  # Dimmer border when locked
        else:
            bg_color = (30, 30, 30)  # Normal background
            border_color = (255, 255, 255)  # Normal border
        
        # Draw box background
        pygame.draw.rect(self.ui.screen, bg_color, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.ui.screen, border_color, (box_x, box_y, box_width, box_height), 2)
        
        # Text area setup with margins for sprites and scrollbar
        text_margin_left, text_margin_right = 60, 20
        bubble_width = box_width - text_margin_left - text_margin_right
        
        # Build wrapped lines from chat history
        all_lines = self._build_chat_lines(current_npc.chat_history, bubble_width)
        
        # Add live message lines to the total if typing
        total_lines_including_live = len(all_lines)
        live_lines = []
        if chat_manager.live_message:
            live_lines = self.ui.wrap_text(chat_manager.live_message, self.ui.font_chat, bubble_width)
            total_lines_including_live += len(live_lines)
        
        # Calculate visible area
        top_padding, bottom_padding = 10, 10
        available_height = box_height - top_padding - bottom_padding
        line_height = self.ui.font_chat.get_height() + 5
        visible_lines = available_height // line_height
        
        # Update scroll offset based on total lines including live message
        chat_manager.handle_scroll(0, total_lines_including_live, visible_lines)
        
        # Set up clipping rectangle for text area to prevent overflow
        text_area_x = box_x + 2  # Inside border
        text_area_y = box_y + 2  # Inside border
        text_area_width = box_width - 4  # Account for borders
        text_area_height = box_height - 4  # Account for borders
        
        clip_rect = pygame.Rect(text_area_x, text_area_y, text_area_width, text_area_height)
        original_clip = self.ui.screen.get_clip()
        self.ui.screen.set_clip(clip_rect)
        
        try:
            # Draw visible lines from history
            lines_drawn = self._draw_visible_lines(all_lines, chat_manager.scroll_offset, visible_lines,
                                                 box_x, box_y + top_padding, text_margin_left, bubble_width,
                                                 line_height, current_npc, chat_manager.is_chat_locked())
            
            # Draw live typing message in the remaining visible space
            if chat_manager.live_message and lines_drawn < visible_lines:
                remaining_lines = visible_lines - lines_drawn
                self._draw_live_message(live_lines, chat_manager.scroll_offset - len(all_lines),
                                      remaining_lines, box_x, box_y + top_padding,
                                      text_margin_left, bubble_width, line_height,
                                      lines_drawn, current_npc, chat_manager.is_chat_locked())
        finally:
            # Always restore original clipping
            self.ui.screen.set_clip(original_clip)
        
        # Draw scrollbar (outside clipping area)
        if total_lines_including_live > visible_lines:
            self._draw_scrollbar(box_x + box_width - 10, box_y + top_padding,
                               available_height, total_lines_including_live, visible_lines,
                               chat_manager.scroll_offset, chat_manager.is_chat_locked())
    
    def _build_chat_lines(self, chat_history: List, bubble_width: int) -> List[Tuple]:
        """Build a flat list of wrapped lines from chat history with robust wrapping"""
        all_lines = []
        for entry in chat_history:
            speaker, message = entry if isinstance(entry, tuple) else ("npc", entry)
            # Use robust wrapping to prevent overflow
            wrapped = self._robust_wrap_text(message, self.ui.font_chat, bubble_width)
            for idx, line in enumerate(wrapped):
                all_lines.append((speaker, line, idx == 0))
        return all_lines
    
    def _draw_visible_lines(self, all_lines: List, scroll_offset: int, visible_lines: int,
                          box_x: int, start_y: int, text_margin_left: int, bubble_width: int,
                          line_height: int, current_npc: 'NPC', is_locked: bool = False) -> int:
        """Draw the visible portion of chat lines with clipping protection"""
        y_offset = start_y
        lines_to_draw = min(len(all_lines) - scroll_offset, visible_lines)
        
        if lines_to_draw <= 0:
            return 0
            
        visible_slice = all_lines[scroll_offset:scroll_offset + lines_to_draw]
        
        for speaker, line_text, is_first in visible_slice:
            # Skip empty lines
            if not line_text.strip():
                y_offset += line_height
                continue
                
            # Dim text colors when locked
            if is_locked:
                text_color = (70, 105, 180) if speaker == "player" else (180, 180, 70)  # Dimmed colors
            else:
                text_color = (100, 150, 255) if speaker == "player" else (255, 255, 0)  # Normal colors
            
            # Ensure text fits within bubble width
            bubble_x = box_x + text_margin_left
            
            # Truncate text if it's somehow still too wide
            display_text = line_text
            text_width = self.ui.font_chat.size(display_text)[0]
            if text_width > bubble_width:
                # Emergency truncation with ellipsis
                while len(display_text) > 3 and self.ui.font_chat.size(display_text + "...")[0] > bubble_width:
                    display_text = display_text[:-1]
                display_text += "..."
                text_width = self.ui.font_chat.size(display_text)[0]
            
            # Center text in bubble
            text_x = bubble_x + (bubble_width - text_width) // 2
            
            # Ensure text doesn't go outside bubble area
            text_x = max(bubble_x, min(text_x, bubble_x + bubble_width - text_width))
            
            line_surf = self.ui.font_chat.render(display_text, True, text_color)
            self.ui.screen.blit(line_surf, (text_x, y_offset))
            
            # Draw sprite for first line of each message
            if is_first:
                self._draw_message_sprite(speaker, box_x, y_offset, current_npc, is_locked)
            
            y_offset += line_height
        
        return lines_to_draw
    
    def _draw_message_sprite(self, speaker: str, box_x: int, y_offset: int, current_npc: 'NPC', is_locked: bool = False):
        """Draw character sprite next to message"""
        if speaker == "player" and hasattr(self, 'player') and self.player:
            # Draw player sprite on the right side
            sprite_box = pygame.Rect(box_x + app.WIDTH - 350 - 60, y_offset, 40, 50)
            player_sprite = pygame.transform.flip(pygame.transform.scale(self.player.image, (40, 50)), True, False)
            
            # Dim sprite when locked
            if is_locked:
                # Create a dimmed version of the sprite
                dimmed_sprite = player_sprite.copy()
                dim_overlay = pygame.Surface((40, 50), pygame.SRCALPHA)
                dim_overlay.fill((0, 0, 0, 100))
                dimmed_sprite.blit(dim_overlay, (0, 0))
                self.ui.screen.blit(dimmed_sprite, sprite_box.topleft)
            else:
                self.ui.screen.blit(player_sprite, sprite_box.topleft)
                
        elif speaker == "npc":
            # Draw NPC sprite on the left side
            sprite_box = pygame.Rect(box_x + 10, y_offset, 40, 50)
            npc_sprite = pygame.transform.scale(current_npc.image, (40, 50))
            
            # Dim sprite when locked
            if is_locked:
                # Create a dimmed version of the sprite
                dimmed_sprite = npc_sprite.copy()
                dim_overlay = pygame.Surface((40, 50), pygame.SRCALPHA)
                dim_overlay.fill((0, 0, 0, 100))
                dimmed_sprite.blit(dim_overlay, (0, 0))
                self.ui.screen.blit(dimmed_sprite, sprite_box.topleft)
            else:
                self.ui.screen.blit(npc_sprite, sprite_box.topleft)
    
    def _draw_live_message(self, live_lines: List[str], live_scroll_offset: int,
                         remaining_visible_lines: int, box_x: int, box_y: int,
                         text_margin_left: int, bubble_width: int, line_height: int,
                         y_start_offset: int, current_npc: 'NPC', is_locked: bool = False):
        """Draw the currently typing message with clipping protection"""
        if not live_lines:
            return
            
        bubble_x = box_x + text_margin_left
        
        # Calculate starting position right after the last history line
        y_offset = box_y + (y_start_offset * line_height)
        
        # Determine which live lines to show based on scroll and available space
        start_line = max(0, live_scroll_offset)
        end_line = min(len(live_lines), start_line + remaining_visible_lines)
        
        for i in range(start_line, end_line):
            line = live_lines[i]
            if not line.strip():
                y_offset += line_height
                continue
                
            # Ensure text fits within bubble width (emergency protection)
            display_text = line
            text_width = self.ui.font_chat.size(display_text)[0]
            if text_width > bubble_width:
                # Emergency truncation with ellipsis
                while len(display_text) > 3 and self.ui.font_chat.size(display_text + "...")[0] > bubble_width:
                    display_text = display_text[:-1]
                display_text += "..."
                text_width = self.ui.font_chat.size(display_text)[0]
            
            # Center text in bubble
            text_x = bubble_x + (bubble_width - text_width) // 2
            
            # Ensure text doesn't go outside bubble area
            text_x = max(bubble_x, min(text_x, bubble_x + bubble_width - text_width))
            
            # Use normal NPC color for live message (it's always from NPC)
            text_color = (180, 180, 70) if is_locked else (255, 255, 0)
            line_surf = self.ui.font_chat.render(display_text, True, text_color)
            self.ui.screen.blit(line_surf, (text_x, y_offset))
            
            # Draw NPC sprite for the first line of live message
            if i == start_line:
                self._draw_message_sprite("npc", box_x, y_offset, current_npc, is_locked)
            
            y_offset += line_height
    
    def _draw_scrollbar(self, bar_x: int, bar_y: int, bar_height: int,
                       total_lines: int, visible_lines: int, scroll_offset: int, is_locked: bool = False):
        """Draw the chat scrollbar"""
        bar_width = 8
        
        # Dim colors when locked
        if is_locked:
            track_color = (60, 60, 60)
            thumb_color = (120, 120, 120)
        else:
            track_color = (100, 100, 100)
            thumb_color = (200, 200, 200)
        
        # Background track
        pygame.draw.rect(self.ui.screen, track_color, (bar_x, bar_y, bar_width, bar_height))
        
        # Thumb
        thumb_height = max(20, bar_height * visible_lines // total_lines)
        max_scroll = max(1, total_lines - visible_lines)
        thumb_y = bar_y + (bar_height - thumb_height) * scroll_offset // max_scroll
        pygame.draw.rect(self.ui.screen, thumb_color, (bar_x, thumb_y, bar_width, thumb_height))

    def _draw_loading_spinner(self, x: int, y: int, size: int = 16):
        """Draw a spinning loading icon"""
        center_x, center_y = x + size // 2, y + size // 2
        
        # Draw spinning circle segments
        for i in range(8):
            angle = math.radians(self.loading_rotation + i * 45)
            start_x = center_x + math.cos(angle) * (size // 3)
            start_y = center_y + math.sin(angle) * (size // 3)
            end_x = center_x + math.cos(angle) * (size // 2)
            end_y = center_y + math.sin(angle) * (size // 2)
            
            # Fade effect - newer segments are brighter
            alpha = max(50, 255 - i * 25)
            color = (alpha, alpha, alpha)
            
            pygame.draw.line(self.ui.screen, color, (start_x, start_y), (end_x, end_y), 2)
    
    def _draw_send_arrow(self, x: int, y: int, size: int = 12):
        """Draw a simple send arrow icon"""
        # Arrow pointing right
        points = [
            (x, y + size // 2),           # Left point
            (x + size - 4, y + 2),        # Top right
            (x + size - 4, y + size // 2 - 2),  # Middle right top
            (x + size, y + size // 2),    # Right point
            (x + size - 4, y + size // 2 + 2),  # Middle right bottom
            (x + size - 4, y + size - 2), # Bottom right
        ]
        pygame.draw.polygon(self.ui.screen, (150, 150, 150), points)
    
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
        """Draw the message input box with send prompt and loading state - FIXED with robust clipping"""
        box_width, box_height = app.WIDTH - 350, 100
        box_x, box_y = 175, app.HEIGHT - box_height - 50
        
        pygame.draw.rect(self.ui.screen, (50, 50, 50), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.ui.screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)
        
        # Draw typed message with strict clipping
        if message:
            # Create a clipping rectangle to prevent overflow
            text_margin_left = 10
            text_margin_right = 140  # Space for "Press ENTER" text
            text_margin_top = 5
            text_margin_bottom = 30  # Space for UI elements at bottom
            
            text_area_x = box_x + text_margin_left
            text_area_y = box_y + text_margin_top
            text_area_width = box_width - text_margin_left - text_margin_right
            text_area_height = box_height - text_margin_top - text_margin_bottom
            
            # Set clipping rectangle
            clip_rect = pygame.Rect(text_area_x, text_area_y, text_area_width, text_area_height)
            original_clip = self.ui.screen.get_clip()
            self.ui.screen.set_clip(clip_rect)
            
            try:
                # Try different font sizes
                fonts_to_try = [self.ui.font_small]
                
                # Create smaller fonts if they don't exist
                if hasattr(self.ui.font_small, 'get_height'):
                    base_size = self.ui.font_small.get_height()
                    try:
                        small_font = pygame.font.Font(None, max(12, base_size - 2))
                        tiny_font = pygame.font.Font(None, max(10, base_size - 4))
                        fonts_to_try.extend([small_font, tiny_font])
                    except:
                        pass
                
                best_font = fonts_to_try[0]
                wrapped_lines = []
                
                # Find font that fits
                for font in fonts_to_try:
                    wrapped_lines = self._robust_wrap_text(message, font, text_area_width)
                    line_height = font.get_height() + 1
                    total_height = len(wrapped_lines) * line_height
                    
                    if total_height <= text_area_height:
                        best_font = font
                        break
                
                # If still doesn't fit, truncate lines
                line_height = best_font.get_height() + 1
                max_lines = max(1, text_area_height // line_height)
                if len(wrapped_lines) > max_lines:
                    wrapped_lines = wrapped_lines[:max_lines]
                    # Add ellipsis to last line if truncated
                    if wrapped_lines:
                        last_line = wrapped_lines[-1]
                        ellipsis = "..."
                        # Make sure ellipsis fits
                        while best_font.size(last_line + ellipsis)[0] > text_area_width and len(last_line) > 0:
                            last_line = last_line[:-1]
                        wrapped_lines[-1] = last_line + ellipsis
                
                # Draw the text
                start_y = text_area_y + (text_area_height - len(wrapped_lines) * line_height) // 2
                
                for i, line in enumerate(wrapped_lines):
                    if not line.strip():
                        continue
                        
                    line_surf = best_font.render(line, True, (100, 150, 255))
                    
                    # Center horizontally within text area
                    line_width = line_surf.get_width()
                    text_x = text_area_x + (text_area_width - line_width) // 2
                    text_y = start_y + (i * line_height)
                    
                    # Only draw if within bounds
                    if (text_y >= text_area_y and 
                        text_y + line_height <= text_area_y + text_area_height):
                        self.ui.screen.blit(line_surf, (text_x, text_y))
                        
            finally:
                # Always restore original clipping
                self.ui.screen.set_clip(original_clip)
        
        # Draw bottom right UI elements
        bottom_right_x = box_x + box_width - 10
        bottom_right_y = box_y + box_height - 25
        
        # Check if we're waiting for AI response
        if hasattr(chat_manager, 'waiting_for_response') and chat_manager.waiting_for_response:
            # Show animated thinking text with dots
            thinking_dots = self._get_thinking_dots()
            thinking_text = f"Thinking{thinking_dots}"
            thinking_surf = self.ui.font_chat.render(thinking_text, True, (150, 150, 150))
            thinking_x = bottom_right_x - thinking_surf.get_width() - 5
            self.ui.screen.blit(thinking_surf, (thinking_x, bottom_right_y - 7))
        else:
            # Show send prompt
            send_text = "Press ENTER to send"
            send_surf = self.ui.font_chat.render(send_text, True, (150, 150, 150))
            send_x = bottom_right_x - send_surf.get_width() - 20
            self.ui.screen.blit(send_surf, (send_x, bottom_right_y - 7))
            
            # Draw send arrow
            arrow_x = bottom_right_x - 15
            arrow_y = bottom_right_y - 6
            self._draw_send_arrow(arrow_x, arrow_y)