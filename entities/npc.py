import pygame
import random
import math
from functions import app, ai
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
        },
        "Gordon": {
            "bubble": "Greetings, I'm Gordon. I like video games and I can play with you anytime!",
            "personality": "You are Gordon, 16, is a perpetually tired, hoodie-wearing gamer who lives for all-night sessions and terrible energy drinks. Not the sharpest tool in the shed, he masks his cluelessness with an over-the-top “mysterious” persona, speaking in vague, dramatic phrases and acting like he’s hiding world-shattering secrets when he’s really just scrolling memes."
        },
        "Timmy": {
            "bubble": "Yo, I'm Timmy. Got a Coke, a Tim Tam, and a cat video? I'm in.",
            "personality": "You are Timmy, a slightly eccentric NPC who juggles being a professional robotics team captain and a solid student with an odd mix of habits: an obsession with cats, a sweet tooth for Tim Tams, and a love of Coke. You wear knock-off brands without shame, gamble for fun, and spend way too much time scrolling reels. You know your coding, but sometimes your questionable hygiene distracts from your skills."
        },
        "Foxy": {
            "bubble": "Heyo, I'm Foxy! Let's debug life together, fam!",
            "personality": "You are Foxy, a computer science teacher in your late 30s who radiates peak cringe millennial energy. You pepper your speech with outdated slang like 'lit' and 'epic win,' unironically reference memes from 2010, and think dabbing is still funny. Despite the awkward delivery, you’re passionate about coding and teaching, always trying (and failing) to relate to your students through pop culture. You wear graphic tees with ironic slogans and carry a reusable coffee cup plastered with stickers from long-dead tech conferences."
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
        self.movement_delay = random.randint(120, 300)  # Longer initial delay
        self.has_reached_target = False

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
                random.random() < 0.4)

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
        """Choose a random target with better exploration"""
        exploration_chance = random.random()

        if exploration_chance < 0.15:  # 15% stay in hangout (reduced)
            hangout = self.npc.hangout_area
            self.target_x = random.randint(hangout['x'], hangout['x'] + hangout['width'])
            self.target_y = random.randint(hangout['y'], hangout['y'] + hangout['height'])
        elif exploration_chance < 0.45:  # 30% explore nearby areas (extended range)
            self.target_x = self.npc.rect.centerx + random.randint(-800, 800)  # Doubled range
            self.target_y = self.npc.rect.centery + random.randint(-800, 800)  # Doubled range
        else:  # 55% explore far areas (increased percentage and range)
            # Pick completely random map locations with larger range
            self.target_x = random.randint(200, 2000)   # Expanded map range
            self.target_y = random.randint(200, 2000)   # Expanded map range

    def move_towards_target(self):
        """Move NPC towards target position"""
        dx = self.target_x - self.npc.rect.centerx
        dy = self.target_y - self.npc.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)

        if distance > 15:  # Must get close to target
            # Calculate movement vector
            move_x = (dx / distance) * self.npc.speed * 0.5
            move_y = (dy / distance) * self.npc.speed * 0.5

            # Update position
            self.npc.rect.centerx += move_x
            self.npc.rect.centery += move_y
            
            if abs(move_x) > 0.1:
                # Face left if moving left (negative x), face right if moving right (positive x)
                self.npc.facing_left = move_x < 0

            # Set animation state
            self.npc.state = "run" if "run" in self.npc.animations else "idle"
        else:
            self.npc.state = "idle"
            # Mark that we've reached the target
            self.has_reached_target = True

    def update_movement_timer(self):
        """Update movement timing"""
        self.movement_timer += 1

        # Check if we should pick a new target
        should_pick_new = False

        if self.movement_timer >= self.movement_delay:
            should_pick_new = True
        elif hasattr(self, 'has_reached_target') and self.has_reached_target:
            # If we reached the target, wait a bit then pick a new one
            if self.movement_timer >= 30:  # Wait 30 frames after reaching target
                should_pick_new = True

        if should_pick_new:
            self.movement_timer = 0
            self.movement_delay = random.randint(120, 300)  # Longer delays between targets
            if hasattr(self, 'has_reached_target'):
                self.has_reached_target = False
            return True

        return False
    
    def _follow_player(self, player):
        """Follow player across positions. If in different scene/building, attempt to exit building first."""
        # If NPC is inside a building and player is outside, head to exit
        if self.npc.building_state.is_inside_building and self.npc.building_state.current_building:
            # Check if player is outside building or in different building
            player_inside = getattr(player, "is_inside_building", False) if hasattr(player, "is_inside_building") else False
            if not player_inside:
                # Player is outside, NPC should exit building
                self.npc.building_state._move_toward_exit(self.npc)
                return
            # Check if player is in same building
            elif hasattr(player, "current_building") and player.current_building != self.npc.building_state.current_building:
                # Player is in different building, exit current one
                self.npc.building_state._move_toward_exit(self.npc)
                return

        # Check if NPC is outside but player is inside a building
        elif not self.npc.building_state.is_inside_building and hasattr(player, "is_inside_building") and player.is_inside_building:
            # Try to enter the same building as player
            if hasattr(player, "current_building") and player.current_building:
                # Move toward player's building entrance
                building = player.current_building
                if hasattr(building, "exit_zone") and building.exit_zone:
                    self.npc.movement.target_x = building.exit_zone.centerx
                    self.npc.movement.target_y = building.exit_zone.centery
                else:
                    self.npc.movement.target_x = building.rect.centerx
                    self.npc.movement.target_y = building.rect.centery
                return

        # Rest of the method stays the same...


