import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.npc import NPC

class ChatManager:
    """Handles all chat-related functionality with AI response locking - FIXED VERSION"""
    
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
        
        # FIXED: Improved chat locking system
        self.waiting_for_response = False  # Waiting for AI to generate response
        self.chat_locked = False  # General lock flag
        self.lock_reason = ""  # Reason for locking (for debugging)

        
        
        # New: Separate states for better control
        self._ai_processing = False  # AI is generating response
        self._npc_typing = False    # NPC is typing out response
        self._can_exit = True       # Can player exit chat
    
    def update_cooldown(self, delta_time: int):
        """Update chat cooldown timer"""
        if self.chat_cooldown > 0:
            self.chat_cooldown -= delta_time
            if self.chat_cooldown < 0:
                self.chat_cooldown = 0
    
    def lock_chat(self, reason: str = "AI processing"):
        """Lock the chat interface during AI processing"""
        self.chat_locked = True
        self.lock_reason = reason
        self._can_exit = False
        
        if "AI" in reason or "response" in reason:
            self._ai_processing = True
            self.waiting_for_response = True
        elif "typing" in reason.lower():
            self._npc_typing = True
            
        print(f"Chat locked: {reason}")
    
    def unlock_chat(self):
        """Unlock the chat interface after processing completes"""
        self.chat_locked = False
        self.lock_reason = ""
        self.waiting_for_response = False
        self._ai_processing = False
        self._npc_typing = False
        self._can_exit = True
        print("Chat unlocked")
    
    def is_chat_locked(self) -> bool:
        """Check if chat is currently locked - FIXED logic"""
        return (self.chat_locked or 
                self.waiting_for_response or 
                self.typing_active or 
                self._ai_processing or 
                self._npc_typing)
    
    def can_exit_chat(self) -> bool:
        """Check if player can exit the chat (not locked) - FIXED"""
        return self._can_exit and not self.is_chat_locked()
    
    def can_send_message(self) -> bool:
        """Check if player can send a message - FIXED"""
        if self.is_chat_locked():
            return False
            
        current_time = pygame.time.get_ticks()
        
        # Clear expired input block
        if self.input_block_time and current_time >= self.input_block_time:
            self.input_block_time = None
            
        return (self.chat_cooldown <= 0 and 
                self.message.strip() != "" and 
                not self.typing_active and 
                not self.input_block_time and
                not self._ai_processing and
                not self._npc_typing)
    
    def start_typing_animation(self, response_text: str):
        """Start the typing animation for NPC response - FIXED"""
        self.typing_active = True
        self._npc_typing = True
        self.response_start_time = pygame.time.get_ticks() + 2000
        self.current_response = ""
        self.dialogue_index = 0
        self.live_message = ""
        self.letter_timer = None
        
        # Update lock state for typing
        if not self.chat_locked:
            self.lock_chat("NPC typing")
        else:
            # Already locked, just update the reason and flags
            self.lock_reason = "NPC typing"
            self._npc_typing = True
            self._ai_processing = False  # AI is done, now typing
    
    def update_typing_animation(self, npc_dialogue: str) -> bool:
        """Update typing animation. Returns True if finished typing - FIXED"""
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
                # Finished typing - FIXED unlock logic
                self.typing_active = False
                self._npc_typing = False
                self.letter_timer = None
                self.response_start_time = None
                self.live_message = ""
                self.input_block_time = current_time + 500
                
                # Unlock chat completely when typing is finished
                self.unlock_chat()
                return True
        
        return False
    
    def send_message(self, current_npc: 'NPC') -> str:
        """Send message and return the message that was sent - FIXED"""
        if not self.can_send_message():
            return ""
            
        sent_message = self.message
        current_npc.chat_history.append(("player", sent_message))
        self.chat_cooldown = self.cooldown_duration
        self.message = ""
        
        # Lock chat immediately after sending message
        self.lock_chat("Waiting for AI response")
        
        return sent_message
    
    def handle_scroll(self, direction: int, total_lines: int, visible_lines: int):
        """Handle chat scroll wheel input - FIXED to respect lock state"""
        # Allow scrolling even when locked, but not when actively typing
        if self.typing_active:
            return  # Don't allow scrolling during typing animation
            
        self.scroll_offset -= direction
        max_offset = max(0, total_lines - visible_lines)
        self.scroll_offset = max(0, min(self.scroll_offset, max_offset))
    
    def get_lock_status_text(self) -> str:
        """Get text to display when chat is locked - IMPROVED"""
        if self._ai_processing and not self.typing_active:
            return "AI is thinking..."
        elif self.typing_active or self._npc_typing:
            return "NPC is responding..."
        elif self.chat_locked and self.lock_reason:
            return f"Chat locked: {self.lock_reason}"
        elif self.waiting_for_response:
            return "Processing response..."
        return ""
    
    # New helper methods for better state management
    def start_ai_processing(self):
        """Mark that AI processing has started"""
        self._ai_processing = True
        self.waiting_for_response = True
        self.lock_chat("AI processing response")
    
    def finish_ai_processing(self):
        """Mark that AI processing has finished (but typing may start)"""
        self._ai_processing = False
        # Don't unlock yet - typing animation will handle unlocking
    
    def force_unlock(self):
        """Force unlock chat in case of errors"""
        self.typing_active = False
        self._npc_typing = False
        self._ai_processing = False
        self.waiting_for_response = False
        self.unlock_chat()
        print("Chat force unlocked")
    
    def get_debug_state(self) -> dict:
        """Get debug information about current chat state"""
        return {
            "chat_locked": self.chat_locked,
            "waiting_for_response": self.waiting_for_response,
            "typing_active": self.typing_active,
            "_ai_processing": self._ai_processing,
            "_npc_typing": self._npc_typing,
            "_can_exit": self._can_exit,
            "lock_reason": self.lock_reason,
            "can_send": self.can_send_message(),
            "can_exit": self.can_exit_chat()
        }