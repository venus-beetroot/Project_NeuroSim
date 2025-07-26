"""
Chat interface rendering
"""
import pygame
from typing import List, Tuple, TYPE_CHECKING
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.assets import app

if TYPE_CHECKING:
    from managers.ui_manager import UIManager
    from managers.chat_manager import ChatManager
    from functions.core.npc import NPC

class ChatRenderer:
    """Handles chat box rendering"""
    
    def __init__(self, ui_manager: 'UIManager'):
        self.ui = ui_manager
    
    def draw_chat_interface(self, current_npc: 'NPC', chat_manager: 'ChatManager', player=None):
        """Draw the complete chat interface"""
        self.player = player  # Store player reference for sprite drawing
        self._draw_overlay()
        self._draw_header(current_npc.name)
        self._draw_chat_history(current_npc, chat_manager)
        self._draw_input_box(chat_manager.message)
    
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
        
        # Draw visible lines from history
        lines_drawn = self._draw_visible_lines(all_lines, chat_manager.scroll_offset, visible_lines,
                                             box_x, box_y + top_padding, text_margin_left, bubble_width,
                                             line_height, current_npc)
        
        # Draw live typing message in the remaining visible space
        if chat_manager.live_message and lines_drawn < visible_lines:
            remaining_lines = visible_lines - lines_drawn
            self._draw_live_message(live_lines, chat_manager.scroll_offset - len(all_lines),
                                  remaining_lines, box_x, box_y + top_padding,
                                  text_margin_left, bubble_width, line_height,
                                  lines_drawn, current_npc)
        
        # Draw scrollbar
        if total_lines_including_live > visible_lines:
            self._draw_scrollbar(box_x + box_width - 10, box_y + top_padding,
                               available_height, total_lines_including_live, visible_lines,
                               chat_manager.scroll_offset)
    
    def _build_chat_lines(self, chat_history: List, bubble_width: int) -> List[Tuple]:
        """Build a flat list of wrapped lines from chat history"""
        all_lines = []
        for entry in chat_history:
            speaker, message = entry if isinstance(entry, tuple) else ("npc", entry)
            wrapped = self.ui.wrap_text(message, self.ui.font_chat, bubble_width)
            for idx, line in enumerate(wrapped):
                all_lines.append((speaker, line, idx == 0))
        return all_lines
    
    def _draw_visible_lines(self, all_lines: List, scroll_offset: int, visible_lines: int,
                          box_x: int, start_y: int, text_margin_left: int, bubble_width: int,
                          line_height: int, current_npc: 'NPC') -> int:
        """Draw the visible portion of chat lines and return number of lines drawn"""
        y_offset = start_y
        lines_to_draw = min(len(all_lines) - scroll_offset, visible_lines)
        
        if lines_to_draw <= 0:
            return 0
            
        visible_slice = all_lines[scroll_offset:scroll_offset + lines_to_draw]
        
        for speaker, line_text, is_first in visible_slice:
            text_color = (100, 150, 255) if speaker == "player" else (255, 255, 0)  # Lighter blue for player
            
            # Center text in bubble
            bubble_x = box_x + text_margin_left
            text_x = bubble_x + (bubble_width - self.ui.font_chat.size(line_text)[0]) // 2
            line_surf = self.ui.font_chat.render(line_text, True, text_color)
            self.ui.screen.blit(line_surf, (text_x, y_offset))
            
            # Draw sprite for first line of each message
            if is_first and line_text.strip():
                self._draw_message_sprite(speaker, box_x, y_offset, current_npc)
            
            y_offset += line_height
        
        return lines_to_draw
    
    def _draw_message_sprite(self, speaker: str, box_x: int, y_offset: int, current_npc: 'NPC'):
        """Draw character sprite next to message"""
        if speaker == "player" and hasattr(self, 'player') and self.player:
            # Draw player sprite on the right side
            sprite_box = pygame.Rect(box_x + app.WIDTH - 350 - 60, y_offset, 40, 50)
            player_sprite = pygame.transform.flip(pygame.transform.scale(self.player.image, (40, 50)), True, False)
            self.ui.screen.blit(player_sprite, sprite_box.topleft)
        elif speaker == "npc":
            # Draw NPC sprite on the left side
            sprite_box = pygame.Rect(box_x + 10, y_offset, 40, 50)
            npc_sprite = pygame.transform.scale(current_npc.image, (40, 50))
            self.ui.screen.blit(npc_sprite, sprite_box.topleft)
    
    def _draw_live_message(self, live_lines: List[str], live_scroll_offset: int,
                         remaining_visible_lines: int, box_x: int, box_y: int,
                         text_margin_left: int, bubble_width: int, line_height: int,
                         y_start_offset: int, current_npc: 'NPC'):
        """Draw the currently typing message within the chat box bounds"""
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
            text_x = bubble_x + (bubble_width - self.ui.font_chat.size(line)[0]) // 2
            line_surf = self.ui.font_chat.render(line, True, (255, 255, 0))
            self.ui.screen.blit(line_surf, (text_x, y_offset))
            
            # Draw NPC sprite for the first line of live message
            if i == start_line and line.strip():
                self._draw_message_sprite("npc", box_x, y_offset, current_npc)
            
            y_offset += line_height
    
    def _draw_scrollbar(self, bar_x: int, bar_y: int, bar_height: int,
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
    
    def _draw_input_box(self, message: str):
        """Draw the message input box"""
        box_width, box_height = app.WIDTH - 350, 100
        box_x, box_y = 175, app.HEIGHT - box_height - 50
        
        pygame.draw.rect(self.ui.screen, (50, 50, 50), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.ui.screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)
        
        if message:
            bubble_x = box_x + 60
            bubble_width = box_width - 120
            msg_surf = self.ui.font_small.render(message, True, (100, 150, 255))
            text_x = bubble_x + (bubble_width - msg_surf.get_width()) // 2
            text_y = box_y + (box_height - msg_surf.get_height()) // 2
            self.ui.screen.blit(msg_surf, (text_x, text_y))