class NPCBuildingState:
    """Manages NPC building interaction state"""

    def __init__(self):
        self.is_inside_building = False
        self.current_building = None
        self.exterior_position = None
        self.building_timer = 0
        self.stay_duration = random.randint(30, 90)
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
        interior_width, interior_height = getattr(building, 'interior_size', (800, 600))
        
        # Position them away from walls, entrance, and furniture
        margin = 100  # Increased margin from walls
        safe_x = random.randint(margin, interior_width - margin)
        safe_y = random.randint(margin, interior_height - margin - 100)  # Extra space from bottom (exit area)
        
        # If there's an exit zone, make sure we're not too close to it
        if hasattr(building, 'exit_zone') and building.exit_zone:
            exit_center_x = building.exit_zone.centerx
            exit_center_y = building.exit_zone.centery
            
            # Keep much further from exit zone
            while abs(safe_x - exit_center_x) < 150 and abs(safe_y - exit_center_y) < 150:
                safe_x = random.randint(margin, interior_width - margin)
                safe_y = random.randint(margin, interior_height - margin - 100)
        
        # Check for furniture collisions and avoid them
        if hasattr(building, 'get_furniture'):
            furniture_list = building.get_furniture()
            attempts = 0
            while attempts < 20:  # Try up to 20 times to find safe spot
                collision_with_furniture = False
                test_rect = pygame.Rect(safe_x - 16, safe_y - 16, 32, 32)  # NPC size
                
                for furniture in furniture_list:
                    # Check against furniture hitbox with extra padding
                    furniture_rect = furniture.hitbox.copy()
                    furniture_rect.inflate_ip(40, 40)  # Add 40 pixels padding around furniture
                    if test_rect.colliderect(furniture_rect):
                        collision_with_furniture = True
                        break
                
                if not collision_with_furniture:
                    break
                
                # Try new position
                safe_x = random.randint(margin, interior_width - margin)
                safe_y = random.randint(margin, interior_height - margin - 100)
                attempts += 1
        
        npc.rect.centerx = safe_x
        npc.rect.centery = safe_y

    def update_animation(self):
        """Update animation with transform-based effects"""
        self.animation_timer += 1
        
        # Get base image
        if self.npc.state in self.animations and len(self.animations[self.npc.state]) > 0:
            base_image = self.animations[self.npc.state][0]
        else:
            # Fallback if state doesn't exist
            base_image = list(self.animations.values())[0][0]
        
        if self.npc.state == "idle":
            # Gentle bobbing animation for idle
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.frame_index = (self.frame_index + 1) % 120  # 2-second cycle
            
            # Create subtle vertical bobbing
            bob_offset = int(2 * math.sin(self.frame_index * 0.1))
            
            # Use the base image
            self.image = base_image
            
            # Store the bobbing offset to be applied in drawing
            self.bob_offset = bob_offset
            
        elif self.npc.state == "run":
            # Faster animation cycle for running
            if self.animation_timer >= self.animation_speed // 2:
                self.animation_timer = 0
                self.frame_index = (self.frame_index + 1) % 60
            
            # Create slight scaling effect
            scale_factor = 1.0 + 0.05 * math.sin(self.frame_index * 0.3)
            
            # Scale the image slightly
            width = int(base_image.get_width() * scale_factor)
            height = int(base_image.get_height() * scale_factor)
            self.image = pygame.transform.scale(base_image, (width, height))
            self.bob_offset = 0  # No bobbing when running
            
        else:
            self.image = base_image
            self.bob_offset = 0
        
        # Update rect size but maintain center position
        old_center = self.npc.rect.center
        self.npc.rect = self.image.get_rect()
        self.npc.rect.center = (old_center[0], old_center[1] + getattr(self, 'bob_offset', 0))

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

    def try_exit_building(self, npc):
        """Attempt to exit current building"""
        if not self.is_inside_building or not self.current_building:
            return False
        
        # Check if this NPC is a permanent resident (like Lisa)
        if getattr(self, '_is_permanent_resident', False):
            return False  # Permanent residents don't leave
        
        # Safety check for exit_zone
        if hasattr(self.current_building, 'check_exit_range') and self.current_building.check_exit_range(npc.rect):
            self._exit_building(npc)
            return True
        else:
            self._move_toward_exit(npc)
            return False

    def _move_toward_exit(self, npc):
        """Handle moving toward building exit"""
        if self.current_building and hasattr(self.current_building, 'exit_zone') and self.current_building.exit_zone:
            exit_center = self.current_building.exit_zone.center
            npc.movement.target_x = exit_center[0]
            npc.movement.target_y = exit_center[1]
            print(f"{npc.name} is moving toward exit at {exit_center}")
        else:
            # Fallback if no exit zone - just stay put or move to center
            print(f"Warning: {npc.name} couldn't find exit zone, staying in place")
            npc.movement.target_x = npc.rect.centerx
            npc.movement.target_y = npc.rect.centery

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
            self._resume_movement()  # ADD THIS LINE
            return

        distance = self.npc._get_distance_to_player(player)

        if distance <= self.detection_radius:
            self._interact_with_player(player, distance)
        else:
            self.npc.is_stopped_by_player = False
            self._resume_movement()  # ADD THIS LINE

    def _resume_movement(self):
        """Resume NPC movement after player interaction ends"""
        if not self.npc.is_stopped_by_player:
            # Only pick new target if they were actually stopped
            if hasattr(self, '_was_stopped') and self._was_stopped:
                self.npc.movement.movement_timer = self.npc.movement.movement_delay - 10  # Pick new target soon, but not immediately
                self._was_stopped = False
                # Reset facing direction to prevent movement/sprite mismatch
                self.npc._last_player_facing = None
            # Hide speech bubble
            self.show_speech_bubble = False
            self.speech_bubble_timer = 0

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
        self._was_stopped = True  # Track that they were stopped

        # Override movement target to current position to make them truly stop
        self.npc.movement.target_x = self.npc.rect.centerx
        self.npc.movement.target_y = self.npc.rect.centery

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
    """Handles NPC animation state and rendering - FIXED VERSION"""

    def __init__(self, npc, assets):
        self.npc = npc
        
        # Tom always uses player assets and animations
        if npc.name.lower() == "tom":
            self.animations = assets["player"]
            self.is_using_player_assets = True
            print(f"✓ Tom using player assets and animations")
        else:
            # Try to load NPC-specific assets for Gordon, Timmy, and others
            npc_key = f"npc_{npc.name.lower()}"
            print(f"DEBUG: Looking for key '{npc_key}' in assets. Available keys: {list(assets.keys())}")
            if npc_key in assets:
                self.animations = assets[npc_key]
                self.is_using_player_assets = False
                print(f"✓ Using custom assets for {npc.name}")
            else:
                self.animations = assets["player"]  # Fallback to player assets
                self.is_using_player_assets = True
                print(f"⚠ Using fallback player assets for {npc.name}")
        
        
        self.state = "idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 8
        self.current_direction = "down"
        self.has_directional_sprites = npc.name.lower() in ["gordon", "timmy", "foxy"]
        
        
        # Initialize with first frame
        if self.state in self.animations and len(self.animations[self.state]) > 0:
            self.image = self.animations[self.state][0]
        else:
            # Fallback to first available animation
            first_anim_key = list(self.animations.keys())[0]
            self.image = self.animations[first_anim_key][0]

    def update_animation(self):
        """Update animation frame with 4-directional support"""
        self.animation_timer += 1
        
        # Determine current state for 4-directional NPCs
        current_state = self.npc.state
        if self.has_directional_sprites:
            if current_state == "run":
                current_state = f"walk_{self.current_direction}"
            elif current_state == "idle":
                # Use directional idle if available, fallback to generic idle
                directional_idle = f"idle_{self.current_direction}"
                if directional_idle in self.animations:
                    current_state = directional_idle
        
        # Get current animation frames
        if current_state in self.animations:
            frames = self.animations[current_state]
        elif self.npc.state in self.animations:
            frames = self.animations[self.npc.state]
        else:
            # Fallback to idle or first available animation
            if "idle" in self.animations:
                frames = self.animations["idle"]
            else:
                frames = list(self.animations.values())[0]
        
        # Update frame when timer reaches speed threshold
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            
            # Only advance frame if we have multiple frames
            if len(frames) > 1:
                self.frame_index = (self.frame_index + 1) % len(frames)
            else:
                self.frame_index = 0
            
            # Update the image
            self.image = frames[self.frame_index]

            # Maintain rect center position
            center = self.npc.rect.center
            self.npc.rect = self.image.get_rect()
            self.npc.rect.center = center

    def get_facing_corrected_image(self):
        """
        Get the image with correct facing direction applied.
        """
        # If the NPC has 4-directional sprites, return the base image as-is
        if self.has_directional_sprites:
            return self.image
        
        # For all NPCs using 2-directional sprites (including Tom with player assets)
        if self.npc.facing_left:
            return pygame.transform.flip(self.image, True, False)
                
        return self.image


