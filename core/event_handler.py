import pygame
from core.states import GameState
from systems.overlay_system import OverlaySystem
from managers.chat_manager import ChatManager
from entities.npc import NPC

class EventHandler:
    """Centralized event handling system with overlay support - FIXED VERSION"""
    
    def __init__(self, game):
        self.game = game
        
        # Import overlay system if available
        try:
            from systems.overlay_system import OverlaySystem
            self.overlay_system = OverlaySystem(
                game.screen, game.font_large, game.font_small, game.font_chat
            )
            self.has_overlay_system = True
        except ImportError:
            self.has_overlay_system = False
            print("Warning: OverlaySystem not found, using fallback overlays")
        
        # State tracking
        self.showing_credits = False
        self.showing_version = False
        self.credits_close_rect = None
        self.version_close_rect = None
        

    def handle_events(self):
        """Main event handling method with smooth scroll wheel support"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.running = False
            
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self._handle_mouse_click(event.pos)
                elif event.button == 4:  # Mouse wheel up (older pygame)
                    self._handle_mouse_wheel(1)
                elif event.button == 5:  # Mouse wheel down (older pygame)
                    self._handle_mouse_wheel(-1)
            
            elif event.type == pygame.MOUSEWHEEL:
                # Handle mouse wheel (for newer pygame versions) - more responsive
                self._handle_mouse_wheel(event.y)

    def _handle_mouse_wheel(self, scroll_direction: int):
        """Handle mouse wheel scrolling for chat interface with smooth scrolling"""
        # Only handle scrolling when in chat mode
        if (self.game.game_state == GameState.INTERACTING and 
            hasattr(self.game, 'chat_renderer') and 
            hasattr(self.game, 'chat_manager') and 
            self.game.chat_manager is not None):
            
            # Use the improved smooth scrolling from chat_renderer
            self.game.chat_renderer.handle_scroll_wheel(self.game.chat_manager, scroll_direction)

    def _handle_keydown(self, event):
        """Handle keyboard events"""
        print(f"Key pressed: {event.key}, Game state: {self.game.game_state}")  # Debug print
        
        if event.key == pygame.K_ESCAPE:
            # Handle overlay escape first
            if self._handle_overlay_escape():
                print("Overlay closed with ESC")
                return
            
            # Then handle game state escapes
            if self.game.game_state == GameState.INTERACTING:
                print("Exiting interaction with ESC")
                self.game.exit_interaction()
            elif self.game.game_state == GameState.PLAYING:
                print("ESC in gameplay - going to SETTINGS")
                self.game.game_state = GameState.SETTINGS
            elif self.game.game_state == GameState.SETTINGS:
                print("Exiting settings with ESC - going to PLAYING")
                self.game.game_state = GameState.PLAYING
        
        elif self.game.game_state == GameState.INTERACTING:
            self._handle_chat_input(event)
        
        elif self.game.game_state == GameState.PLAYING:
            self._handle_playing_keys(event)

    def _handle_chat_input(self, event):
        """Handle keyboard input during NPC interaction/chat"""
        current_time = pygame.time.get_ticks()
        
        # Check if input is blocked due to typing animation or cooldown
        if (self.game.chat_manager.typing_active or 
            (self.game.chat_manager.input_block_time and 
             current_time < self.game.chat_manager.input_block_time)):
            # Only allow escape during blocked input
            if event.key != pygame.K_ESCAPE:
                return

        if event.key == pygame.K_RETURN:
            self._send_chat_message()
        elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
            # Remove last character from chat input
            self.game.chat_manager.message = self.game.chat_manager.message[:-1]
        elif event.unicode and event.unicode.isprintable():
            # Add printable characters to chat input
            self.game.chat_manager.message += event.unicode

    def _handle_playing_keys(self, event):
        """Handle keyboard input during gameplay"""
        if event.key == pygame.K_RETURN:
            # Try to interact with NPC if nearby
            self._try_interact_with_npc()
        elif event.key == pygame.K_F1:
            self.game.toggle_debug_hitboxes()
        elif event.key == pygame.K_e:
            self._handle_building_interaction()
        # Development/testing keys (can be removed in production)
        elif event.key == pygame.K_F2:
            self.game.trigger_tutorial()
        elif event.key == pygame.K_F3:
            self.game.trigger_tip("movement")
        elif event.key == pygame.K_F4:
            self.game.trigger_tip("interact_npc")
        elif event.key == pygame.K_F5:
            self.game.trigger_tip("enter_building")
        elif event.key == pygame.K_m:
            self.game.debug_map_info()
        elif event.key == pygame.K_v:
            # Quick version display
            self._show_version_overlay()
        elif event.key == pygame.K_c:
            # Quick credits display (Ctrl+C might be better)
            if pygame.key.get_pressed()[pygame.K_LCTRL]:
                self._show_credits_overlay()

    def _handle_start_screen_action(self, action):
        """Handle start screen button actions"""
        if action == "start":
            self.game.game_state = GameState.PLAYING
        elif action == "settings":
            self.game.game_state = GameState.SETTINGS
        elif action == "credits":
            self.showing_credits = True
            # Also set the game's flag for compatibility
            self.game.showing_credits = True
        elif action == "quit":
            self.game.running = False

    def _handle_mouse_click(self, pos):
        """Handle mouse click events"""
        # Handle overlay clicks first - with immediate response
        if self.showing_credits:
            self.showing_credits = False
            self.game.showing_credits = False
            print("Credits overlay closed by click")
            return
        
        if self.showing_version:
            self.showing_version = False
            self.game.showing_version = False
            print("Version overlay closed by click")
            return
        
        # Handle game state clicks
        if self.game.game_state == GameState.START_SCREEN:
            action = self.game.start_screen.handle_click(pos)
            if action:
                self._handle_start_screen_action(action)
        
        elif self.game.game_state == GameState.SETTINGS:
            self._handle_settings_click(pos)
        
        elif self.game.game_state == GameState.PLAYING:
            # Handle gameplay clicks (if needed)
            pass

    def _handle_settings_click(self, pos):
        """Handle settings menu clicks - FIXED VERSION"""
        # Define button rectangles that match the settings menu layout
        screen_width = self.game.screen.get_width()
        screen_height = self.game.screen.get_height()
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        button_width = 280
        button_height = 60
        
        # Create button rectangles that match the settings menu layout
        buttons = {
            "return_to_game": pygame.Rect(center_x - button_width//2, center_y - 80, button_width, button_height),
            "toggle_sound": pygame.Rect(center_x - button_width//2, center_y, button_width, button_height),
            "show_version": pygame.Rect(center_x - button_width//2, center_y + 80, button_width, button_height),
            "return_to_title": pygame.Rect(center_x - button_width//2, center_y + 160, button_width, button_height),
            "quit_game": pygame.Rect(center_x - button_width//2, center_y + 240, button_width, button_height)
        }
        
        # Check which button was clicked
        for action, button_rect in buttons.items():
            if button_rect.collidepoint(pos):
                print(f"Settings button clicked: {action}")  # Debug print
                
                if action == "return_to_game":
                    self.game.game_state = GameState.PLAYING
                    print("Returning to game")
                elif action == "toggle_sound":
                    self.game.toggle_sound()
                    print("Sound toggled")
                elif action == "show_version":
                    self.showing_version = True
                    self.game.showing_version = True
                    print("Showing version overlay")
                elif action == "return_to_title":
                    self.game.game_state = GameState.START_SCREEN
                    print("Returning to title screen")
                elif action == "quit_game":
                    self.game.running = False
                    print("Quitting game")
                break

    def _handle_overlay_escape(self):
        """Handle ESC key for overlays - FIXED VERSION"""
        if self.showing_credits:
            self.showing_credits = False
            self.game.showing_credits = False
            print("Credits overlay closed with ESC")
            return True
        if self.showing_version:
            self.showing_version = False
            self.game.showing_version = False
            print("Version overlay closed with ESC")
            return True
        return False
    
    def render_overlays(self):
        """Render any active overlays"""
        if self.showing_credits:
            if self.has_overlay_system:
                self.credits_close_rect = self.overlay_system.draw_credits_overlay()
            else:
                self._draw_fallback_credits()
        
        if self.showing_version:
            if self.has_overlay_system:
                self.version_close_rect = self.overlay_system.draw_version_overlay()
            else:
                self._draw_fallback_version()
    
    def render_corner_version(self):
        """Render version in corner during settings"""
        if self.has_overlay_system:
            self.overlay_system.draw_corner_version()
        else:
            # Fallback version display
            version_text = "v0.8.2 Alpha"
            version_surf = self.game.font_chat.render(version_text, True, (150, 150, 150))
            pos = (self.game.screen.get_width() - version_surf.get_width() - 10, 
                   self.game.screen.get_height() - version_surf.get_height() - 10)
            self.game.screen.blit(version_surf, pos)
    
    def _draw_fallback_credits(self):
        """Fallback credits display when overlay system isn't available"""
        overlay = pygame.Surface((self.game.screen.get_width(), self.game.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.game.screen.blit(overlay, (0, 0))
        
        # Title
        font = self.game.font_large
        text = "CREDITS"
        text_surf = font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(self.game.screen.get_width() // 2, 150))
        self.game.screen.blit(text_surf, text_rect)
        
        # Credits lines
        font_small = self.game.font_small
        credits_lines = [
            "PROJECT TEAM:",
            "",
            "Project Manager: Angus Shui",
            "Lead Programming: Haoran Fang", 
            "Lead Art: Lucas Guo",
            "",
            "TECHNOLOGY:",
            "",
            "Game Engine: Pygame",
            "AI Model: Llama3.2",
            "Graphics: Pixel Art Style",
            "",
            "SPECIAL THANKS:",
            "",
            "Pygame Community",
            "Python Software Foundation",
            "AI Club Members",
            "Beta Testers & Contributors"
        ]
        
        start_y = 250
        for i, line in enumerate(credits_lines):
            if line:  # Skip empty lines
                surf = font_small.render(line, True, (200, 200, 200))
                rect = surf.get_rect(center=(self.game.screen.get_width() // 2, start_y + i * 25))
                self.game.screen.blit(surf, rect)
        
        # Instructions
        esc_surf = font_small.render("Press ESC or click to return", True, (180, 180, 180))
        esc_rect = esc_surf.get_rect(center=(self.game.screen.get_width() // 2, self.game.screen.get_height() - 100))
        self.game.screen.blit(esc_surf, esc_rect)
    
    def _draw_fallback_version(self):
        """Fallback version display when overlay system isn't available"""
        overlay = pygame.Surface((self.game.screen.get_width(), self.game.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.game.screen.blit(overlay, (0, 0))
        
        font = self.game.font_large
        text = "VERSION INFO"
        text_surf = font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(self.game.screen.get_width() // 2, 200))
        self.game.screen.blit(text_surf, text_rect)
        
        font_small = self.game.font_small
        version_lines = [
            "PROJECT NEUROSIM",
            "v0.8.2 Alpha",
            "",
            "Build Date: May/June 2025",
            "Engine: Pygame 2.5.2",
            "Python: 3.9+",
            "",
            "KEY FEATURES:",
            "• AI-Powered NPC Conversations",
            "• Dynamic Building System", 
            "• Procedural Map Generation",
            "• Real-time Chat Interface",
            "• Interactive Tutorial System"
        ]
        
        start_y = 280
        for i, line in enumerate(version_lines):
            if line:  # Skip empty lines
                surf = font_small.render(line, True, (200, 200, 200))
                rect = surf.get_rect(center=(self.game.screen.get_width() // 2, start_y + i * 25))
                self.game.screen.blit(surf, rect)
        
        esc_surf = font_small.render("Press ESC or click to return", True, (180, 180, 180))
        esc_rect = esc_surf.get_rect(center=(self.game.screen.get_width() // 2, self.game.screen.get_height() - 100))
        self.game.screen.blit(esc_surf, esc_rect)

    # Overlay management methods
    def _show_version_overlay(self):
        """Show the version information overlay"""
        self.showing_version = True
        self.game.showing_version = True

    def _show_credits_overlay(self):
        """Show the credits overlay"""
        self.showing_credits = True
        self.game.showing_credits = True

    def _close_overlays(self):
        """Close all overlays"""
        self.showing_version = False
        self.showing_credits = False
        self.game.showing_version = False
        self.game.showing_credits = False

    # Game interaction helper methods
    def _try_interact_with_npc(self):
        """Attempt to interact with nearby NPC"""
        if hasattr(self.game, 'try_interact_with_npc'):
            self.game.try_interact_with_npc()

    def _handle_building_interaction(self):
        """Handle building interaction (e.g., entering/exiting)"""
        if hasattr(self.game, 'handle_building_interaction'):
            self.game.handle_building_interaction()

    def _send_chat_message(self):
        """Send chat message to current NPC"""
        if (hasattr(self.game, 'chat_manager') and self.game.chat_manager and 
            hasattr(self.game, 'current_npc') and self.game.current_npc):
            
            # Check if we can send a message
            if not self.game.chat_manager.can_send_message():
                return
            
            # Use the ChatManager's send_message method which requires the NPC parameter
            if hasattr(self.game.chat_manager, 'send_message'):
                sent_message = self.game.chat_manager.send_message(self.game.current_npc)
                
                # If message was sent successfully, trigger AI response
                if sent_message:
                    self._trigger_ai_response(sent_message)

    def _trigger_ai_response(self, user_message):
        """Trigger AI response for the current NPC"""
        import asyncio
        from functions.ai import get_ai_response
        
        current_npc = self.game.current_npc
        if not current_npc:
            return
            
        # Set up the NPC for receiving a response
        current_npc.dialogue = "..."  # Show thinking indicator
        self.game.chat_manager.waiting_for_response = True
        
        # Create the AI prompt
        chat_history = current_npc.chat_history
        prompt = self._build_ai_prompt(current_npc, chat_history, user_message)
        
        # Start async AI request
        def handle_ai_response():
            try:
                # Get AI response (this should be the async function from your ai module)
                response = get_ai_response(prompt)
                
                # Limit response length if needed
                if hasattr(self.game, 'limit_npc_response'):
                    response = self.game.limit_npc_response(response)
                
                # Set the NPC dialogue and start typing animation
                current_npc.dialogue = response
                current_npc.bubble_dialogue = response[:50] + "..." if len(response) > 50 else response
                
                # Start typing animation
                self.game.chat_manager.start_typing_animation(response)
                self.game.chat_manager.waiting_for_response = False
                
            except Exception as e:
                print(f"AI response error: {e}")
                # Fallback response
                fallback = "Sorry, I'm having trouble thinking right now."
                current_npc.dialogue = fallback
                current_npc.bubble_dialogue = fallback
                self.game.chat_manager.waiting_for_response = False
        
        # Run the AI response in a separate thread to avoid blocking
        import threading
        thread = threading.Thread(target=handle_ai_response)
        thread.daemon = True
        thread.start()

    def _build_ai_prompt(self, npc, chat_history, user_message):
        """Build the AI prompt based on NPC and conversation history"""
        # Build conversation context
        conversation = ""
        for role, message in chat_history[-5:]:  # Last 5 messages for context
            if role == "player":
                conversation += f"Player: {message}\n"
            elif role == "npc":
                conversation += f"{npc.name}: {message}\n"
        
        # Add the current user message
        conversation += f"Player: {user_message}\n"
        
        # Create the prompt
        prompt = f"""You are {npc.name}, an NPC in a simulation game. You should respond naturally and in character.

Character traits:
- Name: {npc.name}
- Personality: Friendly and helpful
- Location: In a simulated world

Recent conversation:
{conversation}

Respond as {npc.name} in 1-3 sentences. Be conversational and natural."""
        
        return prompt

    # Utility methods
    def is_overlay_active(self):
        """Check if any overlay is currently active"""
        return self.showing_version or self.showing_credits

    def get_overlay_system(self):
        """Get reference to overlay system for external use"""
        return self.overlay_system

def _handle_send_message(self):
        """Handle sending chat messages with proper lock checking"""
        # Check if we can send a message
        if not hasattr(self.game.chat_manager, 'can_send_message'):
            return
            
        if not self.game.chat_manager.can_send_message():
            print("Cannot send message - chat is locked or conditions not met")
            return
        
        # Use the game's send method if available
        if hasattr(self.game, 'send_chat_message'):
            self.game.send_chat_message()
        else:
            # Fallback implementation
            self._send_message_fallback()
