import pygame
from core.states import GameState
from systems.overlay_system import OverlaySystem
from managers.chat_manager import ChatManager
from entities.npc import NPC
from systems.ai_command_system import NPCCommandHandler

class EventHandler:
    """Centralized event handling system with overlay support"""
    
    def __init__(self, game):
        """
        Initialize the event handler
        
        Args:
            game: Reference to the main Game instance
        """
        self.game = game
        
        # Initialize overlay system
        self.overlay_system = OverlaySystem(
            self.game.screen,
            self.game.font_large,
            self.game.font_small,
            self.game.font_chat
        )
        
        # Initialize AI command handler
        self.command_handler = NPCCommandHandler()
        
        # Track overlay states
        self.showing_version = False
        self.showing_credits = False
        
        # Add overlay state tracking to game instance for backward compatibility
        self.game.showing_version = False
        self.game.showing_credits = False

    def handle_events(self):
        """Main event handling method - processes all pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.running = False
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mouse_wheel(event)
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event)

    def _handle_mouse_wheel(self, event):
        """Handle mouse wheel scrolling - primarily for chat interface"""
        if self.game.game_state == GameState.INTERACTING and self.game.current_npc:
            # ChatManager will handle the scroll logic internally
            # This is a placeholder for potential future scroll handling
            pass

    def _handle_keydown(self, event):
        """Route keyboard input to appropriate handler based on game state or overlays"""
        # Handle overlay escape first
        if self.showing_version or self.showing_credits:
            if event.key == pygame.K_ESCAPE:
                self._close_overlays()
                return

        if self.game.game_state == GameState.START_SCREEN:
            self._handle_start_screen_keys(event)
        elif self.game.game_state == GameState.PLAYING:
            self._handle_playing_keys(event)
        elif self.game.game_state == GameState.INTERACTING:
            self._handle_interaction_keys(event)
        elif self.game.game_state == GameState.SETTINGS:
            self._handle_settings_keys(event)

    def _handle_start_screen_keys(self, event):
        """Handle keyboard input on the start screen"""
        if event.key == pygame.K_p:
            self.game.game_state = GameState.PLAYING
        elif event.key == pygame.K_LCTRL and event.key == pygame.K_q:
            self.game.running = False

    def _handle_playing_keys(self, event):
        """Handle keyboard input during gameplay"""
        if event.key == pygame.K_ESCAPE:
            self.game.game_state = GameState.SETTINGS
        elif event.key == pygame.K_RETURN:
            # Try to interact with NPC if nearby
            self._try_interact_with_npc()
        elif event.key == pygame.K_F1:
            self.game.toggle_debug_hitboxes()
        elif event.key == pygame.K_e:
            # Outside building - handle building entry
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

    def handle_debug_collision(self, game):
        """Debug collision at player's current position"""
        player_x = game.player.rect.centerx
        player_y = game.player.rect.centery
        game.debug_collision_at_position(player_x, player_y)

    def _handle_interaction_keys(self, event):
        """Handle keyboard input during NPC interaction/chat"""
        current_time = pygame.time.get_ticks()
        
        # Check if input is blocked due to typing animation or cooldown
        if (self.game.chat_manager.typing_active or 
            (self.game.chat_manager.input_block_time and 
             current_time < self.game.chat_manager.input_block_time)):
            # Only allow escape during blocked input
            if event.key != pygame.K_ESCAPE:
                return

        if event.key == pygame.K_ESCAPE:
            self._exit_interaction()
        elif event.key == pygame.K_RETURN:
            # Send the message - the _trigger_ai_response method will handle command processing
            self._send_chat_message()
        elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
            # Remove last character from chat input
            self.game.chat_manager.message = self.game.chat_manager.message[:-1]
        elif event.unicode and event.unicode.isprintable():
            # Add printable characters to chat input
            self.game.chat_manager.message += event.unicode

    def _handle_settings_keys(self, event):
        """Handle keyboard input in settings menu"""
        if event.key == pygame.K_ESCAPE:
            self.game.game_state = GameState.PLAYING

    def _handle_mouse_click(self, event):
        """Handle mouse clicks based on current game state"""
        # Handle overlay clicks first
        if self.showing_version:
            if self.overlay_system.handle_overlay_click(event.pos, "version"):
                self._close_overlays()
                return
        elif self.showing_credits:
            if self.overlay_system.handle_overlay_click(event.pos, "credits"):
                self._close_overlays()
                return

        # Regular game state clicks
        if self.game.game_state == GameState.START_SCREEN:
            self._handle_start_screen_click(event)
        elif self.game.game_state == GameState.SETTINGS:
            self._handle_settings_click(event)

    def _handle_start_screen_click(self, event):
        """Handle mouse clicks on the start screen"""
        button_clicked = self.game.start_screen.handle_click(event.pos)
        if button_clicked == "start":
            self.game.game_state = GameState.PLAYING
        elif button_clicked == "settings":
            self.game.game_state = GameState.SETTINGS
        elif button_clicked == "quit":
            self.game.running = False

    def _handle_settings_click(self, event):
        """Handle mouse clicks in the settings menu using dynamic button/action list"""
        mx, my = event.pos
        buttons = self.game.ui_manager.draw_settings_menu()
        
        for rect, action in buttons:
            if rect.collidepoint(mx, my):
                if action == "return_to_game":
                    self.game.game_state = GameState.PLAYING
                elif action == "return_to_title":
                    self.game.game_state = GameState.START_SCREEN
                elif action == "show_credits":
                    self._show_credits_overlay()
                elif action == "show_version":
                    self._show_version_overlay()
                elif action == "toggle_sound":
                    self._toggle_sound()
                elif action == "quit_game":
                    self.game.running = False
                break

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

    def _exit_interaction(self):
        """Exit current NPC interaction"""
        if hasattr(self.game, 'exit_interaction'):
            self.game.exit_interaction()
        else:
            # Fallback to changing game state
            self.game.game_state = GameState.PLAYING

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
        
        # First, check if this is a command
        command_response = self.command_handler.handle_player_message(user_message, current_npc, self.game.player)
        
        if command_response:
            # This was a command, use the command response
            current_npc.dialogue = command_response
            current_npc.bubble_dialogue = command_response[:50] + "..." if len(command_response) > 50 else command_response
            self.game.chat_manager.start_typing_animation(command_response)
            
            # Add the command response to chat history
            current_npc.chat_history.append(("npc", command_response))
            
            # Don't exit interaction state - let player continue chatting
            # Just clear the message input
            self.game.chat_manager.message = ""
            
            # Clear the thinking state
            self.game.chat_manager.waiting_for_response = False
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

    def _toggle_sound(self):
        """Toggle sound on/off"""
        if hasattr(self.game, 'toggle_sound'):
            self.game.toggle_sound()

    # Rendering methods for overlays
    def render_overlays(self):
        """Render active overlays - call this in your main game loop"""
        if self.showing_version:
            self.overlay_system.draw_version_overlay()
        elif self.showing_credits:
            self.overlay_system.draw_credits_overlay()

    def render_corner_version(self):
        """Render version in corner - call this in your main game loop"""
        if not (self.showing_version or self.showing_credits):
            self.overlay_system.draw_corner_version()

    # Utility methods
    def is_overlay_active(self):
        """Check if any overlay is currently active"""
        return self.showing_version or self.showing_credits

    def get_overlay_system(self):
        """Get reference to overlay system for external use"""
        return self.overlay_system