class NPCBehavior:
    """Unified behavior: tiredness, following, furniture use"""

    def __init__(self, npc):
        self.npc = npc

        # Following
        self.is_following_player = False
        self.follow_target = None
        self.follow_distance = 50

        # Sitting / furniture
        self.is_sitting = False
        self.current_chair = None
        self.sitting_timer = 0

        # Use npc.can_move (owned by NPC) — behavior will set npc.can_move False/True
        # Tiredness
        self.tiredness = 20.0
        self.tiredness_decay_rate = 0.01
        self.tiredness_recovery_rate = 0.2
        self.exhaustion_threshold = 70.0

        # furniture internals
        self.current_furniture = None
        self.using_furniture = False
        self.furniture_timer = 0
        self.furniture_use_duration = random.randint(180, 600)
        self.furniture_cooldown = 0
        self.furniture_search_radius = 80
        self.can_move = True
        # state
        self.behavior_state = "free_roam"  # free_roam, following, seeking_rest, sitting
        self.resting_timer = 0

    # core update
    def update(self, player=None, building_manager=None):
        # update tiredness & state
        self._update_tiredness()
        self._update_behavior_state()

        # update furniture timers/cooldowns
        if self.furniture_cooldown > 0:
            self.furniture_cooldown -= 1

        if self.using_furniture and self.current_furniture:
            self.furniture_timer += 0.5
            if self.furniture_timer >= self.furniture_use_duration:
                self._stop_using_furniture()

    def _update_tiredness(self):
        if self.is_sitting or self.using_furniture:
            self.tiredness = max(0.0, self.tiredness - self.tiredness_recovery_rate)
        else:
            self.tiredness = min(100.0, self.tiredness + self.tiredness_decay_rate)
            #print(f"[NPC] {self.npc.name} tiredness: {self.tiredness:.2f}")

    def _update_behavior_state(self):
        if self.is_following_player and self.follow_target:
            self.behavior_state = "following"
        elif self.tiredness >= self.exhaustion_threshold:
            self.behavior_state = "seeking_rest"
            # hint visual
            try:
                self.npc.state = "tired"
            except Exception:
                pass
        elif self.is_sitting or self.using_furniture:
            self.behavior_state = "sitting"
        else:
            self.behavior_state = "free_roam"

    def get_behavior_info(self):
        return {
            "behavior_state": self.behavior_state,
            "is_following_player": self.is_following_player,
            "is_sitting": self.is_sitting,
            "current_chair": self.current_chair is not None
        }

    def get_tiredness_message(self):
        if self.using_furniture:
            return "I'm taking a break."
        if self.tiredness >= self.exhaustion_threshold:
            return "I need to rest."
        return ""

    def start_following(self, player):
        """Follow player and cancel sitting if needed."""
        if not player:
            print(f"[NPC] start_following failed: no player provided for {self.npc.name}")
            return
        
        if not isinstance(player, Player):
            print(f"[NPC] start_following failed: target is not a Player instance for {self.npc.name}")
            return

        self.is_following_player = True
        self.follow_target = player

        if self.is_sitting:
            self._leave_chair()

        self.npc.can_move = True

    def stop_following(self):
        self.is_following_player = False
        self.follow_target = None

    # Sitting / furniture usage
    def should_seek_furniture(self):
        return (self.tiredness >= self.exhaustion_threshold and
                not self.using_furniture and
                self.furniture_cooldown <= 0)

    def find_nearest_furniture(self, furniture_list):
        if not furniture_list:
            return None
        best = None
        best_dist = float('inf')
        for f in furniture_list:
            if getattr(f, "is_occupied", False):
                continue
            dx = self.npc.rect.centerx - f.rect.centerx
            dy = self.npc.rect.centery - f.rect.centery
            d = math.hypot(dx, dy)
            if d < self.furniture_search_radius and d < best_dist:
                best = f
                best_dist = d
        return best

    def try_use_furniture(self, furniture_list):
        if not self.should_seek_furniture():
            return False
        target = self.find_nearest_furniture(furniture_list)
        if not target:
            return False
        
        # Check if close enough to interact
        dx = self.npc.rect.centerx - target.rect.centerx
        dy = self.npc.rect.centery - target.rect.centery
        distance = math.hypot(dx, dy)
        
        print(f"{self.npc.name} distance to {target.furniture_type}: {distance:.1f}")
        
        if distance < 60:  # Increased interaction range
            success = self._start_using_furniture(target)
            if success:
                print(f"{self.npc.name} successfully started using {target.furniture_type}")
            return success
        else:
            # Move toward it - position slightly in front of the furniture
            offset_x = 0
            offset_y = 20  # Sit slightly in front
            self.npc.movement.target_x = target.rect.centerx + offset_x
            self.npc.movement.target_y = target.rect.centery + offset_y
            print(f"{self.npc.name} moving toward {target.furniture_type} at ({target.rect.centerx}, {target.rect.centery})")
            return False

    def _start_using_furniture(self, furniture):
        if getattr(furniture, "furniture_type", "") == "chair":
            return self._sit_on_chair(furniture)
        elif getattr(furniture, "furniture_type", "") == "table":
            return self._use_table(furniture)
        return False

    def _use_table(self, table):
        if getattr(table, "is_occupied", False):
            return False
        try:
            table.is_occupied = True
        except Exception:
            pass
        self.current_furniture = table
        self.using_furniture = True
        self.furniture_timer = 0
        self.furniture_use_duration = random.randint(300, 900)
        self.npc.can_move = False
        self.npc.state = "idle"
        return True

    def _sit_on_chair(self, chair):
        if getattr(chair, "is_occupied", False):
            print(f"{self.npc.name} can't sit - chair is occupied")
            return False
        
        print(f"{self.npc.name} is sitting on {chair.furniture_type} at ({chair.x}, {chair.y})")

    def _sit_on_chair(self, chair):
        if getattr(chair, "is_occupied", False):
            return False
        print(f"{self.npc.name} is trying to sit on {chair.furniture_type}")
        # Position NPC similar to player system
        self.npc.x = chair.x + chair.rect.width // 2
        self.npc.y = chair.y - 20 + chair.rect.height // 2
        self.npc.rect.centerx = self.npc.x
        self.npc.rect.centery = self.npc.y
        self.npc.can_move = False
        chair.is_occupied = True
            
        # Set NPC sitting state similar to player
        self.using_furniture = True
        self.current_furniture = chair
        self.current_chair = chair
        self.is_sitting = True
        self.npc.is_sitting = True  # Add player-like flag
        self.furniture_timer = 0
        self.furniture_use_duration = random.randint(700, 1400)

        
        # freeze movement but allow chat/interaction
        self.npc.can_move = False
        self.npc.state = "idle"
        print(f"{self.npc.name} sat on {chair.furniture_type}")
        return True

    def _leave_chair(self):
        if self.current_chair:
            try:
                self.current_chair.is_occupied = False
            except Exception:
                pass
            
            # Move NPC away from chair similar to player system
            self.npc.x = self.current_chair.x + self.current_chair.rect.width + 20
            # Check if NPC would collide and adjust position
            if self.npc.rect.colliderect(self.current_chair.rect):
                self.npc.x = self.current_chair.x + self.current_chair.rect.width - 60
            
            self.npc.y = self.current_chair.y + self.current_chair.rect.height // 2
            self.npc.rect.centerx = self.npc.x
            self.npc.rect.centery = self.npc.y
            
        self.current_chair = None
        self.is_sitting = False
        self.npc.is_sitting = False  # Clear player-like flag
        self.using_furniture = False
        self.npc.can_move = True
        print(f"{self.npc.name} stood up from chair")


    def _stop_using_furniture(self):
        if self.current_furniture:
            if getattr(self.current_furniture, "furniture_type", "") == "chair":
                try:
                    self.current_furniture.is_occupied = False
                except Exception:
                    pass
                # Use proper chair exit positioning similar to player system
                self.npc.x = self.current_furniture.x + self.current_furniture.rect.width + 20
                if self.npc.rect.colliderect(self.current_furniture.rect):
                    self.npc.x = self.current_furniture.x + self.current_furniture.rect.width - 60
                
                self.npc.y = self.current_furniture.y + self.current_furniture.rect.height // 2
                self.npc.rect.centerx = self.npc.x
                self.npc.rect.centery = self.npc.y
                print(f"{self.npc.name} finished using chair")
            else:
                try:
                    self.current_furniture.is_occupied = False
                except Exception:
                    pass
            self.npc.can_move = True

        self.using_furniture = False
        self.current_furniture = None
        self.furniture_timer = 0
        self.furniture_cooldown = 180
        self.npc.is_stopped_by_player = False
        self.is_sitting = False
        self.npc.is_sitting = False  # Clear player-like flag
        self.current_chair = None

    def force_stop_furniture_use(self):
        if self.using_furniture:
            self._stop_using_furniture()

