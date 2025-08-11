# npc.py
# Consolidated NPC module
# Integration notes:
# - Expects `ai.py` with function get_ai_response(prompt) returning a string.
# - Expects `player` objects to have rect, x, y, and optionally current_scene/entry_point.
# - Expects `building` objects to have rect, building_type, exit_zone, interior_size, get_furniture_list(),
#   check_interaction_range(rect), check_exit_range(rect), add_npc(npc), remove_npc(npc), and optionally `.scene`.
# - If your game uses a dedicated scene-change API, adapt the _leave_building_and_follow() hook in NPC._seek_follow_target.

import pygame
import random
import math
from functions import app
from entities.player import Player
from functions import ai  # your ai.py from earlier (must provide get_ai_response(prompt))


# ---------------------------
# Dialogue / Data
# ---------------------------
class NPCDialogue:
    """Simple dialogue store"""
    DIALOGUE_DATA = {
        "Dave": {
            "bubble": "Hello, I'm Dave. I love adventures in this digital world!",
            "personality": "You are Dave, an adventurous NPC who loves exploring the digital world. You're friendly and enthusiastic about new experiences.",
            "obedience": 4,
            "stats": ""
        },
        "Lisa": {
            "bubble": "Hi, I'm Lisa. Coding and coffee fuel my day!",
            "personality": "You are Lisa, a tech-savvy NPC who loves coding and coffee. You're knowledgeable and helpful with technical topics.",
            "obedience": 3,
            "stats": ""
        },
        "Tom": {
            "bubble": "Hey, I'm Tom. Always here to keep things running smoothly!",
            "personality": "You are Tom, a reliable NPC who keeps things organized and running smoothly. You're dependable and solution-oriented.",
            "obedience": 5,
            "stats": ""
        }
    }

    DEFAULT_DIALOGUE = {
        "bubble": "Hello, I'm just an NPC.",
        "personality": "You are a generic NPC in a game world.",
        "obedience": 2,
        "stats": ""
    }

    @classmethod
    def get_dialogue(cls, name):
        return cls.DIALOGUE_DATA.get(name, cls.DEFAULT_DIALOGUE)


