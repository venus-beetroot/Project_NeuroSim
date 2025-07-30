import pygame
import random
import math
from functions import app
from entities.player import Player


class NPCDialogue:
    """Handles NPC dialogue and personality definitions"""
    
    DIALOGUE_DATA = {
        "Dave": {
            "bubble": "Hello, I'm Dave. I love adventures in this digital world!",
            "personality": "You are Dave, an adventurous NPC who loves exploring the digital world. You're friendly and enthusiastic about new experiences."
        },
        "Lisa": {
            "bubble": "Hi, I'm Lisa. Coding and coffee fuel my day!",
            "personality": "You are Lisa, a tech-savvy NPC who loves coding and coffee. You're knowledgeable and helpful with technical topics."
        },
        "Tom": {
            "bubble": "Hey, I'm Tom. Always here to keep things running smoothly!",
            "personality": "You are Tom, a reliable NPC who keeps things organized and running smoothly. You're dependable and solution-oriented."
        }
    }
    
    DEFAULT_DIALOGUE = {
        "bubble": "Hello, I'm just an NPC.",
        "personality": "You are a generic NPC in a game world."
    }
    
    @classmethod
    def get_dialogue(cls, name):
        """Get dialogue data for an NPC by name"""
        return cls.DIALOGUE_DATA.get(name, cls.DEFAULT_DIALOGUE)


class NPCMovement:
    """Handles NPC movement and pathfinding logic"""
    
    def __init__(self, npc):
        self.npc = npc
        self.target_x = npc.x
        self.target_y = npc.y
        self.movement_timer = 0
        self.movement_delay = random.randint(120, 300)
    
    def choose_new_target(self, buildings=None):
        """Choose a new target position for movement"""
        # Try to enter building (20% chance if conditions are met)
        if self._should_try_building_entry(buildings):
            building = self._find_nearest_building(buildings)
            if building:
                self.target_x = building.rect.centerx
                self.target_y = building.rect.centery
                print(f"{self.npc.name} is heading to {building.building_type}")
                return
        
        # Normal movement behavior
        self._choose_random_target()
    
    def _should_try_building_entry(self, buildings):
        """Check if NPC should try to enter a building"""
        return (buildings and not self.npc.building_state.is_inside_building and 
                self.npc.building_state.interaction_cooldown <= 0 and 
                random.random() < 0.2)
    
    def _find_nearest_building(self, buildings):
        """Find the nearest enterable building within range"""
        nearby_buildings = []
        for building in buildings:
            distance = self.npc._get_distance_to_building(building)
            if distance < 300 and building.can_enter:
                nearby_buildings.append((building, distance))
        
        if nearby_buildings:
            nearby_buildings.sort(key=lambda x: x[1])
            return nearby_buildings[0][0]
        return None
    
    def _choose_random_target(self):
        """Choose a random target within or outside hangout area"""
        hangout = self.npc.hangout_area
        
        if random.random() < 0.75:
            # Move within hangout area
            self.target_x = random.randint(hangout['x'], hangout['x'] + hangout['width'])
            self.target_y = random.randint(hangout['y'], hangout['y'] + hangout['height'])
        else:
            # Wander elsewhere
            self.target_x = random.randint(hangout['x'] - 200, hangout['x'] + hangout['width'] + 200)
            self.target_y = random.randint(hangout['y'] - 200, hangout['y'] + hangout['height'] + 200)
    
    def move_towards_target(self):
        """Move NPC towards target position"""
        dx = self.target_x - self.npc.rect.centerx
        dy = self.target_y - self.npc.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 5:
            # Calculate movement vector
            move_x = (dx / distance) * self.npc.speed
            move_y = (dy / distance) * self.npc.speed
            
            # Update position and facing direction
            self.npc.rect.centerx += move_x
            self.npc.rect.centery += move_y
            self.npc.facing_left = move_x < 0
            
            # Set animation state
            self.npc.state = "run" if "run" in self.npc.animations else "idle"
        else:
            self.npc.state = "idle"
    
    def update_movement_timer(self):
        """Update movement timing"""
        self.movement_timer += 1
        if self.movement_timer >= self.movement_delay:
            self.movement_timer = 0
            self.movement_delay = random.randint(120, 300)
            return True
        return False