class NPC:
    """Main NPC class with improved organization"""

    def __init__(self, x, y, assets, name, hangout_area=None):
        # Basic attributes
        self.x = x
        self.y = y
        self.name = name
        self.speed = app.PLAYER_SPEED * 0.7
        self.facing_left = True
        self.is_stopped_by_player = False
        self.chat_history = []
        self.is_stationary = False  # Add this line

        # Initialize components
        self.animation = NPCAnimation(self, assets)
        self.movement = NPCMovement(self)
        self.building_state = NPCBuildingState()
        self.interaction = NPCInteraction(self)
        self.behavior = NPCBehavior(self)

        # Set up rect
        self.rect = self.animation.image.get_rect(center=(x, y))

        # Set up dialogue
        dialogue_data = NPCDialogue.get_dialogue(name)
        self.bubble_dialogue = dialogue_data["bubble"]
        self.dialogue = dialogue_data["personality"]
        self.stats = dialogue_data.get("stats", "")
        self.obedience = dialogue_data.get("obedience", 2)

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
        self.is_sitting = False

    def update(self, player=None, buildings=None, building_manager=None, furniture_list=None):
        """Main update method"""
        # Update building timers
        self.building_state.update_timers()

        # Update behavior (tiredness, following, etc.)
        self.behavior.update(player, building_manager)

        # Force higher tiredness for testing - REMOVE THIS LATER
        if random.random() < 0.001:  # Small chance each frame
            self.behavior.tiredness = 80.0
            print(f"{self.name} is now tired: {self.behavior.tiredness}")

        # If tired: try to seek rest
        if self.behavior.tiredness >= self.behavior.exhaustion_threshold:
            self._seek_rest(building_manager, furniture_list)

        # ALWAYS try furniture interaction if inside building (not just when tired)
        if self.building_state.is_inside_building and furniture_list:
            if not self.behavior.using_furniture and random.random() < 0.02:  # 2% chance per frame
                self.behavior.try_use_furniture(furniture_list)

        # Handle player interaction
        self.interaction.update_player_interaction(player, building_manager)
        self.interaction.update_speech_bubble()

        # Handle movement and collisions - but skip if stationary or can't move
        if not self.is_stopped_by_player and not getattr(self, 'is_stationary', False) and self.can_move:
            self._update_movement(buildings, building_manager)

        # Update animation
        self.animation.update_animation()

        # Sync properties for backward compatibility
        self._sync_properties()

    def _update_movement(self, buildings, building_manager):
        """Handle movement logic and determine collision objects."""
        # Determine the set of objects to collide with
        collision_objects = []
        if self.building_state.is_inside_building and self.building_state.current_building:
            # --- BEHAVIOR INSIDE A BUILDING ---
            collision_objects = self.building_state.current_building.get_interior_walls()
            
            # Add furniture to collision objects (but we'll skip them when seeking furniture)
            if hasattr(self.building_state.current_building, 'get_furniture'):
                furniture_list = self.building_state.current_building.get_furniture()
                collision_objects.extend(furniture_list)
            
            if self.building_state.building_timer >= self.building_state.stay_duration:
                if not self.building_state.try_exit_building(self):
                    pass
            
            if self.movement.update_movement_timer():
                self._choose_interior_target()
            
            if self.movement.update_movement_timer():
                self._choose_interior_target()
        else:
            # --- BEHAVIOR OUTSIDE ---
            collision_objects = buildings
            if self.movement.update_movement_timer():
                self.movement.choose_new_target(buildings)

            # Try to enter a building (uses interaction zones, not collision)
            if buildings and building_manager:
                self.building_state.try_enter_building(self, buildings, building_manager)

        # --- UNIFIED MOVEMENT AND COLLISION HANDLING ---
        self._move_and_collide(collision_objects)


    def _move_and_collide(self, collision_objects):
        if self.is_stopped_by_player:
            self.state = "idle"
            return

        dx = self.movement.target_x - self.rect.centerx
        dy = self.movement.target_y - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 5:
            self.state = "idle"
            return

        # Calculate movement
        move_x = (dx / distance) * self.speed
        move_y = (dy / distance) * self.speed
        
        # Update facing direction based on movement direction
        if abs(move_x) > 0.1:
            # Set facing_left for non-4-directional sprites
            if not self.animation.has_directional_sprites:
                # Tom (using player assets) should use player logic
                if self.name.lower() == "tom":
                    self.facing_left = move_x < 0  # Player logic: left when moving left
                else:
                    # Only update facing if we're not coming off player interaction
                    if not hasattr(self, '_last_player_facing') or self._last_player_facing is None:
                        self.facing_left = move_x > 0  # Other NPCs
                    else:
                        # Force correct facing based on movement direction
                        self.facing_left = move_x > 0
                        self._last_player_facing = None
            
            # Set current_direction for 4-directional sprites  
            if self.animation.has_directional_sprites:
                if abs(move_y) > abs(move_x):
                    self.animation.current_direction = "down" if move_y > 0 else "up"
                else:
                    self.animation.current_direction = "right" if move_x > 0 else "left"
        
        self.state = "run" if "run" in self.animations else "idle"

        # Store original position
        original_x = self.rect.x
        original_y = self.rect.y

        # Move and collide on X axis
        self.rect.x += move_x
        collision_detected = False
        if collision_objects:
            for obj in collision_objects:
                # Skip furniture collision if NPC is trying to use it AND it's the target furniture
                if (hasattr(obj, 'furniture_type') and self.behavior.should_seek_furniture() and 
                    hasattr(self.behavior, 'find_nearest_furniture')):
                    # Check if this is the furniture we're trying to reach
                    nearest = self.behavior.find_nearest_furniture([obj])
                    if nearest == obj:
                        continue
                        
                # For buildings, use hitbox; for walls, use rect
                collision_rect = getattr(obj, 'hitbox', obj.rect)
                if self.rect.colliderect(collision_rect):
                    self.rect.x = original_x  # Revert X movement
                    collision_detected = True
                    break

        # Move and collide on Y axis
        self.rect.y += move_y
        if collision_objects:
            for obj in collision_objects:
                # Skip furniture collision if NPC is trying to use it AND it's the target furniture
                if (hasattr(obj, 'furniture_type') and self.behavior.should_seek_furniture() and 
                    hasattr(self.behavior, 'find_nearest_furniture')):
                    # Check if this is the furniture we're trying to reach
                    nearest = self.behavior.find_nearest_furniture([obj])
                    if nearest == obj:
                        continue
                        
                collision_rect = getattr(obj, 'hitbox', obj.rect)
                if self.rect.colliderect(collision_rect):
                    self.rect.y = original_y  # Revert Y movement
                    collision_detected = True
                    break

        # If we hit something, pick a new target
        # If we hit something, react immediately
        if collision_detected:
            # Revert to original position and choose a new target to avoid the obstacle
            self.rect.x = original_x
            self.rect.y = original_y
            
            print(f"{self.name} collided. Choosing new target.")
            
            # This is the new, simple avoidance logic. Instead of picking a new random spot,
            # we'll choose a new, nearby, random target. This simulates "bouncing" away.
            self.movement.target_x = self.rect.centerx + random.randint(-50, 50)
            self.movement.target_y = self.rect.centery + random.randint(-50, 50)
            
            # Reset the movement timer so it doesn't try to go to the old target
            self.movement.movement_timer = 0
            self.movement.movement_delay = 30 # A short delay before trying to move again


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
        if self.name.lower() == "tom":
            # Tom uses player logic: face left when player is to the left
            self.facing_left = player.rect.centerx < self.rect.centerx
        else:
            # Other NPCs use inverted logic to match their movement logic
            self.facing_left = player.rect.centerx > self.rect.centerx

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

    def _check_building_collision(self, buildings):
        """Check if NPC is colliding with any building hitbox"""
        if not buildings:
            return False
        for building in buildings:
            if building.check_collision(self.rect):
                return True
        return False

    def _choose_target_away_from_buildings(self, buildings):
        """Choose a new target that's away from buildings"""
        # Instead of trying the hangout area, pick a completely different area
        attempts = 0
        while attempts < 20:
            # Pick random location far from current position
            direction = random.uniform(0, 2 * math.pi)
            distance = random.randint(200, 600)
            test_x = self.rect.centerx + distance * math.cos(direction)
            test_y = self.rect.centery + distance * math.sin(direction)

            # Check if this position would be clear
            test_rect = pygame.Rect(test_x - 16, test_y - 16, 32, 32)
            collision = False
            for building in buildings:
                if building.check_collision(test_rect):
                    collision = True
                    break

            if not collision:
                self.movement.target_x = test_x
                self.movement.target_y = test_y
                return

            attempts += 1

        # Fallback: move in opposite direction from collision
        self.movement.target_x = self.rect.centerx + random.randint(-300, 300)
        self.movement.target_y = self.rect.centery + random.randint(-300, 300)

    def check_and_fix_spawn_collision(self, buildings):
        """Check if NPC spawned inside a building and teleport them out with robust algorithm"""
        if not buildings:
            return

        # Check if currently colliding with any building
        collision_building = None
        for building in buildings:
            if building.check_collision(self.rect):
                collision_building = building
                print(f"NPC {self.name} spawned inside {building.building_type}, finding safe position...")
                break

        if not collision_building:
            print(f"NPC {self.name} spawn position is safe")
            return

        # Try multiple strategies to find a safe position
        safe_position = None

        # Strategy 1: Try positions around the building in expanding circles
        safe_position = self._find_safe_position_around_building(collision_building, buildings)

        # Strategy 2: If that fails, try positions within hangout area
        if not safe_position:
            safe_position = self._find_safe_position_in_hangout(buildings)

        # Strategy 3: If that fails, try positions in expanding search from original spawn
        if not safe_position:
            safe_position = self._find_safe_position_expanding_search(buildings)

        # Strategy 4: Emergency fallback - move far away from all buildings
        if not safe_position:
            safe_position = self._emergency_safe_position(buildings)

        # Apply the safe position
        if safe_position:
            old_pos = (self.rect.centerx, self.rect.centery)
            self.rect.centerx, self.rect.centery = safe_position
            self.x, self.y = safe_position  # Update x, y coordinates too
            print(f"Moved {self.name} from {old_pos} to {safe_position}")
        else:
            print(f"WARNING: Could not find safe position for {self.name}")

    def _find_safe_position_around_building(self, building, all_buildings):
        """Find a safe position around a specific building"""
        center_x = building.rect.centerx
        center_y = building.rect.centery

        # Try positions in expanding circles around the building
        for distance in [120, 150, 200, 250, 300]:  # Start far enough to clear building
            for angle in range(0, 360, 15):  # Every 15 degrees for good coverage
                rad = math.radians(angle)
                test_x = center_x + distance * math.cos(rad)
                test_y = center_y + distance * math.sin(rad)

                if self._is_position_safe(test_x, test_y, all_buildings):
                    return (test_x, test_y)

        return None

    def _find_safe_position_near_building(self, building):
        """Find a safe position around a building - legacy method, now calls improved version"""
        # Use the new improved method
        safe_pos = self._find_safe_position_around_building(building, [building])
        return safe_pos

    def _find_safe_position_in_hangout(self, buildings):
        """Find a safe position within the NPC's hangout area"""
        hangout = self.hangout_area
        attempts = 50  # Try 50 random positions

        for _ in range(attempts):
            test_x = random.randint(hangout['x'], hangout['x'] + hangout['width'])
            test_y = random.randint(hangout['y'], hangout['y'] + hangout['height'])

            if self._is_position_safe(test_x, test_y, buildings):
                return (test_x, test_y)

        return None

    def _find_safe_position_expanding_search(self, buildings):
        """Find a safe position using expanding search from original spawn"""
        original_x = self.rect.centerx
        original_y = self.rect.centery

        # Try expanding squares around original position
        for radius in range(50, 400, 25):  # Expand in 25-pixel increments
            # Try positions along the perimeter of the square
            positions_to_try = []

            # Top and bottom edges
            for x in range(original_x - radius, original_x + radius + 1, 25):
                positions_to_try.append((x, original_y - radius))  # Top edge
                positions_to_try.append((x, original_y + radius))   # Bottom edge

            # Left and right edges (excluding corners already covered)
            for y in range(original_y - radius + 25, original_y + radius, 25):
                positions_to_try.append((original_x - radius, y))  # Left edge
                positions_to_try.append((original_x + radius, y))  # Right edge

            # Shuffle to avoid bias
            random.shuffle(positions_to_try)

            for test_x, test_y in positions_to_try:
                if self._is_position_safe(test_x, test_y, buildings):
                    return (test_x, test_y)

        return None

    def _emergency_safe_position(self, buildings):
        """Emergency fallback - find any position far from buildings"""
        hangout = self.hangout_area

        # Try positions at the edges of a much larger area
        search_area = {
            'x': hangout['x'] - 300,
            'y': hangout['y'] - 300,
            'width': hangout['width'] + 600,
            'height': hangout['height'] + 600
        }

        attempts = 100  # More attempts for emergency
        for _ in range(attempts):
            test_x = random.randint(search_area['x'], search_area['x'] + search_area['width'])
            test_y = random.randint(search_area['y'], search_area['y'] + search_area['height'])

            if self._is_position_safe(test_x, test_y, buildings):
                return (test_x, test_y)

        # Absolute last resort - just pick a position far from hangout center
        fallback_x = hangout['x'] + hangout['width'] // 2 + 500
        fallback_y = hangout['y'] + hangout['height'] // 2 + 500
        print(f"Using absolute fallback position for {self.name}: ({fallback_x}, {fallback_y})")
        return (fallback_x, fallback_y)

    def _is_position_safe(self, x, y, buildings):
        """Check if a position is safe (no building collisions)"""
        # Create test rect for NPC at this position
        test_rect = pygame.Rect(x - 16, y - 16, 32, 32)  # Assuming NPC is 32x32

        # Check collision with all buildings
        for building in buildings:
            if building.check_collision(test_rect):
                return False

        return True

    def draw(self, surface, font=None):
        """Draw NPC on screen with proper facing direction"""
        # Get the correctly facing image
        npc_image = self.animation.get_facing_corrected_image()
        
        surface.blit(npc_image, self.rect)

        # Draw speech bubble
        self.interaction.draw_speech_bubble(surface, font)

    def create_npc(name, personality, assets, spawn_x, spawn_y, hangout_area=None):
        """
        Create an NPC with custom parameters
        
        Args:
            name: NPC's name (string)
            personality: NPC's personality description (string) 
            assets: Asset dictionary containing animations
            spawn_x: X coordinate for spawn position
            spawn_y: Y coordinate for spawn position
            hangout_area: Optional dict with 'x', 'y', 'width', 'height' keys
        
        Returns:
            NPC instance
        """
        # Add the NPC to dialogue data if not already present
        if name not in NPCDialogue.DIALOGUE_DATA:
            NPCDialogue.DIALOGUE_DATA[name] = {
                "bubble": f"Hello, I'm {name}!",
                "personality": personality
            }
        
        # Create and return the NPC
        return NPC(spawn_x, spawn_y, assets, name, hangout_area)
    
    def _seek_rest(self, building_manager, furniture_list):
        """If NPC is seeking rest, prefer interior furniture, else try entering building."""
        # If inside, try to sit
        if self.building_state.is_inside_building and furniture_list:
            self.behavior.try_use_furniture(furniture_list)
            return

        # else try to enter building (use building_manager.buildings if available)
        if building_manager and hasattr(building_manager, "buildings"):
            self.building_state.try_enter_building(self, building_manager.buildings, building_manager)

    @property
    def can_move(self):
        """Check if NPC can move (not using furniture, not sitting, etc.)"""
        return not (self.behavior.using_furniture or self.behavior.is_sitting or getattr(self, '_cannot_move', False))

    @can_move.setter
    def can_move(self, value):
        """Set movement capability"""
        self._cannot_move = not value

    def get_tiredness(self):
        return self.behavior.tiredness

    def is_using_furniture(self):
        return self.behavior.using_furniture

    def get_furniture_status(self):
        if self.behavior.using_furniture and self.behavior.current_furniture:
            return f"Using {self.behavior.current_furniture.furniture_type}"
        if self.behavior.should_seek_furniture():
            return f"Seeking furniture (tired: {self.behavior.tiredness:.1f})"
        return f"Not using furniture (tiredness: {self.behavior.tiredness:.1f})"

    def get_debug_info(self):
        return {
            "name": self.name,
            "location": self.get_current_location_info(),
            "behavior": self.behavior.get_behavior_info(),
            "obedience": self.obedience,
            "show_speech_bubble": self.show_speech_bubble,
            "dialogue": self.dialogue[:50] + "..." if len(self.dialogue) > 50 else self.dialogue,
            "furniture_status": ("Using " + getattr(self.behavior.current_furniture, "furniture_type", "") ) if self.behavior.using_furniture else ("Seeking" if self.behavior.should_seek_furniture() else "Idle"),
            "tiredness": self.behavior.tiredness
        }
    