# ---------------------------
# Movement
# ---------------------------
class NPCMovement:
    """Handles NPC movement and pathfinding logic (uses npc.can_move for gating)"""

    def __init__(self, npc):
        self.npc = npc
        self.target_x = npc.x
        self.target_y = npc.y
        self.movement_timer = 0
        self.movement_delay = random.randint(120, 300)

    def choose_new_target(self, buildings=None, building_manager=None):
        """Choose a new target position for movement based on behavior state"""
        if self.npc.behavior.behavior_state == "seeking_rest":
            # pass both so helper can check NPC's own building_state
            self._choose_chair_target(buildings, building_manager)
        elif self.npc.behavior.behavior_state == "following":
            self._choose_following_target()
        else:
            self._choose_free_roam_target(buildings)

    def update_movement_timer(self):
        self.movement_timer += 1
        if self.movement_timer >= self.movement_delay:
            self.movement_timer = 0
            self.movement_delay = random.randint(120, 300)
            return True
        return False

    def _choose_chair_target(self, buildings=None, building_manager=None):
        """Choose target position when seeking a chair - uses NPC's building_state."""
        # If NPC is inside a building, search that building's furniture
        if getattr(self.npc, "building_state", None) and self.npc.building_state.is_inside_building:
            current_building = self.npc.building_state.current_building
            if current_building:
                furniture = current_building.get_furniture_list()
                chairs = [f for f in furniture if getattr(f, "furniture_type", "") == "chair" and not getattr(f, "is_occupied", False)]
                if chairs:
                    closest = min(chairs, key=lambda c: math.hypot(c.rect.centerx - self.npc.rect.centerx, c.rect.centery - self.npc.rect.centery))
                    # Target slightly in front of the chair for better approach
                    self.target_x = closest.rect.centerx
                    self.target_y = closest.rect.bottom + 5  # Target just below the chair
                    self.npc.target_chair = closest
                    return

        # NPC is outside (or couldn't find an interior chair) -> move toward a building entrance
        candidates = buildings or (getattr(building_manager, "buildings", []) if building_manager else [])
        # Prioritize buildings that have available chairs
        buildings_with_chairs = []
        for building in candidates:
            if getattr(building, "can_npc_enter", lambda: True)():
                furniture = building.get_furniture_list()
                available_chairs = [f for f in furniture if getattr(f, "furniture_type", "") == "chair" and not getattr(f, "is_occupied", False)]
                if available_chairs:
                    buildings_with_chairs.append(building)
        
        # Choose the closest building with chairs, or any building as fallback
        target_building = None
        if buildings_with_chairs:
            target_building = min(buildings_with_chairs, key=lambda b: math.hypot(b.rect.centerx - self.npc.rect.centerx, b.rect.centery - self.npc.rect.centery))
        elif candidates:
            # Fallback to any enterable building
            for building in candidates:
                if getattr(building, "can_npc_enter", lambda: True)():
                    target_building = building
                    break
        
        if target_building:
            # Prefer aiming at building exit_zone if available (entrance)
            if hasattr(target_building, "exit_zone") and target_building.exit_zone:
                self.target_x = target_building.exit_zone.centerx
                self.target_y = target_building.exit_zone.centery
            else:
                self.target_x = target_building.rect.centerx
                self.target_y = target_building.rect.centery
            return

        # fallback
        self._choose_random_target()

    def move_towards_target(self, player=None):
        """Move NPC towards target position. If behavior prevents movement (npc.can_move False) we still allow interaction/chat."""
        # Following behavior handled specially
        if self.npc.behavior.behavior_state == "following" and self.npc.behavior.follow_target:
            self._follow_player(self.npc.behavior.follow_target)
            return

        if not self.npc.can_move:
            self.npc.state = "idle"
            return

        dx = self.target_x - self.npc.rect.centerx
        dy = self.target_y - self.npc.rect.centery
        distance = math.hypot(dx, dy)

        # Reached a resting target (chair)
        if self.npc.behavior.behavior_state == "seeking_rest" and distance < 24 and hasattr(self.npc, "target_chair"):
            # attempt sit
            self._try_sit_on_target_chair()
            return

        if distance > 4:
            move_x = (dx / distance) * self.npc.speed if distance != 0 else 0
            move_y = (dy / distance) * self.npc.speed if distance != 0 else 0
            self.npc.rect.centerx += move_x
            self.npc.rect.centery += move_y
            self.npc.facing_left = move_x < 0
            self.npc.state = "run" if "run" in self.npc.animations else "idle"
        else:
            self.npc.state = "idle"

    def _follow_player(self, player):
        """Follow player across positions. If in different scene/building, attempt to exit building first."""
        # If NPC is inside a building and player is outside, head to exit
        if self.npc.building_state.is_inside_building:
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

        # Otherwise compute distance in world coords and move appropriately
        dx = player.rect.centerx - self.npc.rect.centerx
        dy = player.rect.centery - self.npc.rect.centery
        distance = math.hypot(dx, dy)

        desired = self.npc.behavior.follow_distance
        tolerance = 10
        if distance < desired - tolerance:
            dx, dy = -dx, -dy
            distance = math.hypot(dx, dy)
        elif distance <= desired + tolerance and distance >= desired - tolerance:
            # already at comfortable distance
            return

        if distance > 0 and self.npc.can_move:
            move_x = (dx / distance) * self.npc.speed
            move_y = (dy / distance) * self.npc.speed
            self.npc.rect.centerx += move_x
            self.npc.rect.centery += move_y
            self.npc.facing_left = move_x < 0
            self.npc.state = "run" if "run" in self.npc.animations else "idle"
        else:
            self.npc.state = "idle"

    def _choose_following_target(self):
        # placeholder - target determined live in _follow_player
        pass

    def _choose_free_roam_target(self, buildings=None):
        # try to enter building rarely
        if random.random() < 0.2 and buildings:
            building = random.choice(buildings)
            self.target_x = building.rect.centerx
            self.target_y = building.rect.centery
            return
        self._choose_random_target()

    def _choose_random_target(self):
        hangout = getattr(self.npc, "hangout_area", {'x': self.npc.rect.centerx - 100, 'y': self.npc.rect.centery - 100, 'width': 200, 'height': 200})
        # Ensure hangout area has valid coordinates
        if hangout['x'] <= 0 or hangout['y'] <= 0:
            hangout = {'x': max(50, self.npc.rect.centerx - 100), 'y': max(50, self.npc.rect.centery - 100), 'width': 200, 'height': 200}
            
        if random.random() < 0.75:
            self.target_x = random.randint(max(0, hangout['x']), hangout['x'] + hangout['width'])
            self.target_y = random.randint(max(0, hangout['y']), hangout['y'] + hangout['height'])
        else:
            self.target_x = random.randint(max(0, hangout['x'] - 200), hangout['x'] + hangout['width'] + 200)
            self.target_y = random.randint(max(0, hangout['y'] - 200), hangout['y'] + hangout['height'] + 200)

    def _try_sit_on_target_chair(self):
        if hasattr(self.npc, "target_chair") and self.npc.target_chair:
            if self.npc.behavior.sit_on_chair(self.npc.target_chair):
                # clear target
                self.npc.target_chair = None