class NPCBuildingState:
    """Manages NPC building interaction state - FIXED VERSION"""
    
    def __init__(self):
        self.is_inside_building = False
        self.current_building = None
        self.exterior_position = None
        self.building_timer = 0
        self.stay_duration = random.randint(300, 900)
        self.interaction_cooldown = 0
        self.interaction_delay = 300
    
    def try_enter_building(self, npc, buildings, building_manager):
        """Attempt to enter a nearby building - FIXED"""
        if self.is_inside_building or self.interaction_cooldown > 0:
            return False
        
        for building in buildings:
            if self._can_enter_building(npc, building):
                return self._enter_building(npc, building, building_manager)
        return False
    
    def _can_enter_building(self, npc, building):
        """Check if NPC can enter a specific building - IMPROVED"""
        if not building.can_enter:
            return False
            
        # Check distance to building
        distance = npc._get_distance_to_building(building)
        if distance > 60:  # Close enough to enter
            return False
            
        # Check if building has capacity (if it tracks NPCs)
        if hasattr(building, 'can_npc_enter'):
            return building.can_npc_enter()
            
        return True
    
    def _enter_building(self, npc, building, building_manager):
        """Handle entering a building - FIXED"""
        print(f"DEBUG: {npc.name} attempting to enter {building.building_type}")
        
        # Save exterior position
        self.exterior_position = {'x': npc.rect.centerx, 'y': npc.rect.centery}
        print(f"DEBUG: Saved exterior position: {self.exterior_position}")
        
        # Try to use building manager if available
        if building_manager and hasattr(building_manager, 'enter_building_for_npc'):
            success = building_manager.enter_building_for_npc(building, npc)
            if not success:
                print(f"DEBUG: Building manager failed to enter {npc.name}")
                return False
        else:
            # Fallback: manually enter building
            if hasattr(building, 'add_npc'):
                building.add_npc(npc)
        
        # Position NPC in building
        self._position_npc_in_building(npc, building)
        
        # Update state
        self.is_inside_building = True
        self.current_building = building
        self.building_timer = 0
        self.stay_duration = random.randint(300, 900)
        
        print(f"SUCCESS: {npc.name} entered {building.building_type}")
        return True
    
    def _position_npc_in_building(self, npc, building):
        """Position NPC inside the building - IMPROVED"""
        if hasattr(building, 'get_interior_spawn_point'):
            # Use building's spawn point method
            spawn_x, spawn_y = building.get_interior_spawn_point()
            npc.rect.centerx = spawn_x
            npc.rect.centery = spawn_y
        elif hasattr(building, 'exit_zone') and building.exit_zone:
            # Position near exit zone with some randomness
            npc.rect.centerx = building.exit_zone.centerx + random.randint(-30, 30)
            npc.rect.centery = building.exit_zone.centery + random.randint(-30, 30)
        else:
            # Default positioning
            interior_width, interior_height = getattr(building, 'interior_size', (800, 600))
            npc.rect.centerx = interior_width // 2 + random.randint(-50, 50)
            npc.rect.centery = interior_height // 2 + random.randint(-50, 50)
            
        print(f"DEBUG: Positioned {npc.name} at ({npc.rect.centerx}, {npc.rect.centery})")
    
    def try_exit_building(self, npc, building_manager=None):
        """Attempt to exit current building - FIXED"""
        if not self.is_inside_building or not self.current_building:
            return False
        
        # Check if near exit
        if self._is_near_exit(npc):
            return self._exit_building(npc, building_manager)
        else:
            # Move toward exit
            self._move_toward_exit(npc)
            return False
    
    def _is_near_exit(self, npc):
        """Check if NPC is near the exit - IMPROVED"""
        if not self.current_building:
            return False
            
        if hasattr(self.current_building, 'exit_zone') and self.current_building.exit_zone:
            # Check distance to exit zone
            dx = npc.rect.centerx - self.current_building.exit_zone.centerx
            dy = npc.rect.centery - self.current_building.exit_zone.centery
            distance = math.sqrt(dx * dx + dy * dy)
            return distance < 40
        
        # Fallback: assume near exit if near edge of interior
        interior_width, interior_height = getattr(self.current_building, 'interior_size', (800, 600))
        margin = 50
        return (npc.rect.centerx < margin or npc.rect.centerx > interior_width - margin or
                npc.rect.centery < margin or npc.rect.centery > interior_height - margin)
    
    def _exit_building(self, npc, building_manager=None):
        """Handle exiting a building - FIXED"""
        print(f"DEBUG: {npc.name} attempting to exit {self.current_building.building_type}")
        
        building_ref = self.current_building
        
        # Try to use building manager if available
        if building_manager and hasattr(building_manager, 'exit_building_for_npc'):
            success = building_manager.exit_building_for_npc(npc)
            if not success:
                print(f"DEBUG: Building manager failed to exit {npc.name}")
                return False
        else:
            # Fallback: manually exit building
            if hasattr(building_ref, 'remove_npc'):
                building_ref.remove_npc(npc)
        
        # Restore exterior position
        if self.exterior_position:
            npc.rect.centerx = self.exterior_position['x']
            npc.rect.centery = self.exterior_position['y']
            print(f"DEBUG: Restored {npc.name} to exterior position: {self.exterior_position}")
        else:
            # Fallback: position outside building
            npc.rect.centerx = building_ref.rect.centerx + random.randint(-60, 60)
            npc.rect.centery = building_ref.rect.centery + 80  # Below building
        
        # Reset state
        self.is_inside_building = False
        self.current_building = None
        self.exterior_position = None
        self.interaction_cooldown = self.interaction_delay
        
        print(f"SUCCESS: {npc.name} exited building")
        return True
    
    def _move_toward_exit(self, npc):
        """Move NPC toward building exit - IMPROVED"""
        if self.current_building and hasattr(self.current_building, 'exit_zone') and self.current_building.exit_zone:
            exit_center = self.current_building.exit_zone.center
            npc.movement.target_x = exit_center[0]
            npc.movement.target_y = exit_center[1]
        else:
            # Move toward center as fallback
            interior_width, interior_height = getattr(self.current_building, 'interior_size', (800, 600))
            npc.movement.target_x = interior_width // 2
            npc.movement.target_y = interior_height // 2
    
    def update_timers(self):
        """Update building-related timers"""
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1
        if self.is_inside_building:
            self.building_timer += 1