class CommandProcessor:
    """
    Processes raw player text, asks the AI to classify intent, and executes commands.
    Use process_input(npc, player_input, chat_callback) where chat_callback(msg) prints to UI once.
    """

    VALID_CMDS = {"FOLLOW", "STOP", "REST", "NONE"}

    @staticmethod
    def _ask_ai_for_command(player_input):
        # Prompt instructs the AI to return one word: FOLLOW, STOP, REST, or NONE.
        prompt = (
            "You are a command interpreter for a game NPC. "
            "Given the player's message, respond with ONE of: FOLLOW, STOP, REST, NONE. "
            "Do not output anything else. "
            f'Player message: "{player_input}"'
        )
        try:
            resp = ai.get_ai_response(prompt)  # uses your ai.py
            if not resp:
                return "NONE"
            # Normalize
            text = resp.strip().upper()
            # try to extract one of the valid tokens
            for tok in CommandProcessor.VALID_CMDS:
                if tok in text:
                    print(f"DEBUG: AI Parser Response: {resp.strip()}")
                    return tok
            # else fallback to NONE
            print(f"DEBUG: AI Parser Response: NONE!")
            return "NONE"
        except Exception as e:
            # conservative fallback
            print("AI command parse error:", e)
            return "NONE"

    @staticmethod
    def process_input(npc: NPC, player_input: str, chat_callback=None, player=None):
        """
        Processes the input exactly once and executes a command if AI says so.
        - chat_callback: function(msg: str) -> None used to display the UI chat once.
        - player: optional Player instance (used for follow target)
        """
        # get intent from AI
        cmd = CommandProcessor._ask_ai_for_command(player_input)

        # craft a single confirmation message (if any) to send via chat_callback
        confirmation = None
        
        print("We got up to here!")
        if cmd == "FOLLOW":
            if player is None:
                confirmation = "I can't follow — no player target."
            else:
                try:
                    npc.behavior.start_following(player)
                    confirmation = f"{npc.name} will follow you."
                except Exception as e:
                    print(f"Error starting follow: {e}")
                    confirmation = f"I couldn't start following you."
        elif cmd == "STOP":
            npc.behavior.stop_following()
            npc.behavior.force_stop_furniture_use()
            confirmation = f"{npc.name} stopped."
        elif cmd == "REST":
            # set NPC to seek rest immediately
            # make them look for furniture/building next update
            npc.behavior.tiredness = max(npc.behavior.exhaustion_threshold + 1, npc.behavior.tiredness)
            confirmation = f"{npc.name} will look for a place to rest."
        else:
            # NONE -> treat as normal chat; route to AI for reply if you want
            confirmation = None

        # send a single message if requested
        if chat_callback and confirmation:
            chat_callback(confirmation)

        # return the parsed command for any gameplay logic
        return cmd