# ---------------------------
# Building state
# ---------------------------
class NPCBuildingState:
    def __init__(self):
        self.is_inside_building = False
        self.current_building = None
        self.exterior_position = None
        self.building_timer = 0
        self.stay_duration = random.randint(300, 900)
        self.interaction_cooldown = 0
        self.interaction_delay = 300

    def try_enter_building(self, npc, buildings, building_manager):
        if self.is_inside_building or self.interaction_cooldown > 0:
            return False
        for building in buildings:
            if self._can_enter_building(npc, building):
                self._enter_building(npc, building)
                return True
        return False

    def _can_enter_building(self, npc, building):
        return (getattr(building, "can_enter", False)
                and hasattr(building, "check_interaction_range")
                and building.check_interaction_range(npc.rect)
                and hasattr(building, "can_npc_enter")
                and building.can_npc_enter())

    def _enter_building(self, npc, building):
        self.exterior_position = {'x': npc.rect.centerx, 'y': npc.rect.centery}
        if hasattr(building, "add_npc"):
            building.add_npc(npc)
        # position
        if hasattr(building, 'exit_zone') and building.exit_zone:
            npc.rect.centerx = building.exit_zone.centerx + random.randint(-30, 30)
            npc.rect.centery = building.exit_zone.centery + random.randint(-30, 30)
        else:
            iw, ih = getattr(building, 'interior_size', (800, 600))
            npc.rect.centerx = iw // 2
            npc.rect.centery = ih // 2

        self.is_inside_building = True
        self.current_building = building
        self.building_timer = 0
        self.stay_duration = random.randint(300, 900)
        print(f"{npc.name} entered {building.building_type}")

    def try_exit_building(self, npc):
        if not self.is_inside_building or not self.current_building:
            return False
        if self.current_building.check_exit_range(npc.rect):
            self._exit_building(npc)
            return True
        else:
            self._move_toward_exit(npc)
            return False

    def _exit_building(self, npc):
        building_ref = self.current_building
        if self.exterior_position:
            npc.rect.centerx = self.exterior_position['x']
            npc.rect.centery = self.exterior_position['y']
        if hasattr(building_ref, "remove_npc"):
            building_ref.remove_npc(npc)

        self.is_inside_building = False
        self.current_building = None
        self.exterior_position = None
        self.interaction_cooldown = self.interaction_delay

        # ensure any furniture usage stops
        if hasattr(npc, "behavior") and hasattr(npc.behavior, "force_stop_furniture_use"):
            npc.behavior.force_stop_furniture_use()

        print(f"{npc.name} exited building")

    def _move_toward_exit(self, npc):
        if self.current_building and hasattr(self.current_building, 'exit_zone'):
            exit_center = self.current_building.exit_zone.center
            npc.movement.target_x = exit_center[0]
            npc.movement.target_y = exit_center[1]

    def update_timers(self):
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1
        if self.is_inside_building:
            self.building_timer += 1