class NPCInteraction:
    """Handles NPC player interaction and speech bubbles - FIXED VERSION"""
    
    def __init__(self, npc):
        self.npc = npc
        self.show_speech_bubble = False
        self.speech_bubble_timer = 0
        self.speech_bubble_duration = 180
        self.detection_radius = 80
        self.stop_distance = 50
        self.bubble_text = ""  # Store the current bubble text
        
        # CRITICAL: Initialize default bubble text
        self.bubble_text = npc.bubble_dialogue if hasattr(npc, 'bubble_dialogue') else "Hello!"
    
    def update_player_interaction(self, player, building_manager):
        """Update interaction with player - FIXED"""
        if not player or not self._in_same_location(player, building_manager):
            # Only reset if this was a player interaction
            if hasattr(self.npc, '_stopped_by_player_interaction'):
                self.npc.is_stopped_by_player = False
                delattr(self.npc, '_stopped_by_player_interaction')
            return
        
        distance = self.npc._get_distance_to_player(player)
        
        if distance <= self.detection_radius:
            self._interact_with_player(player, distance)
        else:
            if hasattr(self.npc, '_stopped_by_player_interaction'):
                self.npc.is_stopped_by_player = False
                delattr(self.npc, '_stopped_by_player_interaction')
    
    def _in_same_location(self, player, building_manager):
        """Check if player and NPC are in same location - FIXED"""
        if self.npc.building_state.is_inside_building:
            # NPC is inside - check if player is in same building
            if building_manager and building_manager.is_inside_building():
                current_interior = building_manager.get_current_interior()
                return self.npc.building_state.current_building == current_interior
            else:
                return False  # Player outside, NPC inside
        else:
            # NPC is outside - check if player is also outside
            return not (building_manager and building_manager.is_inside_building())
    
    def _interact_with_player(self, player, distance):
        """Handle interaction when player is nearby"""
        self.npc.is_stopped_by_player = True
        self.npc._stopped_by_player_interaction = True  # Mark as player interaction
        self.npc._face_player(player)
        self.npc.state = "idle"
        
        if distance <= self.stop_distance:
            self.show_speech_bubble = True
            self.speech_bubble_timer = self.speech_bubble_duration
            self.bubble_text = self.npc.bubble_dialogue
    
    def update_speech_bubble(self):
        """Update speech bubble timer - FIXED"""
        if self.show_speech_bubble:
            self.speech_bubble_timer -= 1
            if self.speech_bubble_timer <= 0:
                self.show_speech_bubble = False
                # Don't clear bubble_text here - let it persist for drawing
    
    def set_speech_bubble(self, text, duration=None):
        """Manually set speech bubble - for NPC-NPC conversations"""
        self.bubble_text = text
        self.show_speech_bubble = True
        self.speech_bubble_timer = duration if duration else self.speech_bubble_duration
        print(f"DEBUG: Set speech bubble for {self.npc.name}: '{text}' (duration: {self.speech_bubble_timer})")


