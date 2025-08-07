import pygame
from typing import Optional
from config.settings import KEYBIND_MENU_SETTINGS


class KeybindOverlayHandler:
    """Handles the keybind configuration overlay interface"""
    
    def __init__(self, overlay_system, keybind_manager):
        self.overlay_system = overlay_system
        self.keybind_manager = keybind_manager
        
        # State tracking
        self.scroll_offset = 0
        self.max_scroll = 0
        self.listening_action = None
        self.conflict_message = None
        self.conflict_timer = 0
        self.interactive_elements = {}
        self.reset_confirmation = False
        
        # Save feedback state
        self.save_feedback_time = None
        
        # IMPROVED Scrolling settings
        self.scroll_speed = 3  # Reduced for smoother scrolling
        self.items_per_page = 12  # Better fit
        self.item_height = 50  # Increased spacing to prevent overlap
        
        # Dragging scrollbar
        self.dragging_scrollbar = False
        self.drag_start_y = 0
        self.drag_start_scroll = 0
    
    def handle_event(self, event) -> str:
        """
        Handle events for the keybind overlay
        Returns: action to take ('close', 'none', etc.)
        """
        if event.type == pygame.KEYDOWN:
            if self.listening_action:
                # Listening for key input
                return self._handle_key_assignment(event)
            elif event.key == pygame.K_ESCAPE:
                return 'close'
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                return self._handle_mouse_click(event.pos)
            elif event.button == 4:  # Mouse wheel up
                self._scroll_up()
            elif event.button == 5:  # Mouse wheel down
                self._scroll_down()
        
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self._scroll_up()
            elif event.y < 0:
                self._scroll_down()
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_scrollbar:
                self.dragging_scrollbar = False
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_scrollbar:
                self._handle_scrollbar_drag(event.pos[1])
        
        return 'none'
    
    def _handle_key_assignment(self, event) -> str:
        """Handle key assignment when listening for input"""
        if event.key == pygame.K_ESCAPE:
            # Cancel key assignment
            self.listening_action = None
            self.conflict_message = None
            return 'none'
        
        # Check if it's a modifier key combo
        pressed_keys = pygame.key.get_pressed()
        new_key = event.key
        
        # Check for common combos (Ctrl+key, Alt+key, etc.)
        if pressed_keys[pygame.K_LCTRL] or pressed_keys[pygame.K_RCTRL]:
            new_key = [pygame.K_LCTRL, event.key]
        elif pressed_keys[pygame.K_LALT] or pressed_keys[pygame.K_RALT]:
            new_key = [pygame.K_LALT, event.key]
        elif pressed_keys[pygame.K_LSHIFT] or pressed_keys[pygame.K_RSHIFT]:
            new_key = [pygame.K_LSHIFT, event.key]
        
        # Validate the new keybind
        is_valid, message = self.keybind_manager.validate_keybind(self.listening_action, new_key)
        
        if is_valid:
            # Set the new keybind
            self.keybind_manager.set_key(self.listening_action, new_key, temporary=True)
            self.listening_action = None
            self.conflict_message = None
        else:
            # Show conflict message
            self.conflict_message = message
            self.conflict_timer = pygame.time.get_ticks()
            self.listening_action = None
        
        return 'none'
    
    def _handle_mouse_click(self, pos) -> str:
        """Handle mouse clicks on overlay elements - FIXED VERSION"""
        # Get elements from the overlay system
        elements = self.overlay_system.draw_keybind_overlay(
            self.keybind_manager, self.scroll_offset, 
            self.listening_action, self.conflict_message
        )
        
        # Store elements for other methods
        self.interactive_elements = elements
        
        # Check if clicking inside the panel - if so, handle internal clicks
        if elements.get("panel_rect") and elements["panel_rect"].collidepoint(pos):
            # Check close button first
            if elements.get("close_button") and elements["close_button"].collidepoint(pos):
                return 'close'
            
            # Check keybind buttons
            for action, button_rect in elements.get("keybind_buttons", {}).items():
                if button_rect.collidepoint(pos):
                    self.listening_action = action
                    self.conflict_message = None
                    return 'none'
            
            # Check control buttons
            if elements.get("reset_button") and elements["reset_button"].collidepoint(pos):
                if not hasattr(self, 'reset_confirmation') or not self.reset_confirmation:
                    self.reset_confirmation = True
                    self.conflict_message = "!! Click Reset again to confirm !!"
                    self.conflict_timer = pygame.time.get_ticks()
                else:
                    self.keybind_manager.reset_to_defaults()
                    self.reset_confirmation = False
                    self.listening_action = None
                    self.conflict_message = "Reset to defaults"
                    self.conflict_timer = pygame.time.get_ticks()
                return 'none'
            
            # FIXED: Save button doesn't close overlay
            if elements.get("save_button") and elements["save_button"].collidepoint(pos):
                self.keybind_manager.apply_temp_keybinds()
                success = self.keybind_manager.save_keybinds()
                if success:
                    self.conflict_message = "Settings saved!"
                    self.save_feedback_time = pygame.time.get_ticks()
                    # Trigger visual feedback on overlay system
                    if hasattr(self.overlay_system, 'trigger_save_feedback'):
                        self.overlay_system.trigger_save_feedback()
                else:
                    self.conflict_message = "Failed to save settings"
                self.conflict_timer = pygame.time.get_ticks()
                return 'none'  # Don't close overlay!
            
            if elements.get("cancel_button") and elements["cancel_button"].collidepoint(pos):
                self.keybind_manager.cancel_temp_keybinds()
                self.listening_action = None
                self.conflict_message = None
                return 'close'
            
            # Check scrollbar
            if elements.get("scrollbar") and elements["scrollbar"].collidepoint(pos):
                self._start_scrollbar_drag(pos[1], elements["scrollbar"])
                return 'none'
            
            # Click was inside panel but not on any button - do nothing
            return 'none'
        
        # FIXED: Click outside panel doesn't close overlay - user must use close button or ESC
        return 'none'
    
    def _scroll_up(self):
        """Scroll up in the keybind list with MUCH smoother movement"""
        self.scroll_offset = max(0, self.scroll_offset - self.scroll_speed * 5)  # Reduced from 15 to 5

    def _scroll_down(self):
        """Scroll down in the keybind list with MUCH smoother movement"""
        self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.scroll_speed * 5)  # Reduced from 15 to 5
    
    def _start_scrollbar_drag(self, mouse_y, scrollbar_rect):
        """Start dragging the scrollbar"""
        self.dragging_scrollbar = True
        self.drag_start_y = mouse_y
        self.drag_start_scroll = self.scroll_offset
    
    def _handle_scrollbar_drag(self, mouse_y):
        """Handle scrollbar dragging"""
        if not self.dragging_scrollbar:
            return
        
        # Calculate new scroll position based on mouse movement
        delta_y = mouse_y - self.drag_start_y
        scroll_area_height = 500  # Approximate scroll area height
        scroll_ratio = delta_y / scroll_area_height
        scroll_delta = scroll_ratio * self.max_scroll
        
        new_scroll = self.drag_start_scroll + scroll_delta
        self.scroll_offset = max(0, min(self.max_scroll, new_scroll))
    
    def update(self):
        """Update the overlay state"""
        current_time = pygame.time.get_ticks()
        
        # Clear conflict message after 3 seconds
        if self.conflict_message and current_time - self.conflict_timer > 3000:
            self.conflict_message = None
        
        # Clear save feedback after 1 second
        if (self.save_feedback_time and 
            current_time - self.save_feedback_time > 1000):
            self.save_feedback_time = None
        
        # Calculate max scroll based on content
        from config.settings import KEYBIND_CATEGORIES
        total_items = sum(len(actions) for actions in KEYBIND_CATEGORIES.values())
        total_categories = len(KEYBIND_CATEGORIES)

        content_height = sum(
            KEYBIND_MENU_SETTINGS["category_height"] + len(v) * KEYBIND_MENU_SETTINGS["item_height"] + 15
            for v in KEYBIND_CATEGORIES.values()
        ) + 300  # Increased padding at bottom

        visible_height = 600  # Reduced to account for button area
        self.max_scroll = max(0, content_height - visible_height)
    
    def render(self):
        """Render the keybind overlay"""
        self.update()
        
        # Pass save feedback state to overlay system
        if self.save_feedback_time and hasattr(self.overlay_system, '_save_feedback_time'):
            self.overlay_system._save_feedback_time = self.save_feedback_time / 1000.0  # Convert to seconds
        
        return self.overlay_system.draw_keybind_overlay(
            self.keybind_manager, self.scroll_offset, 
            self.listening_action, self.conflict_message
        )
    
    def get_interactive_elements(self):
        """Get the current interactive elements"""
        return self.interactive_elements
    
    def save_keybinds(self):
        """Save keybind settings with feedback"""
        self.keybind_manager.apply_temp_keybinds()
        success = self.keybind_manager.save_keybinds()
        if success:
            self.conflict_message = "Settings saved!"
            self.save_feedback_time = pygame.time.get_ticks()
            if hasattr(self.overlay_system, 'trigger_save_feedback'):
                self.overlay_system.trigger_save_feedback()
        else:
            self.conflict_message = "Failed to save settings"
        self.conflict_timer = pygame.time.get_ticks()
    
    def start_listening_for_key(self, action: str):
        """Start listening for a key press for the given action"""
        self.listening_action = action
        self.conflict_message = None
    
    def reset_all_keybinds(self):
        """Reset all keybinds to defaults"""
        self.keybind_manager.reset_to_defaults()
        self.listening_action = None
        self.conflict_message = "Reset to defaults"
        self.conflict_timer = pygame.time.get_ticks()
    
    def reset_state(self):
        """Reset the overlay state when opening"""
        self.scroll_offset = 0
        self.listening_action = None
        self.conflict_message = None
        self.dragging_scrollbar = False
        self.save_feedback_time = None
        self.reset_confirmation = False