# ---------------------------
# Interaction / speech
# ---------------------------
class NPCInteraction:
    def __init__(self, npc):
        self.npc = npc
        self.show_speech_bubble = False
        self.speech_bubble_timer = 0
        self.speech_bubble_duration = 180
        self.detection_radius = 80
        self.stop_distance = 50

    def update_player_interaction(self, player, building_manager):
        if not player or not self._in_same_location(player, building_manager):
            self.npc.is_stopped_by_player = False
            return

        distance = self.npc._get_distance_to_player(player)
        if distance <= self.detection_radius:
            self._interact_with_player(player, distance)
        else:
            self.npc.is_stopped_by_player = False

    def _in_same_location(self, player, building_manager):
        if self.npc.building_state.is_inside_building and building_manager and building_manager.is_inside_building():
            return self.npc.building_state.current_building == building_manager.get_current_interior()
        elif not self.npc.building_state.is_inside_building and not (building_manager and building_manager.is_inside_building()):
            return True
        return False

    def _interact_with_player(self, player, distance):
        self.npc.is_stopped_by_player = True
        self.npc._face_player(player)
        self.npc.state = "idle"
        if distance <= self.stop_distance:
            self.show_speech_bubble = True
            self.speech_bubble_timer = self.speech_bubble_duration

    def update_speech_bubble(self):
        tired_msg = self.npc.behavior.get_tiredness_message() if hasattr(self.npc, "behavior") else ""
        if tired_msg:
            self.npc.bubble_dialogue = tired_msg
            self.show_speech_bubble = True
            self.speech_bubble_timer = self.speech_bubble_duration
            return

        if self.npc.behavior.is_following_player and not tired_msg:
            self.show_speech_bubble = False
            return

        if self.show_speech_bubble:
            self.speech_bubble_timer -= 1
            if self.speech_bubble_timer <= 0:
                self.show_speech_bubble = False

    def draw_speech_bubble(self, surface, font):
        if not self.show_speech_bubble or not font:
            return
        text_surface = font.render(self.npc.bubble_dialogue, True, (0, 0, 0))
        text_rect = text_surface.get_rect()
        bubble_width = text_rect.width + 20
        bubble_height = text_rect.height + 16
        bubble_x = self.npc.rect.centerx - bubble_width // 2
        bubble_y = self.npc.rect.top - bubble_height - 10
        self._draw_bubble_background(surface, bubble_x, bubble_y, bubble_width, bubble_height)
        self._draw_bubble_tail(surface, bubble_y + bubble_height)
        surface.blit(text_surface, (bubble_x + 10, bubble_y + 8))

    def _draw_bubble_background(self, surface, x, y, width, height):
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (255, 255, 255), rect)
        pygame.draw.rect(surface, (0, 0, 0), rect, 2)

    def _draw_bubble_tail(self, surface, tail_y):
        tail_points = [
            (self.npc.rect.centerx - 10, tail_y),
            (self.npc.rect.centerx + 10, tail_y),
            (self.npc.rect.centerx, tail_y + 10)
        ]
        pygame.draw.polygon(surface, (255, 255, 255), tail_points)
        pygame.draw.polygon(surface, (0, 0, 0), tail_points, 2)


