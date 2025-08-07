import pygame
import json
import os
from typing import Dict, Any, List, Tuple, Optional
from config.settings import (
    DEFAULT_KEYBINDS, CURRENT_KEYBINDS, RESERVED_KEYS, 
    KEYBIND_DISPLAY_NAMES, CONFIG_DIR
)


class KeybindManager:
    """Manages custom keybinds for the game"""
    
    def __init__(self):
        self.keybinds = CURRENT_KEYBINDS.copy()
        self.temp_keybinds = {}  # For temporary changes before saving
        self.keybind_file = os.path.join(CONFIG_DIR, "keybinds.json")
        self.load_keybinds()
    
    def load_keybinds(self):
        """Load keybinds from file or use defaults"""
        try:
            if os.path.exists(self.keybind_file):
                with open(self.keybind_file, 'r') as f:
                    saved_keybinds = json.load(f)
                
                # Convert string keys back to pygame constants
                for action, key_data in saved_keybinds.items():
                    if isinstance(key_data, list):  # Combo keys
                        self.keybinds[action] = [self._string_to_key(k) for k in key_data]
                    else:
                        self.keybinds[action] = self._string_to_key(key_data)
                
                print("Keybinds loaded successfully")
            else:
                print("No keybind file found, using defaults")
                
        except Exception as e:
            print(f"Error loading keybinds: {e}, using defaults")
            self.keybinds = DEFAULT_KEYBINDS.copy()

    def get_effective_key(self, action: str) -> Any:
        """Get the effective key for an action (custom if set, otherwise default)"""
        # First check if there's a custom keybind
        if action in self.keybinds and self.keybinds[action] is not None:
            return self.keybinds[action]
        # Fall back to default
        return DEFAULT_KEYBINDS.get(action)
    
    def save_keybinds(self):
        """Save only custom keybinds (that differ from defaults) to file"""
        try:
            # Ensure config directory exists
            os.makedirs(CONFIG_DIR, exist_ok=True)
            
            # Only save keybinds that are different from defaults
            custom_keybinds = {}
            for action, key_data in self.keybinds.items():
                default_key = DEFAULT_KEYBINDS.get(action)
                if key_data != default_key:  # Only save if different from default
                    if isinstance(key_data, list):  # Combo keys
                        custom_keybinds[action] = [self._key_to_string(k) for k in key_data]
                    else:
                        custom_keybinds[action] = self._key_to_string(key_data)
            
            with open(self.keybind_file, 'w') as f:
                json.dump(custom_keybinds, f, indent=2)
            
            print(f"Saved {len(custom_keybinds)} custom keybinds")
            return True
            
        except Exception as e:
            print(f"Error saving keybinds: {e}")
            return False
    
    def get_key(self, action: str) -> Any:
        """Get the key(s) bound to an action (uses effective key logic)"""
        return self.get_effective_key(action)
    
    def has_custom_keybind(self, action: str) -> bool:
        """Check if an action has a custom keybind (different from default)"""
        return (action in self.keybinds and 
                self.keybinds[action] != DEFAULT_KEYBINDS.get(action))

    def set_key(self, action: str, new_key: Any, temporary: bool = False):
        """Set a new key for an action"""
        if temporary:
            if not hasattr(self, 'temp_keybinds'):
                self.temp_keybinds = {}
            self.temp_keybinds[action] = new_key
        else:
            self.keybinds[action] = new_key
    
    def apply_temp_keybinds(self):
        """Apply temporary keybinds to main keybinds"""
        if hasattr(self, 'temp_keybinds'):
            self.keybinds.update(self.temp_keybinds)
            self.temp_keybinds.clear()
    
    def cancel_temp_keybinds(self):
        """Cancel temporary keybinds"""
        if hasattr(self, 'temp_keybinds'):
            self.temp_keybinds.clear()
    
    def reset_to_defaults(self):
        """Reset all keybinds to defaults"""
        self.keybinds = DEFAULT_KEYBINDS.copy()
        self.temp_keybinds.clear()
    
    def reset_action_to_default(self, action: str):
        """Reset a specific action to its default keybind"""
        if action in DEFAULT_KEYBINDS:
            self.keybinds[action] = DEFAULT_KEYBINDS[action]
    
    def is_key_available(self, key: Any, exclude_action: str = None) -> bool:
        """Check if a key is available for binding"""
        # Check if key is reserved
        if isinstance(key, int) and key in RESERVED_KEYS:
            return False
        
        # Check if key conflicts with any effective keybind
        for action in DEFAULT_KEYBINDS.keys():
            if action == exclude_action:
                continue
                
            bound_key = self.get_effective_key(action)  # Use effective key
            if isinstance(bound_key, list):
                if isinstance(key, list):
                    if bound_key == key:
                        return False
                elif key in bound_key:
                    return False
            elif bound_key == key:
                return False
        
        return True
    
    def get_conflicting_action(self, key: Any, exclude_action: str = None) -> Optional[str]:
        """Get the action that conflicts with the given key"""
        for action, bound_key in self.keybinds.items():
            if action == exclude_action:
                continue
                
            if isinstance(bound_key, list):
                if isinstance(key, list):
                    if bound_key == key:
                        return action
                elif key in bound_key:
                    return action
            elif bound_key == key:
                return action
        
        return None
    
    def is_key_pressed(self, action: str, pressed_keys: Dict[int, bool], 
                       event_key: int = None) -> bool:
        """Check if the key(s) for an action are currently pressed"""
        bound_key = self.get_key(action)
        
        if isinstance(bound_key, list):  # Combo keys
            if event_key and event_key == bound_key[-1]:  # Last key in combo
                return all(pressed_keys.get(k, False) for k in bound_key[:-1])
            return False
        else:  # Single key
            if event_key:
                return event_key == bound_key
            return pressed_keys.get(bound_key, False)
    
    def get_key_display_name(self, key: Any) -> str:
        """Get human-readable name for a key or key combination"""
        if isinstance(key, list):
            return " + ".join(self._key_to_string(k) for k in key)
        else:
            return self._key_to_string(key)
    
    def _key_to_string(self, key: int) -> str:
        """Convert pygame key constant to string"""
        if key is None:
            return "None"
        
        # Special key mappings for better display
        key_names = {
            pygame.K_SPACE: "SPACE",
            pygame.K_RETURN: "ENTER",
            pygame.K_ESCAPE: "ESCAPE",
            pygame.K_BACKSPACE: "BACKSPACE",
            pygame.K_TAB: "TAB",
            pygame.K_LSHIFT: "Left SHIFT",
            pygame.K_RSHIFT: "Right SHIFT",
            pygame.K_LCTRL: "Left CTRL",
            pygame.K_RCTRL: "Right CTRL",
            pygame.K_LALT: "Left ALT",
            pygame.K_RALT: "Right ALT",
            pygame.K_UP: "Up ARROW",
            pygame.K_DOWN: "Down ARROW",
            pygame.K_LEFT: "Left ARROW",
            pygame.K_RIGHT: "Right ARROW",
        }
        
        if key in key_names:
            return key_names[key]
        
        # Try to get the name from pygame
        try:
            name = pygame.key.name(key)
            return name.capitalize()
        except:
            return f"Key_{key}"
    
    def _string_to_key(self, key_str: str) -> int:
        """Convert string back to pygame key constant"""
        if key_str == "None":
            return None
        
        # Special key mappings (reverse of _key_to_string)
        string_to_key = {
            "SPACE": pygame.K_SPACE,
            "ENTER": pygame.K_RETURN,
            "ESCAPE": pygame.K_ESCAPE,
            "BACKSPACE": pygame.K_BACKSPACE,
            "TAB": pygame.K_TAB,
            "Left SHIFT": pygame.K_LSHIFT,
            "Right SHIFT": pygame.K_RSHIFT,
            "Left CTRL": pygame.K_LCTRL,
            "Right CTRL": pygame.K_RCTRL,
            "Left ALT": pygame.K_LALT,
            "Right ALT": pygame.K_RALT,
            "Up ARROW": pygame.K_UP,
            "Down ARROW": pygame.K_DOWN,
            "Left ARROW": pygame.K_LEFT,
            "Right ARROW": pygame.K_RIGHT,
        }
        
        if key_str in string_to_key:
            return string_to_key[key_str]
        
        # Try to find the key by iterating through pygame keys
        for key_const in dir(pygame):
            if key_const.startswith('K_') and hasattr(pygame, key_const):
                key_val = getattr(pygame, key_const)
                try:
                    if pygame.key.name(key_val).lower() == key_str.lower():
                        return key_val
                except:
                    continue
        
        # Fallback: try to parse as integer
        try:
            return int(key_str.split('_')[-1])
        except:
            return pygame.K_UNKNOWN
    
    def validate_keybind(self, action: str, key: Any) -> Tuple[bool, str]:
        """Validate a keybind and return success status and message"""
        if key is None:
            return False, "Invalid key"
        
        if isinstance(key, int) and key in RESERVED_KEYS:
            return False, f"Key is reserved: {self.get_key_display_name(key)}"
        
        conflicting_action = self.get_conflicting_action(key, action)
        if conflicting_action:
            action_name = KEYBIND_DISPLAY_NAMES.get(conflicting_action, conflicting_action)
            return False, f"Key already bound to: {action_name}"
        
        return True, "Valid keybind"
    
    def get_all_actions(self) -> List[str]:
        """Get list of all available actions"""
        return list(DEFAULT_KEYBINDS.keys())
    
    def get_keybinds_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all keybinds showing default vs custom"""
        summary = {}
        for action in DEFAULT_KEYBINDS.keys():
            summary[action] = {
                'default': DEFAULT_KEYBINDS[action],
                'current': self.get_effective_key(action),
                'is_custom': self.has_custom_keybind(action),
                'display_name': KEYBIND_DISPLAY_NAMES.get(action, action)
            }
        return summary