"""
Chat system management
"""
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.npc import NPC

class ChatManager:
    """Handles all chat-related functionality"""
    
    def __init__(self, font_chat, font_small):
        self.font_chat = font_chat
        self.font_small = font_small
        self.scroll_offset = 0
        self.cooldown_duration = 3000
        self.chat_cooldown = 0
        self.message = ""
        
        # NPC typing variables
        self.typing_active = False
        self.letter_timer = None
        self.response_start_time = None
        self.current_response = ""
        self.dialogue_index = 0
        self.live_message = ""
        self.input_block_time = None
        self.waiting_for_response = False
    
    def update_cooldown(self, delta_time: int):
        """Update chat cooldown timer"""
        if self.chat_cooldown > 0:
            self.chat_cooldown -= delta_time
            if self.chat_cooldown < 0:
                self.chat_cooldown = 0
    
    def start_typing_animation(self, response_text: str):
        """Start the typing animation for NPC response"""
        self.typing_active = True
        self.response_start_time = pygame.time.get_ticks() + 1000  # Reduced delay
        self.current_response = ""
        self.dialogue_index = 0
        self.live_message = ""
        self.letter_timer = None
        print(f"Starting typing animation for: {response_text[:50]}...")
    
    def update_typing_animation(self, npc_dialogue: str) -> bool:
        """Update typing animation. Returns True if finished typing."""
        if not self.typing_active:
            return False
            
        current_time = pygame.time.get_ticks()
        
        if current_time < self.response_start_time:
            return False
            
        if self.letter_timer is None:
            self.letter_timer = current_time + 30
            
        if current_time >= self.letter_timer:
            dialogue_text = npc_dialogue.content if hasattr(npc_dialogue, "content") else str(npc_dialogue)
            
            if self.dialogue_index < len(dialogue_text):
                letter = dialogue_text[self.dialogue_index]
                self.current_response += letter
                self.dialogue_index += 1
                self.live_message = self.current_response
                
                # Calculate delay based on punctuation
                base_delay = 30
                extra_delay = 0
                if letter in [",", ";"]:
                    extra_delay = 100
                elif letter in [".", "!", "?"]:
                    extra_delay = 150
                    
                self.letter_timer = current_time + base_delay + extra_delay
            else:
                # Finished typing
                self.typing_active = False
                self.letter_timer = None
                self.response_start_time = None
                self.live_message = ""
                self.input_block_time = current_time + 500
                print("Finished typing animation")
                return True
        
        return False
    
    def can_send_message(self) -> bool:
        """Check if player can send a message"""
        current_time = pygame.time.get_ticks()
        
        # Clear expired input block
        if self.input_block_time and current_time >= self.input_block_time:
            self.input_block_time = None
            
        can_send = (self.chat_cooldown <= 0 and 
                   self.message.strip() != "" and 
                   not self.typing_active and 
                   not self.input_block_time and
                   not self.waiting_for_response)
        
        if not can_send:
            if self.chat_cooldown > 0:
                print(f"Cannot send: cooldown active ({self.chat_cooldown}ms remaining)")
            elif self.message.strip() == "":
                print("Cannot send: empty message")
            elif self.typing_active:
                print("Cannot send: typing animation active")
            elif self.input_block_time:
                print("Cannot send: input blocked")
            elif self.waiting_for_response:
                print("Cannot send: waiting for AI response")
        
        return can_send
    
    def send_message(self, current_npc: 'NPC') -> str:
        """Send message and return the message that was sent"""
        if not self.can_send_message():
            return ""
            
        sent_message = self.message.strip()
        print(f"Sending message: '{sent_message}' to {current_npc.name}")
        
        # Add to chat history
        current_npc.chat_history.append(("player", sent_message))
        
        # Set cooldown and clear message
        self.chat_cooldown = self.cooldown_duration
        self.message = ""
        
        # Mark as waiting for response
        self.waiting_for_response = True
        
        return sent_message
    
    def handle_scroll(self, direction: int, total_lines: int, visible_lines: int):
        """Handle chat scroll wheel input"""
        self.scroll_offset -= direction
        max_offset = max(0, total_lines - visible_lines)
        self.scroll_offset = max(0, min(self.scroll_offset, max_offset))
    
    def reset_state(self):
        """Reset chat manager state - useful when starting new conversation"""
        self.scroll_offset = 0
        self.chat_cooldown = 0
        self.message = ""
        self.typing_active = False
        self.letter_timer = None
        self.response_start_time = None
        self.current_response = ""
        self.dialogue_index = 0
        self.live_message = ""
        self.input_block_time = None
        self.waiting_for_response = False
        print("Chat manager state reset")