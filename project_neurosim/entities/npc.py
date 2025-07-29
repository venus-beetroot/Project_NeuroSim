import pygame
import random
import math
from functions.assets import app
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
    """Manages NPC building interaction state"""
    
    def __init__(self):
        self.is_inside_building = False
        self.current_building = None
        self.exterior_position = None
        self.building_timer = 0
        self.stay_duration = random.randint(300, 900)
        self.interaction_cooldown = 0
        self.interaction_delay = 300
    
    def try_enter_building(self, npc, buildings, building_manager):
        """Attempt to enter a nearby building"""
        if self.is_inside_building or self.interaction_cooldown > 0:
            return False
        
        for building in buildings:
            if self._can_enter_building(npc, building):
                self._enter_building(npc, building)
                return True
        return False
    
    def _can_enter_building(self, npc, building):
        """Check if NPC can enter a specific building"""
        return (building.can_enter and 
                building.check_interaction_range(npc.rect) and
                hasattr(building, 'can_npc_enter') and 
                building.can_npc_enter())
    
    def _enter_building(self, npc, building):
        """Handle entering a building"""
        # Save exterior position
        self.exterior_position = {'x': npc.rect.centerx, 'y': npc.rect.centery}
        
        # Add NPC to building
        if hasattr(building, 'add_npc'):
            building.add_npc(npc)
        
        # Position NPC in building
        self._position_npc_in_building(npc, building)
        
        # Update state
        self.is_inside_building = True
        self.current_building = building
        self.building_timer = 0
        self.stay_duration = random.randint(300, 900)
        
        print(f"{npc.name} entered {building.building_type}")
    
    def _position_npc_in_building(self, npc, building):
        """Position NPC inside the building"""
        if hasattr(building, 'exit_zone') and building.exit_zone:
            npc.rect.centerx = building.exit_zone.centerx + random.randint(-30, 30)
            npc.rect.centery = building.exit_zone.centery + random.randint(-30, 30)
        else:
            interior_width, interior_height = getattr(building, 'interior_size', (800, 600))
            npc.rect.centerx = interior_width // 2
            npc.rect.centery = interior_height // 2
    
    def try_exit_building(self, npc):
        """Attempt to exit current building"""
        if not self.is_inside_building or not self.current_building:
            return False
        
        if self.current_building.check_exit_range(npc.rect):
            self._exit_building(npc)
            return True
        else:
            self._move_toward_exit(npc)
            return False
    
    def _exit_building(self, npc):
        """Handle exiting a building"""
        building_ref = self.current_building
        
        # Restore exterior position
        if self.exterior_position:
            npc.rect.centerx = self.exterior_position['x']
            npc.rect.centery = self.exterior_position['y']
        
        # Remove from building
        if hasattr(building_ref, 'remove_npc'):
            building_ref.remove_npc(npc)
        
        # Reset state
        self.is_inside_building = False
        self.current_building = None
        self.exterior_position = None
        self.interaction_cooldown = self.interaction_delay
        
        print(f"{npc.name} exited building")
    
    def _move_toward_exit(self, npc):
        """Move NPC toward building exit"""
        if self.current_building and hasattr(self.current_building, 'exit_zone'):
            exit_center = self.current_building.exit_zone.center
            npc.movement.target_x = exit_center[0]
            npc.movement.target_y = exit_center[1]
    
    def update_timers(self):
        """Update building-related timers"""
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1
        if self.is_inside_building:
            self.building_timer += 1