# ---------------------------
# Behavior (tiredness + furniture merged)
# ---------------------------
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
        self.tiredness = 100.0
        self.tiredness_decay_rate = 0.2
        self.tiredness_recovery_rate = 0.5
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
            self.furniture_timer += 1
            if self.furniture_timer >= self.furniture_use_duration:
                self._stop_using_furniture()

    def _update_tiredness(self):
        if self.is_sitting or self.using_furniture:
            self.tiredness = max(0.0, self.tiredness - self.tiredness_recovery_rate)
        else:
            self.tiredness = min(100.0, self.tiredness + self.tiredness_decay_rate)

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
        # Check if close enough to interact (more lenient range)
        dx = self.npc.rect.centerx - target.rect.centerx
        dy = self.npc.rect.centery - target.rect.centery
        distance = math.hypot(dx, dy)
        if distance < 32:  # More lenient interaction range
            return self._start_using_furniture(target)
        else:
            # move toward it
            self.npc.movement.target_x = target.rect.centerx
            self.npc.movement.target_y = target.rect.bottom + 8
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

    def sit_on_chair(self, chair):
        """Legacy API used elsewhere — sits on chair and sets npc.can_move False"""
        return self._sit_on_chair(chair)

    def _sit_on_chair(self, chair):
        if getattr(chair, "is_occupied", False):
            return False
        # snap to chair
        self.npc.rect.centerx = chair.rect.centerx
        self.npc.rect.centery = chair.rect.centery
        try:
            chair.is_occupied = True
        except Exception:
            pass
        self.using_furniture = True
        self.current_furniture = chair
        self.current_chair = chair
        self.is_sitting = True
        self.furniture_timer = 0
        self.furniture_use_duration = random.randint(300, 900)
        # freeze movement but allow chat/interaction
        self.npc.can_move = False
        self.npc.state = "idle"
        return True

    def _leave_chair(self):
        if self.current_chair:
            try:
                self.current_chair.is_occupied = False
            except Exception:
                pass
        self.current_chair = None
        self.is_sitting = False
        self.using_furniture = False
        self.npc.can_move = True

    def _stop_using_furniture(self):
        if self.current_furniture:
            if getattr(self.current_furniture, "furniture_type", "") == "chair":
                try:
                    self.current_furniture.is_occupied = False
                except Exception:
                    pass
                # nudge away
                self.npc.rect.centerx += random.randint(-16, 16)
                self.npc.rect.centery += 12
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
        self.current_chair = None

    def force_stop_furniture_use(self):
        if self.using_furniture:
            self._stop_using_furniture()


# ---------------------------
# Animation (unchanged)
# ---------------------------
class NPCAnimation:
    def __init__(self, npc, assets):
        self.npc = npc
        self.animations = assets["player"]
        self.state = "idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 8
        self.image = self.animations[self.state][self.frame_index]

    def update_animation(self):
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.animations.get(self.npc.state, self.animations.get("idle"))
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]
            center = self.npc.rect.center
            self.npc.rect = self.image.get_rect()
            self.npc.rect.center = center