class NPCAnimation:
    """Handles NPC animation state and rendering"""
    
    def __init__(self, npc, assets):
        self.npc = npc
        self.animations = assets["player"]  # Using player assets for now
        self.state = "idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 8
        self.image = self.animations[self.state][self.frame_index]
    
    def update_animation(self):
        """Update animation frame"""
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.animations[self.npc.state]
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]
            
            # Maintain rect center position
            center = self.npc.rect.center
            self.npc.rect = self.image.get_rect()
            self.npc.rect.center = center


class NPC:
    """Main NPC class with improved organization - FIXED VERSION"""
    
    def __init__(self, x, y, assets, name, hangout_area=None):
        # Basic attributes
        self.x = x
        self.y = y
        self.name = name
        self.speed = app.PLAYER_SPEED * 0.7
        self.facing_left = False
        self.is_stopped_by_player = False
        self.chat_history = []
        
        # Set up dialogue FIRST
        dialogue_data = NPCDialogue.get_dialogue(name)
        self.bubble_dialogue = dialogue_data["bubble"]
        self.dialogue = dialogue_data["personality"]
        
        # Initialize components (order matters!)
        self.animation = NPCAnimation(self, assets)
        self.movement = NPCMovement(self)
        self.building_state = NPCBuildingState()
        self.interaction = NPCInteraction(self)  # This needs bubble_dialogue to be set
        
        # Set up rect
        self.rect = self.animation.image.get_rect(center=(x, y))
        
        # Set up hangout area
        self.hangout_area = hangout_area or {
            'x': x - 100, 'y': y - 100, 'width': 200, 'height': 200
        }
        
        # Properties for backward compatibility
        self.state = self.animation.state
        self.image = self.animation.image
        self.animations = self.animation.animations
        self.show_speech_bubble = self.interaction.show_speech_bubble
        self.is_inside_building = self.building_state.is_inside_building
        self.current_building = self.building_state.current_building
        
        # CRITICAL: Initialize conversation flags
        self._in_npc_conversation = False
        self._conversation_partner = None
        
        print(f"DEBUG: Created NPC {name} at ({x}, {y}) with bubble: '{self.bubble_dialogue}'")
    
    def update(self, player=None, buildings=None, building_manager=None):
        """Main update method - FIXED for proper conversation support"""
        # Update building timers
        self.building_state.update_timers()
        
        # Handle building interactions first
        self._update_building_behavior(building_manager)
        
        # Handle player interaction
        self.interaction.update_player_interaction(player, building_manager)
        self.interaction.update_speech_bubble()
        
        # CRITICAL FIX: Proper movement logic
        # Only move if not stopped by player OR in conversation
        should_move = not self.is_stopped_by_player and not self._in_npc_conversation
        
        if should_move:
            self._update_movement(buildings, building_manager)
        else:
            # If stopped, ensure we're in idle state
            self.state = "idle"
        
        # Update animation
        self.animation.update_animation()
        
        # Sync properties for backward compatibility
        self._sync_properties()
    
    def _update_building_behavior(self, building_manager):
        """Handle building-related behavior - IMPROVED"""
        if self.building_state.is_inside_building and self.building_state.current_building:
            # Inside building behavior
            if self.building_state.building_timer >= self.building_state.stay_duration:
                # Try to exit
                self.building_state.try_exit_building(self, building_manager)
            
            # Handle interior collision if needed
            if building_manager and hasattr(self.building_state.current_building, 'get_interior_walls'):
                collision_objects = self.building_state.current_building.get_interior_walls()
                self._handle_interior_collision(collision_objects)
    
    def _update_movement(self, buildings, building_manager):
        """Handle movement logic - IMPROVED"""
        if self.movement.update_movement_timer():
            if self.building_state.is_inside_building and self.building_state.current_building:
                self._choose_interior_target()
            else:
                self.movement.choose_new_target(buildings)
        
        self.movement.move_towards_target()
        
        # Try to enter building if outside and not in conversation
        if (not self.building_state.is_inside_building and 
            not self._in_npc_conversation and 
            buildings and building_manager):
            self.building_state.try_enter_building(self, buildings, building_manager)
    
    def _choose_interior_target(self):
        """Choose movement target when inside a building"""
        if self.building_state.building_timer >= self.building_state.stay_duration * 0.8:
            # Move toward exit
            if (self.building_state.current_building and 
                hasattr(self.building_state.current_building, 'exit_zone') and 
                self.building_state.current_building.exit_zone):
                exit_center = self.building_state.current_building.exit_zone.center
                self.movement.target_x = exit_center[0] + random.randint(-20, 20)
                self.movement.target_y = exit_center[1] + random.randint(-20, 20)
        else:
            # Random movement within interior
            interior_width, interior_height = getattr(
                self.building_state.current_building, 'interior_size', (800, 600)
            )
            margin = 50
            self.movement.target_x = random.randint(margin, interior_width - margin)
            self.movement.target_y = random.randint(margin, interior_height - margin)
    
    def _handle_interior_collision(self, collision_objects):
        """Handle collision with interior walls"""
        for wall in collision_objects:
            if hasattr(wall, 'check_collision') and wall.check_collision(self.rect):
                if hasattr(wall, 'resolve_collision'):
                    resolved_rect = wall.resolve_collision(self.rect)
                    self.rect = resolved_rect
                
                # Choose new target to avoid getting stuck
                if self.building_state.current_building:
                    interior_width, interior_height = getattr(
                        self.building_state.current_building, 'interior_size', (800, 600)
                    )
                    margin = 50
                    self.movement.target_x = random.randint(margin, interior_width - margin)
                    self.movement.target_y = random.randint(margin, interior_height - margin)
    
    def _sync_properties(self):
        """Sync properties for backward compatibility"""
        self.state = self.animation.state
        self.image = self.animation.image
        self.show_speech_bubble = self.interaction.show_speech_bubble
        self.is_inside_building = self.building_state.is_inside_building
        self.current_building = self.building_state.current_building
    
    # Utility methods
    def _get_distance_to_player(self, player):
        """Calculate distance to player"""
        dx = self.rect.centerx - player.rect.centerx
        dy = self.rect.centery - player.rect.centery
        return math.sqrt(dx * dx + dy * dy)
    
    def _get_distance_to_building(self, building):
        """Calculate distance to building"""
        dx = self.rect.centerx - building.rect.centerx
        dy = self.rect.centery - building.rect.centery
        return math.sqrt(dx * dx + dy * dy)
    
    def _get_distance_to_npc(self, other_npc):
        """Calculate distance to another NPC"""
        dx = self.rect.centerx - other_npc.rect.centerx
        dy = self.rect.centery - other_npc.rect.centery
        return math.sqrt(dx * dx + dy * dy)
    
    def _face_player(self, player):
        """Make NPC face the player"""
        self.facing_left = player.rect.centerx < self.rect.centerx
    
    def _face_npc(self, other_npc):
        """Make NPC face another NPC"""
        self.facing_left = other_npc.rect.centerx < self.rect.centerx
    
    def sync_position(self):
        """Synchronize x,y with rect position"""
        self.x = self.rect.centerx
        self.y = self.rect.centery
    
    def get_current_location_info(self):
        """Get information about NPC's current location"""
        if self.building_state.is_inside_building and self.building_state.current_building:
            building_type = getattr(self.building_state.current_building, 'building_type', 'unknown building')
            return f"{self.name} is inside {building_type}"
        else:
            return f"{self.name} is outside at ({self.rect.centerx}, {self.rect.centery})"
    
    # Conversation support methods
    def start_conversation_with(self, other_npc, topic="general chat"):
        """Start a conversation with another NPC"""
        print(f"DEBUG: {self.name} starting conversation with {other_npc.name} about {topic}")
        
        # Set conversation flags for both NPCs
        self._in_npc_conversation = True
        self._conversation_partner = other_npc
        other_npc._in_npc_conversation = True
        other_npc._conversation_partner = self
        
        # Stop both NPCs
        self.is_stopped_by_player = True
        other_npc.is_stopped_by_player = True
        
        # Make them face each other
        self._face_npc(other_npc)
        other_npc._face_npc(self)
        
        # Set to idle state
        self.state = "idle"
        other_npc.state = "idle"
    
    def end_conversation(self):
        """End current conversation"""
        if self._conversation_partner:
            print(f"DEBUG: {self.name} ending conversation with {self._conversation_partner.name}")
            
            # Clear conversation flags
            partner = self._conversation_partner
            self._in_npc_conversation = False
            self._conversation_partner = None
            partner._in_npc_conversation = False
            partner._conversation_partner = None
            
            # Allow movement again
            self.is_stopped_by_player = False
            partner.is_stopped_by_player = False
            
            # Clear speech bubbles
            self.interaction.show_speech_bubble = False
            partner.interaction.show_speech_bubble = False
            self.interaction.bubble_text = self.bubble_dialogue  # Reset to default
            partner.interaction.bubble_text = partner.bubble_dialogue  # Reset to default
    
    def is_available_for_conversation(self):
        """Check if NPC is available for starting a conversation"""
        return (not self._in_npc_conversation and 
                not self.is_stopped_by_player and 
                not self.building_state.is_inside_building)