class NPCInteraction:
    """Handles NPC player interaction and speech bubbles"""
    
    def __init__(self, npc):
        self.npc = npc
        self.show_speech_bubble = False
        self.speech_bubble_timer = 0
        self.speech_bubble_duration = 180
        self.detection_radius = 80
        self.stop_distance = 50
    
    def update_player_interaction(self, player, building_manager):
        """Update interaction with player"""
        if not player or not self._in_same_location(player, building_manager):
            self.npc.is_stopped_by_player = False
            return
        
        distance = self.npc._get_distance_to_player(player)
        
        if distance <= self.detection_radius:
            self._interact_with_player(player, distance)
        else:
            self.npc.is_stopped_by_player = False
    
    def _in_same_location(self, player, building_manager):
        """Check if player and NPC are in same location"""
        if self.npc.building_state.is_inside_building and building_manager and building_manager.is_inside_building():
            return self.npc.building_state.current_building == building_manager.get_current_interior()
        elif not self.npc.building_state.is_inside_building and not (building_manager and building_manager.is_inside_building()):
            return True
        return False
    
    def _interact_with_player(self, player, distance):
        """Handle interaction when player is nearby"""
        self.npc.is_stopped_by_player = True
        self.npc._face_player(player)
        self.npc.state = "idle"
        
        if distance <= self.stop_distance:
            self.show_speech_bubble = True
            self.speech_bubble_timer = self.speech_bubble_duration
    
    def update_speech_bubble(self):
        """Update speech bubble timer"""
        if self.show_speech_bubble:
            self.speech_bubble_timer -= 1
            if self.speech_bubble_timer <= 0:
                self.show_speech_bubble = False
    
    def draw_speech_bubble(self, surface, font):
        """Draw speech bubble above NPC"""
        if not self.show_speech_bubble or not font:
            return
        
        text_surface = font.render(self.npc.bubble_dialogue, True, (0, 0, 0))
        text_rect = text_surface.get_rect()
        
        # Calculate bubble dimensions and position
        bubble_width = text_rect.width + 20
        bubble_height = text_rect.height + 16
        bubble_x = self.npc.rect.centerx - bubble_width // 2
        bubble_y = self.npc.rect.top - bubble_height - 10
        
        # Draw bubble
        self._draw_bubble_background(surface, bubble_x, bubble_y, bubble_width, bubble_height)
        self._draw_bubble_tail(surface, bubble_y + bubble_height)
        
        # Draw text
        surface.blit(text_surface, (bubble_x + 10, bubble_y + 8))
    
    def _draw_bubble_background(self, surface, x, y, width, height):
        """Draw speech bubble background"""
        bubble_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (255, 255, 255), bubble_rect)
        pygame.draw.rect(surface, (0, 0, 0), bubble_rect, 2)
    
    def _draw_bubble_tail(self, surface, tail_y):
        """Draw speech bubble tail"""
        tail_points = [
            (self.npc.rect.centerx - 10, tail_y),
            (self.npc.rect.centerx + 10, tail_y),
            (self.npc.rect.centerx, tail_y + 10)
        ]
        pygame.draw.polygon(surface, (255, 255, 255), tail_points)
        pygame.draw.polygon(surface, (0, 0, 0), tail_points, 2)


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
    """Main NPC class with improved organization"""
    
    def __init__(self, x, y, assets, name, hangout_area=None):
        # Basic attributes
        self.x = x
        self.y = y
        self.name = name
        self.speed = app.PLAYER_SPEED * 0.7
        self.facing_left = False
        self.is_stopped_by_player = False
        self.chat_history = []
        
        # Initialize components
        self.animation = NPCAnimation(self, assets)
        self.movement = NPCMovement(self)
        self.building_state = NPCBuildingState()
        self.interaction = NPCInteraction(self)
        
        # Set up rect
        self.rect = self.animation.image.get_rect(center=(x, y))
        
        # Set up dialogue
        dialogue_data = NPCDialogue.get_dialogue(name)
        self.bubble_dialogue = dialogue_data["bubble"]
        self.dialogue = dialogue_data["personality"]
        
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
    
    def update(self, player=None, buildings=None, building_manager=None):
        """Main update method"""
        # Update building timers
        self.building_state.update_timers()
        
        # Handle building interactions
        if self.building_state.is_inside_building and self.building_state.current_building:
            self._update_interior_behavior(building_manager)
        
        # Handle player interaction
        self.interaction.update_player_interaction(player, building_manager)
        self.interaction.update_speech_bubble()
        
        # Handle movement
        if not self.is_stopped_by_player:
            self._update_movement(buildings, building_manager)
        
        # Update animation
        self.animation.update_animation()
        
        # Sync properties for backward compatibility
        self._sync_properties()
    
    def _update_interior_behavior(self, building_manager):
        """Handle behavior when inside a building"""
        if self.building_state.building_timer >= self.building_state.stay_duration:
            self.building_state.try_exit_building(self)
        
        if building_manager and self.building_state.is_inside_building and self.building_state.current_building:
            collision_objects = self.building_state.current_building.get_interior_walls()
            self._handle_interior_collision(collision_objects)
    
    def _update_movement(self, buildings, building_manager):
        """Handle movement logic"""
        if self.movement.update_movement_timer():
            if self.building_state.is_inside_building and self.building_state.current_building:
                self._choose_interior_target()
            else:
                self.movement.choose_new_target(buildings)
        
        self.movement.move_towards_target()
        
        # Try to enter building if outside
        if not self.building_state.is_inside_building and buildings and building_manager:
            self.building_state.try_enter_building(self, buildings, building_manager)
    
    def _choose_interior_target(self):
        """Choose movement target when inside a building"""
        if self.building_state.building_timer >= self.building_state.stay_duration * 0.8:
            # Move toward exit
            exit_center = self.building_state.current_building.exit_zone.center
            self.movement.target_x = exit_center[0] + random.randint(-20, 20)
            self.movement.target_y = exit_center[1] + random.randint(-20, 20)
        else:
            # Random movement within interior
            interior_width, interior_height = self.building_state.current_building.interior_size
            margin = 50
            self.movement.target_x = random.randint(margin, interior_width - margin)
            self.movement.target_y = random.randint(margin, interior_height - margin)
    
    def _handle_interior_collision(self, collision_objects):
        """Handle collision with interior walls"""
        for wall in collision_objects:
            if wall.check_collision(self.rect):
                resolved_rect = wall.resolve_collision(self.rect)
                self.rect = resolved_rect
                
                # Choose new target to avoid getting stuck
                if self.building_state.current_building:
                    interior_width, interior_height = self.building_state.current_building.interior_size
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
    
    def _face_player(self, player):
        """Make NPC face the player"""
        self.facing_left = player.rect.centerx < self.rect.centerx
    
    def sync_position(self):
        """Synchronize x,y with rect position"""
        self.x = self.rect.centerx
        self.y = self.rect.centery
    
    def get_current_location_info(self):
        """Get information about NPC's current location"""
        if self.building_state.is_inside_building and self.building_state.current_building:
            return f"{self.name} is inside {self.building_state.current_building.building_type}"
        else:
            return f"{self.name} is outside at ({self.rect.centerx}, {self.rect.centery})"
    
    def draw(self, surface, font=None):
        """Draw NPC on screen"""
        # Draw sprite
        if self.facing_left:
            flipped_image = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_image, self.rect)
        else:
            surface.blit(self.image, self.rect)
        
        # Draw speech bubble
        self.interaction.draw_speech_bubble(surface, font)