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
        # Load defaults from JSON first, fallback to hardcoded
        self.default_keybinds = self.load_default_keybinds_from_json()
        self.keybinds = self.default_keybinds.copy()
        self.temp_keybinds = {}  # For temporary changes before saving
        self.original_keybinds_backup = {}  # NEW: Backup of original state
        self.keybind_file = os.path.join(CONFIG_DIR, "keybinds.json")
        self.load_keybinds()

    def load_default_keybinds_from_json(self):
        """Load default keybinds from JSON file"""
        import json
        try:
            json_path = os.path.join(CONFIG_DIR, "keybinds.json")
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    json_keybinds = json.load(f)
                
                # Convert JSON structure to flat dictionary
                flat_keybinds = {}
                for category, keybinds in json_keybinds.items():
                    for action, key_data in keybinds.items():
                        if isinstance(key_data, list):  # Combo keys
                            flat_keybinds[action] = [self._string_to_key(k) for k in key_data]
                        else:
                            flat_keybinds[action] = self._string_to_key(key_data)
                
                return flat_keybinds
            else:
                print("Default keybinds JSON not found, using hardcoded defaults")
                return DEFAULT_KEYBINDS.copy()
        except Exception as e:
            print(f"Error loading default keybinds JSON: {e}")
            return DEFAULT_KEYBINDS.copy()
    
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
        """Get the effective key for an action (temp takes priority)"""
        # Check temp keybinds first
        if hasattr(self, 'temp_keybinds') and action in self.temp_keybinds:
            temp_key = self.temp_keybinds[action]
            # If temp key is None, this action was temporarily disabled
            # Return None so it appears unbound
            return temp_key
        
        # Fall back to main keybinds
        return self.keybinds.get(action)
    
    def save_keybinds(self):
        """Save only custom keybinds (that differ from defaults) to file"""
        try:
            # Ensure config directory exists
            os.makedirs(CONFIG_DIR, exist_ok=True)
            
            # Load existing custom keybinds if file exists
            existing_custom = {}
            if os.path.exists(self.keybind_file):
                try:
                    with open(self.keybind_file, 'r') as f:
                        existing_custom = json.load(f)
                except:
                    existing_custom = {}
            
            # Only update keybinds that are different from defaults
            for action, key_data in self.keybinds.items():
                default_key = self.default_keybinds.get(action)
                if key_data != default_key:  # Different from default - save it
                    if isinstance(key_data, list):  # Combo keys
                        existing_custom[action] = [self._key_to_string(k) for k in key_data]
                    else:
                        existing_custom[action] = self._key_to_string(key_data)
                elif action in existing_custom:  # Same as default but was custom before - remove it
                    del existing_custom[action]
            
            # Save the updated custom keybinds
            with open(self.keybind_file, 'w') as f:
                json.dump(existing_custom, f, indent=2)
            
            print(f"Saved {len(existing_custom)} custom keybinds")
            return True
            
        except Exception as e:
            print(f"Error saving keybinds: {e}")
            return False
    
    def get_key(self, action: str) -> Any:
        """Get the key(s) bound to an action (temp takes priority)"""
        # Check temp keybinds first (for immediate effect during configuration)
        if hasattr(self, 'temp_keybinds') and action in self.temp_keybinds:
            return self.temp_keybinds[action]
        
        # Fall back to main keybinds
        return self.keybinds.get(action)
    
    def has_custom_keybind(self, action: str) -> bool:
        """Check if an action has a custom keybind (different from default)"""
        return (action in self.keybinds and 
                self.keybinds[action] != DEFAULT_KEYBINDS.get(action))

    def set_key(self, action: str, new_key: Any, temporary: bool = False):
        """Set a new key for an action, resolving conflicts"""
        if temporary:
            if not hasattr(self, 'temp_keybinds'):
                self.temp_keybinds = {}
            
            # First, remove any existing temp assignment for this action
            if action in self.temp_keybinds:
                del self.temp_keybinds[action]
            
            # Check for conflicts ONLY against main keybinds (not temp ones)
            conflicting_action = None
            for existing_action, existing_key in self.keybinds.items():
                if existing_action == action:
                    continue
                if existing_key == new_key:
                    conflicting_action = existing_action
                    break
            
            # If there's a conflict, temporarily clear it
            if conflicting_action:
                print(f"Temporarily clearing {conflicting_action} to resolve conflict")
                self.temp_keybinds[conflicting_action] = None
            
            # Set the new temporary keybind
            self.temp_keybinds[action] = new_key
            print(f"Temporarily set {action} to {self.get_key_display_name(new_key)}")
            
        else:
            # Remove conflicts from main keybinds
            for existing_action, existing_key in list(self.keybinds.items()):
                if existing_key == new_key and existing_action != action:
                    self.keybinds[existing_action] = None
                    print(f"Cleared {existing_action} to avoid conflict with {action}")
            
            self.keybinds[action] = new_key
            print(f"Set {action} to {self.get_key_display_name(new_key)}")
    
    def apply_temp_keybinds(self):
        """Apply temporary keybinds to main keybinds"""
        if hasattr(self, 'temp_keybinds'):
            self.keybinds.update(self.temp_keybinds)
            self.temp_keybinds.clear()
        
        # Clear the backup since changes are now permanent
        if hasattr(self, 'original_keybinds_backup'):
            self.original_keybinds_backup.clear()
    
    def cancel_temp_keybinds(self):
        """Cancel temporary keybinds"""
        if hasattr(self, 'temp_keybinds'):
            self.temp_keybinds.clear()
            print("Cleared all temporary keybinds")
    
    def reset_to_defaults(self):
        """Reset all keybinds to defaults and save"""
        self.keybinds = self.default_keybinds.copy()
        if hasattr(self, 'temp_keybinds'):
            self.temp_keybinds.clear()
        if hasattr(self, 'original_keybinds_backup'):
            self.original_keybinds_backup.clear()
        self.save_keybinds()
    
    def reset_action_to_default(self, action: str):
        """Reset a specific action to its default keybind"""
        if action in self.default_keybinds:
            if hasattr(self, 'temp_keybinds') and action in self.temp_keybinds:
                # If we're in temp mode, set temp to default
                self.temp_keybinds[action] = self.default_keybinds[action]
            else:
                # Otherwise set main keybind to default
                self.keybinds[action] = self.default_keybinds[action]
    
    def is_key_available(self, key: Any, exclude_action: str = None) -> bool:
        """Check if a key is available for binding"""
        # Check if key is reserved
        if isinstance(key, int) and key in RESERVED_KEYS:
            return False
        
        # Check if key conflicts with any effective keybind
        conflicting_actions = self.get_conflicting_actions(key, exclude_action)
        return len(conflicting_actions) == 0

    def get_conflicting_action(self, key: Any, exclude_action: str = None) -> Optional[str]:
        """Get the first action that conflicts with the given key"""
        conflicts = self.get_conflicting_actions(key, exclude_action)
        return conflicts[0] if conflicts else None
    
    def get_conflicting_actions(self, key: Any, exclude_action: str = None) -> List[str]:
        """Get all actions that conflict with the given key"""
        conflicts = []
        for action, bound_key in self.keybinds.items():
            if action == exclude_action:
                continue
            
            # Skip if this action has a temp override (including None)
            if hasattr(self, 'temp_keybinds') and action in self.temp_keybinds:
                continue
                
            if bound_key is None:
                continue
                
            if isinstance(bound_key, list):
                if isinstance(key, list):
                    if bound_key == key:
                        conflicts.append(action)
                elif key in bound_key:
                    conflicts.append(action)
            elif bound_key == key:
                conflicts.append(action)
        
        return conflicts
    
    def is_key_pressed(self, action: str, pressed_keys: Dict[int, bool] = None, 
                   event_key: int = None) -> bool:
        """Check if the key(s) for an action are currently pressed"""
        if pressed_keys is None:
            pressed_keys = pygame.key.get_pressed()
            
        bound_key = self.get_key(action)
        if bound_key is None:
            return False
        
        if isinstance(bound_key, list):  # Combo keys
            if event_key and event_key == bound_key[-1]:  # Last key in combo
                return all(pressed_keys[k] for k in bound_key[:-1])
            return False
        else:  # Single key
            if event_key:
                return event_key == bound_key
            return pressed_keys[bound_key]
    
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
    
    def get_display_key(self, action: str) -> Any:
        """Get the key to display (temp key if set, otherwise effective key)"""
        if hasattr(self, 'temp_keybinds') and action in self.temp_keybinds:
            return self.temp_keybinds[action]
        return self.get_effective_key(action)
    
    def get_conflicting_actions(self, key: Any, exclude_action: str = None) -> List[str]:
        """Get all actions that conflict with the given key"""
        conflicts = []
        for action, bound_key in self.keybinds.items():
            if action == exclude_action:
                continue
            
            if bound_key is None:
                continue
                
            if isinstance(bound_key, list):
                if isinstance(key, list):
                    if bound_key == key:
                        conflicts.append(action)
                elif key in bound_key:
                    conflicts.append(action)
            elif bound_key == key:
                conflicts.append(action)
        
        return conflicts

    def has_conflicts(self) -> Dict[str, List[str]]:
        """Get all current keybind conflicts"""
        conflicts = {}
        for action, key in self.keybinds.items():
            if key is None:
                continue
            conflicting = self.get_conflicting_actions(key, action)
            if conflicting:
                conflicts[action] = conflicting
        return conflicts
    
    def debug_current_keybinds(self):
        """Debug method to print current keybinds"""
        print("=== CURRENT KEYBINDS DEBUG ===")
        print("Main keybinds:")
        for action, key in self.keybinds.items():
            key_name = self.get_key_display_name(key) if key is not None else "UNBOUND"
            print(f"  {action}: {key_name}")
        
        if hasattr(self, 'temp_keybinds') and self.temp_keybinds:
            print("Temp keybinds:")
            for action, key in self.temp_keybinds.items():
                key_name = self.get_key_display_name(key) if key is not None else "CLEARED"
                print(f"  {action}: {key_name}")
        
        if hasattr(self, 'original_keybinds_backup') and self.original_keybinds_backup:
            print("Original backup exists")
        
        print("Effective keybinds:")
        movement_actions = ["move_up", "move_down", "move_left", "move_right", "run"]
        for action in movement_actions:
            effective_key = self.get_effective_key(action)
            key_name = self.get_key_display_name(effective_key) if effective_key is not None else "UNBOUND"
            print(f"  {action}: {key_name}")
        print("==============================")