# ---------------------------
# NPC main class
# ---------------------------
class NPC:
    def __init__(self, x, y, assets, name, hangout_area=None):
        self.x = x
        self.y = y
        self.name = name
        self.speed = app.PLAYER_SPEED * 0.7
        self.facing_left = False
        self.is_stopped_by_player = False
        self.chat_history = []
        self.can_move = True  # canonical movement gate

        # components
        self.animation = NPCAnimation(self, assets)
        self.movement = NPCMovement(self)
        self.building_state = NPCBuildingState()
        self.interaction = NPCInteraction(self)
        self.behavior = NPCBehavior(self)

        # rect and visuals
        self.rect = self.animation.image.get_rect(center=(x, y))
        d = NPCDialogue.get_dialogue(name)
        self.bubble_dialogue = d["bubble"]
        self.dialogue = d["personality"]
        self.stats = d.get("stats", "")
        self.obedience = d.get("obedience", 2)

        self.hangout_area = hangout_area or {'x': x - 100, 'y': y - 100, 'width': 200, 'height': 200}

        # backward compat props
        self.state = self.animation.state
        self.image = self.animation.image
        self.animations = self.animation.animations
        self.show_speech_bubble = self.interaction.show_speech_bubble
        self.is_inside_building = self.building_state.is_inside_building
        self.current_building = self.building_state.current_building

        # runtime target placeholders
        self.target_chair = None

    def update(self, player=None, buildings=None, building_manager=None, furniture_list=None):
        """Main per-frame update."""
        # update behavior
        self.behavior.update(player, building_manager)

        # if tired: try to seek rest
        if self.behavior.tiredness >= self.behavior.exhaustion_threshold:
            self._seek_rest(building_manager, furniture_list)

        # update furniture interaction if inside building
        if self.building_state.is_inside_building and furniture_list:
            self.behavior.try_use_furniture(furniture_list)

        # building interior handling
        if self.building_state.is_inside_building and self.building_state.current_building:
            self._update_interior_behavior(building_manager)

        # player interactions and speech bubble
        self.interaction.update_player_interaction(player, building_manager)
        self.interaction.update_speech_bubble()

        # movement
        if not self.is_stopped_by_player:
            self._update_movement(buildings, building_manager, player)

        # animation and sync
        self.animation.update_animation()
        self._sync_properties()

    def _seek_rest(self, building_manager, furniture_list):
        """If NPC is seeking rest, prefer interior furniture, else try entering building."""
        # If inside, try to sit
        if self.building_state.is_inside_building and furniture_list:
            self.behavior.try_use_furniture(furniture_list)
            return

        # else try to enter building (use building_manager.buildings if available)
        if building_manager and hasattr(building_manager, "buildings"):
            self.building_state.try_enter_building(self, building_manager.buildings, building_manager)

    def _update_interior_behavior(self, building_manager):
        if self.building_state.building_timer >= self.building_state.stay_duration:
            self.building_state.try_exit_building(self)
        if building_manager and self.building_state.is_inside_building and self.building_state.current_building:
            walls = self.building_state.current_building.get_interior_walls()
            self._handle_interior_collision(walls)

    def _update_movement(self, buildings, building_manager, player=None):
        if self.movement.update_movement_timer():
            if self.building_state.is_inside_building and self.building_state.current_building:
                # interior wandering
                self._choose_interior_target()
            else:
                self.movement.choose_new_target(buildings, building_manager)

        # movement tries to follow or walk toward target
        self.movement.move_towards_target(player)

        # if outside, potentially enter building
        if (not self.building_state.is_inside_building) and buildings and building_manager:
            self.building_state.try_enter_building(self, buildings, building_manager)

    def _choose_interior_target(self):
        if self.building_state.building_timer >= self.building_state.stay_duration * 0.8:
            exit_center = self.building_state.current_building.exit_zone.center
            self.movement.target_x = exit_center[0] + random.randint(-20, 20)
            self.movement.target_y = exit_center[1] + random.randint(-20, 20)
        else:
            iw, ih = self.building_state.current_building.interior_size
            margin = 50
            self.movement.target_x = random.randint(margin, iw - margin)
            self.movement.target_y = random.randint(margin, ih - margin)

    def _handle_interior_collision(self, collision_objects):
        for wall in collision_objects:
            if wall.check_collision(self.rect):
                resolved = wall.resolve_collision(self.rect)
                self.rect = resolved
                if self.building_state.current_building:
                    iw, ih = self.building_state.current_building.interior_size
                    margin = 50
                    self.movement.target_x = random.randint(margin, iw - margin)
                    self.movement.target_y = random.randint(margin, ih - margin)

    def _sync_properties(self):
        self.state = self.animation.state
        self.image = self.animation.image
        self.show_speech_bubble = self.interaction.show_speech_bubble
        self.is_inside_building = self.building_state.is_inside_building
        self.current_building = self.building_state.current_building
        self.x = self.rect.centerx
        self.y = self.rect.centery

    # Utilities
    def _get_distance_to_player(self, player):
        dx = self.rect.centerx - player.rect.centerx
        dy = self.rect.centery - player.rect.centery
        return math.hypot(dx, dy)

    def _get_distance_to_building(self, building):
        dx = self.rect.centerx - building.rect.centerx
        dy = self.rect.centery - building.rect.centery
        return math.hypot(dx, dy)

    def _face_player(self, player):
        self.facing_left = player.rect.centerx < self.rect.centerx

    def sync_position(self):
        self.x = self.rect.centerx
        self.y = self.rect.centery

    def get_current_location_info(self):
        if self.building_state.is_inside_building and self.building_state.current_building:
            return f"{self.name} is inside {self.building_state.current_building.building_type}"
        return f"{self.name} is outside at ({self.rect.centerx}, {self.rect.centery})"

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

    def draw(self, surface, font=None):
        img = pygame.transform.flip(self.image, True, False) if self.facing_left else self.image
        surface.blit(img, self.rect)
        self.interaction.draw_speech_bubble(surface, font)

    # Furniture / behavior proxies
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


# ---------------------------
# Command interpreter - avoids duplicate chat prints and uses AI for context
# ---------------------------
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


# End of file
