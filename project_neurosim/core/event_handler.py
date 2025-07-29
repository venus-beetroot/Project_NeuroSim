"""
Event handler system for PROJECT NEUROSIM
Handles all user input events (keyboard, mouse, etc.)
"""
import pygame
from core.states import GameState


class EventHandler:
    """Centralized event handling system"""
    
    def __init__(self, game):
        """
        Initialize the event handler
        
        Args:
            game: Reference to the main Game instance
        """
        self.game = game
    
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
        """Route keyboard input to appropriate handler based on game state"""
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
        if event.key == pygame.K_RETURN:
            self.game.game_state = GameState.PLAYING
        elif event.key == pygame.K_ESCAPE:
            self.game.running = False
    
    def _handle_playing_keys(self, event):
        """Handle keyboard input during gameplay"""
        if event.key == pygame.K_ESCAPE:
            self.game.game_state = GameState.SETTINGS
        elif event.key == pygame.K_RETURN:
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
        """Handle mouse clicks in the settings menu"""
        from functions import app  # Import here to avoid circular imports
        
        mx, my = event.pos
        return_rect = pygame.Rect(app.WIDTH//2 - 150, app.HEIGHT//2 - 50, 300, 50)
        quit_rect = pygame.Rect(app.WIDTH//2 - 150, app.HEIGHT//2 + 10, 300, 50)
        
        if return_rect.collidepoint(mx, my):
            # Return to start screen instead of playing
            self.game.game_state = GameState.START_SCREEN
        elif quit_rect.collidepoint(mx, my):
            self.game.running = False
    
    def _try_interact_with_npc(self):
        """Attempt to interact with nearby NPCs"""
        for npc_obj in self.game.npcs:
            # Calculate distance between player and NPC
            distance = ((self.game.player.rect.centerx - npc_obj.rect.centerx) ** 2 + 
                       (self.game.player.rect.centery - npc_obj.rect.centery) ** 2) ** 0.5
            
            if distance <= 60:  # Interaction range in pixels
                self.game.game_state = GameState.INTERACTING
                self.game.current_npc = npc_obj
                self.game.chat_manager.message = ""
                break
    
    def _exit_interaction(self):
        """Exit NPC interaction and return to gameplay"""
        self.game.game_state = GameState.PLAYING
        self.game.chat_manager.message = ""
        self.game.current_npc = None
    
    def _handle_building_interaction(self):
        """Handle entering/exiting buildings"""
        if self.game.building_manager.is_inside_building():
            # Player is inside - try to exit
            if self.game.building_manager.check_building_exit(self.game.player.rect):
                success = self.game.building_manager.exit_building(self.game.player)
                if success:
                    # Ensure position is synchronized after exit
                    self.game.player.sync_position()
                    # Reset camera to follow player again
                    self.game.camera.follow(self.game.player)
                    print("Exited building")
        else:
            # Player is outside - try to enter building
            building = self.game.building_manager.check_building_entry(self.game.player.rect)
            if building:
                success = self.game.building_manager.enter_building(building, self.game.player)
                if success:
                    # Ensure position is synchronized after entry
                    self.game.player.sync_position()
                    # Track building entry for tips system
                    self.game._has_entered_building = True
                    print(f"Entered {building.building_type}")
    
    def _send_chat_message(self):
        """Send a chat message to the current NPC"""
        if not self.game.current_npc or not self.game.chat_manager.can_send_message():
            return
        
        # Set waiting state for loading indicator
        if hasattr(self.game.chat_manager, 'waiting_for_response'):
            self.game.chat_manager.waiting_for_response = True
        
        sent_message = self.game.chat_manager.send_message(self.game.current_npc)
        if sent_message:
            # Track NPC interaction for tips system
            self.game._has_talked_to_npc = True
            
            # Get AI response
            from functions.ai import get_ai_response
            prompt = self._build_ai_prompt(self.game.current_npc, sent_message)
            ai_response = get_ai_response(prompt)
            response_text = ai_response.content if hasattr(ai_response, "content") else str(ai_response)
            
            # Limit response length to 4 sentences max
            limited_response = self.game.limit_npc_response(response_text)
            
            # Set up NPC response
            self.game.current_npc.dialogue = limited_response
            self.game.chat_manager.start_typing_animation(limited_response)
            
            # Clear waiting state
            if hasattr(self.game.chat_manager, 'waiting_for_response'):
                self.game.chat_manager.waiting_for_response = False
    
    def _build_ai_prompt(self, npc_obj, new_message: str) -> str:
        """Build AI prompt for NPC response with length instruction"""
        prompt = f"You are {npc_obj.name}. "
        prompt += f"Your personality: {npc_obj.dialogue}\n"
        prompt += "Keep your responses short and conversational - maximum 4 sentences.\n"
        prompt += "Conversation history:\n"
        
        for speaker, message in npc_obj.chat_history:
            prompt += f"{speaker.capitalize()}: {message}\n"
        
        prompt += f"Player: {new_message}\n"
        prompt += f"{npc_obj.name}:"
        return prompt


class InputValidator:
    """Helper class for validating and sanitizing input"""
    
    @staticmethod
    def is_valid_chat_input(text: str) -> bool:
        """
        Validate chat input text
        
        Args:
            text: The input text to validate
            
        Returns:
            bool: True if input is valid, False otherwise
        """
        if not text or not text.strip():
            return False
        
        # Check for reasonable length limits
        if len(text) > 200:  # Maximum message length
            return False
        
        # Add other validation rules as needed
        return True
    
    @staticmethod
    def sanitize_chat_input(text: str) -> str:
        """
        Sanitize chat input by removing unwanted characters
        
        Args:
            text: The input text to sanitize
            
        Returns:
            str: Sanitized text
        """
        # Remove control characters but keep printable ones
        sanitized = ''.join(char for char in text if char.isprintable() or char.isspace())
        
        # Strip leading/trailing whitespace
        sanitized = sanitized.strip()
        
        return sanitized


class KeyBindings:
    """Class to manage key bindings and allow for customization"""
    
    def __init__(self):
        """Initialize default key bindings"""
        self.bindings = {
            # Gameplay controls
            'interact': pygame.K_RETURN,
            'building_enter_exit': pygame.K_e,
            'settings': pygame.K_ESCAPE,
            
            # Debug controls (development only)
            'debug_hitboxes': pygame.K_F1,
            'restart_tutorial': pygame.K_F2,
            'test_movement_tip': pygame.K_F3,
            'test_interaction_tip': pygame.K_F4,
            'test_building_tip': pygame.K_F5,
            
            # Chat controls
            'send_message': pygame.K_RETURN,
            'exit_chat': pygame.K_ESCAPE,
            'delete_char': pygame.K_BACKSPACE,
        }
    
    def get_key(self, action: str) -> int:
        """
        Get the key code for a specific action
        
        Args:
            action: The action name
            
        Returns:
            int: Pygame key code, or None if action not found
        """
        return self.bindings.get(action)
    
    def set_key(self, action: str, key_code: int):
        """
        Set a new key binding for an action
        
        Args:
            action: The action name
            key_code: The new pygame key code
        """
        self.bindings[action] = key_code
    
    def is_key_for_action(self, key_code: int, action: str) -> bool:
        """
        Check if a key code matches a specific action
        
        Args:
            key_code: The pygame key code to check
            action: The action name
            
        Returns:
            bool: True if the key matches the action
        """
        return self.bindings.get(action) == key_code