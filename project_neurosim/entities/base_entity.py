import pygame
import math
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class EntityState(Enum):
    """Common entity states"""
    IDLE = "idle"
    MOVING = "moving"
    RUNNING = "run"
    INTERACTING = "interacting"
    ENTERING_BUILDING = "entering_building"
    EXITING_BUILDING = "exiting_building"


class EntityType(Enum):
    """Types of entities in the game"""
    PLAYER = "player"
    NPC = "npc"
    OBJECT = "object"
    PROJECTILE = "projectile"


class MovementComponent:
    """Handles entity movement and pathfinding"""
    
    def __init__(self, entity, speed: float = 2.0):
        self.entity = entity
        self.base_speed = speed
        self.current_speed = speed
        self.target_x = entity.x
        self.target_y = entity.y
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.is_moving = False
        self.movement_smoothing = 0.8  # For smooth movement
        
        # Movement constraints
        self.can_move = True
        self.is_blocked = False
        
        # Path following
        self.path = []
        self.path_index = 0
    
    def set_target(self, x: float, y: float):
        """Set movement target"""
        self.target_x = x
        self.target_y = y
        self.is_moving = True
    
    def move_towards_target(self, delta_time: float = 1.0):
        """Move entity towards target position"""
        if not self.can_move or not self.is_moving:
            return
        
        dx = self.target_x - self.entity.rect.centerx
        dy = self.target_y - self.entity.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 5:  # Minimum distance threshold
            # Normalize direction vector
            direction_x = dx / distance
            direction_y = dy / distance
            
            # Calculate movement
            move_distance = self.current_speed * delta_time
            move_x = direction_x * move_distance
            move_y = direction_y * move_distance
            
            # Apply smoothing
            self.velocity_x = (self.velocity_x * self.movement_smoothing + 
                             move_x * (1 - self.movement_smoothing))
            self.velocity_y = (self.velocity_y * self.movement_smoothing + 
                             move_y * (1 - self.movement_smoothing))
            
            # Update position
            new_x = self.entity.rect.centerx + self.velocity_x
            new_y = self.entity.rect.centery + self.velocity_y
            
            # Check collision before moving
            if not self._would_collide(new_x, new_y):
                self.entity.rect.centerx = new_x
                self.entity.rect.centery = new_y
                self.entity.sync_position()
                
                # Update facing direction
                self.entity.facing_left = move_x < 0
                self.entity.set_state(EntityState.MOVING)
            else:
                self.is_blocked = True
                self.entity.set_state(EntityState.IDLE)
        else:
            # Reached target
            self.is_moving = False
            self.velocity_x = 0
            self.velocity_y = 0
            self.entity.set_state(EntityState.IDLE)
    
    def _would_collide(self, new_x: float, new_y: float) -> bool:
        """Check if movement would cause collision"""
        # Create test rect at new position
        test_rect = self.entity.rect.copy()
        test_rect.centerx = new_x
        test_rect.centery = new_y
        
        # Check against collision objects
        collision_objects = self.entity.get_collision_objects()
        for obj in collision_objects:
            if hasattr(obj, 'rect') and test_rect.colliderect(obj.rect):
                return True
            elif hasattr(obj, 'check_collision') and obj.check_collision(test_rect):
                return True
        
        return False
    
    def stop(self):
        """Stop movement immediately"""
        self.is_moving = False
        self.velocity_x = 0
        self.velocity_y = 0
    
    def set_speed(self, speed: float):
        """Set movement speed"""
        self.current_speed = speed


class AnimationComponent:
    """Handles entity animation"""
    
    def __init__(self, entity, animations: Dict[str, List[pygame.Surface]]):
        self.entity = entity
        self.animations = animations
        self.current_animation = "idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 8  # Frames per animation frame
        self.loop = True
        self.paused = False
        
        # Set initial image
        if self.animations and "idle" in self.animations:
            self.entity.image = self.animations["idle"][0]
    
    def play_animation(self, animation_name: str, loop: bool = True):
        """Play a specific animation"""
        if animation_name in self.animations and animation_name != self.current_animation:
            self.current_animation = animation_name
            self.frame_index = 0
            self.animation_timer = 0
            self.loop = loop
            self.paused = False
    
    def update(self):
        """Update animation frame"""
        if self.paused or not self.animations or self.current_animation not in self.animations:
            return
        
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.animations[self.current_animation]
            
            if self.loop:
                self.frame_index = (self.frame_index + 1) % len(frames)
            else:
                self.frame_index = min(self.frame_index + 1, len(frames) - 1)
            
            # Update entity image
            self.entity.image = frames[self.frame_index]
            
            # Maintain rect center position
            center = self.entity.rect.center
            self.entity.rect = self.entity.image.get_rect()
            self.entity.rect.center = center
    
    def pause(self):
        """Pause animation"""
        self.paused = True
    
    def resume(self):
        """Resume animation"""
        self.paused = False
    
    def is_finished(self) -> bool:
        """Check if non-looping animation is finished"""
        if not self.loop and self.current_animation in self.animations:
            return self.frame_index >= len(self.animations[self.current_animation]) - 1
        return False


class BuildingInteractionComponent:
    """Handles entity building interactions"""
    
    def __init__(self, entity):
        self.entity = entity
        self.is_inside_building = False
        self.current_building = None
        self.exterior_position = None
        self.can_enter_buildings = True
        self.interaction_range = 50
        
        # Cooldowns and timers
        self.interaction_cooldown = 0
        self.building_timer = 0
        self.max_building_time = 600  # Frames to stay in building
    
    def try_enter_building(self, buildings: List[Any]) -> bool:
        """Try to enter a nearby building"""
        if (not self.can_enter_buildings or self.is_inside_building or 
            self.interaction_cooldown > 0):
            return False
        
        for building in buildings:
            if self._can_enter_building(building):
                self._enter_building(building)
                return True
        return False
    
    def _can_enter_building(self, building) -> bool:
        """Check if entity can enter a specific building"""
        if not hasattr(building, 'can_enter') or not building.can_enter:
            return False
        
        # Check distance
        distance = math.sqrt(
            (self.entity.rect.centerx - building.rect.centerx) ** 2 +
            (self.entity.rect.centery - building.rect.centery) ** 2
        )
        return distance <= self.interaction_range
    
    def _enter_building(self, building):
        """Handle entering a building"""
        # Save exterior position
        self.exterior_position = {
            'x': self.entity.rect.centerx,
            'y': self.entity.rect.centery
        }
        
        # Position in building
        if hasattr(building, 'get_interior_spawn_point'):
            spawn_x, spawn_y = building.get_interior_spawn_point()
            self.entity.rect.centerx = spawn_x
            self.entity.rect.centery = spawn_y
        
        # Update state
        self.is_inside_building = True
        self.current_building = building
        self.building_timer = 0
        self.entity.sync_position()
        
        # Notify building
        if hasattr(building, 'add_entity'):
            building.add_entity(self.entity)
    
    def try_exit_building(self) -> bool:
        """Try to exit current building"""
        if not self.is_inside_building or not self.current_building:
            return False
        
        # Check if near exit
        if hasattr(self.current_building, 'check_exit_range'):
            if self.current_building.check_exit_range(self.entity.rect):
                self._exit_building()
                return True
        
        return False
    
    def _exit_building(self):
        """Handle exiting a building"""
        building_ref = self.current_building
        
        # Restore exterior position
        if self.exterior_position:
            self.entity.rect.centerx = self.exterior_position['x']
            self.entity.rect.centery = self.exterior_position['y']
            self.entity.sync_position()
        
        # Notify building
        if hasattr(building_ref, 'remove_entity'):
            building_ref.remove_entity(self.entity)
        
        # Reset state
        self.is_inside_building = False
        self.current_building = None
        self.exterior_position = None
        self.interaction_cooldown = 60  # Cooldown before re-entering
        self.building_timer = 0
    
    def update(self):
        """Update building interaction state"""
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1
        
        if self.is_inside_building:
            self.building_timer += 1


class BaseEntity(ABC):
    """Base class for all game entities"""
    
    def __init__(self, x: float, y: float, entity_type: EntityType = EntityType.OBJECT):
        # Core attributes
        self.x = x
        self.y = y
        self.entity_type = entity_type
        self.entity_id = id(self)  # Unique identifier
        
        # Visual attributes
        self.image = None
        self.rect = pygame.Rect(x - 16, y - 16, 32, 32)  # Default size
        self.facing_left = False
        self.visible = True
        self.alpha = 255
        
        # State management
        self.state = EntityState.IDLE
        self.previous_state = EntityState.IDLE
        self.active = True
        self.marked_for_deletion = False
        
        # Health and damage (if applicable)
        self.max_health = 100
        self.current_health = 100
        self.invulnerable = False
        
        # Components (initialized by subclasses)
        self.movement = None
        self.animation = None
        self.building_interaction = None
        
        # Collision
        self.solid = True
        self.collision_objects = []
    
    def initialize_components(self, assets: Dict = None, speed: float = 2.0):
        """Initialize entity components (called by subclasses)"""
        # Initialize movement
        self.movement = MovementComponent(self, speed)
        
        # Initialize animation if assets provided
        if assets:
            self.animation = AnimationComponent(self, assets)
            if self.animation.animations:
                self.image = list(assets.values())[0][0]  # First frame of first animation
        
        # Initialize building interaction
        self.building_interaction = BuildingInteractionComponent(self)
    
    def sync_position(self):
        """Synchronize x,y with rect position"""
        self.x = self.rect.centerx
        self.y = self.rect.centery
    
    def set_position(self, x: float, y: float):
        """Set entity position"""
        self.x = x
        self.y = y
        self.rect.centerx = x
        self.rect.centery = y
    
    def get_position(self) -> Tuple[float, float]:
        """Get entity position"""
        return (self.x, self.y)
    
    def set_state(self, new_state: EntityState):
        """Set entity state with animation update"""
        if new_state != self.state:
            self.previous_state = self.state
            self.state = new_state
            
            # Update animation if available
            if self.animation and new_state.value in self.animation.animations:
                self.animation.play_animation(new_state.value)
    
    def get_distance_to(self, other_entity) -> float:
        """Calculate distance to another entity"""
        dx = self.rect.centerx - other_entity.rect.centerx
        dy = self.rect.centery - other_entity.rect.centery
        return math.sqrt(dx * dx + dy * dy)
    
    def get_distance_to_point(self, x: float, y: float) -> float:
        """Calculate distance to a point"""
        dx = self.rect.centerx - x
        dy = self.rect.centery - y
        return math.sqrt(dx * dx + dy * dy)
    
    def is_near(self, other_entity, distance: float = 50) -> bool:
        """Check if entity is near another entity"""
        return self.get_distance_to(other_entity) <= distance
    
    def face_towards(self, target_entity):
        """Face towards another entity"""
        self.facing_left = target_entity.rect.centerx < self.rect.centerx
    
    def face_towards_point(self, x: float, y: float):
        """Face towards a point"""
        self.facing_left = x < self.rect.centerx
    
    def take_damage(self, damage: int):
        """Take damage (if applicable)"""
        if not self.invulnerable:
            self.current_health = max(0, self.current_health - damage)
            if self.current_health <= 0:
                self.on_death()
    
    def heal(self, amount: int):
        """Heal entity"""
        self.current_health = min(self.max_health, self.current_health + amount)
    
    def is_alive(self) -> bool:
        """Check if entity is alive"""
        return self.current_health > 0
    
    def get_collision_objects(self) -> List[Any]:
        """Get objects this entity should collide with"""
        return self.collision_objects
    
    def set_collision_objects(self, objects: List[Any]):
        """Set collision objects"""
        self.collision_objects = objects
    
    def check_collision(self, other_rect: pygame.Rect) -> bool:
        """Check collision with a rectangle"""
        return self.rect.colliderect(other_rect)
    
    def mark_for_deletion(self):
        """Mark entity for deletion"""
        self.marked_for_deletion = True
        self.active = False
    
    @abstractmethod
    def update(self, delta_time: float = 1.0, **kwargs):
        """Update entity (must be implemented by subclasses)"""
        pass
    
    def base_update(self, delta_time: float = 1.0):
        """Base update method called by all entities"""
        # Update components
        if self.movement:
            self.movement.move_towards_target(delta_time)
        
        if self.animation:
            self.animation.update()
        
        if self.building_interaction:
            self.building_interaction.update()
        
        # Sync position
        self.sync_position()
    
    def draw(self, surface: pygame.Surface, camera=None):
        """Draw entity on surface"""
        if not self.visible or not self.image:
            return
        
        # Calculate draw position
        if camera:
            draw_rect = camera.apply(self.rect)
        else:
            draw_rect = self.rect
        
        # Draw image (flipped if facing left)
        if self.facing_left:
            flipped_image = pygame.transform.flip(self.image, True, False)
            if self.alpha < 255:
                flipped_image.set_alpha(self.alpha)
            surface.blit(flipped_image, draw_rect)
        else:
            if self.alpha < 255:
                self.image.set_alpha(self.alpha)
            surface.blit(self.image, draw_rect)
    
    def draw_debug_info(self, surface: pygame.Surface, camera=None, font=None):
        """Draw debug information"""
        if not font:
            return
        
        # Calculate draw position
        if camera:
            draw_rect = camera.apply(self.rect)
        else:
            draw_rect = self.rect
        
        # Draw entity rect
        pygame.draw.rect(surface, (255, 0, 0), draw_rect, 2)
        
        # Draw entity info
        info_text = f"{self.entity_type.value}: {self.state.value}"
        text_surface = font.render(info_text, True, (255, 255, 255))
        surface.blit(text_surface, (draw_rect.x, draw_rect.y - 20))
    
    def on_death(self):
        """Called when entity dies"""
        self.mark_for_deletion()
    
    def get_info(self) -> Dict[str, Any]:
        """Get entity information for debugging"""
        return {
            "id": self.entity_id,
            "type": self.entity_type.value,
            "position": (self.x, self.y),
            "state": self.state.value,
            "health": f"{self.current_health}/{self.max_health}",
            "active": self.active,
            "visible": self.visible,
            "facing_left": self.facing_left,
            "inside_building": (self.building_interaction.is_inside_building 
                              if self.building_interaction else False)
        }
    
    def __str__(self):
        """String representation"""
        return f"{self.entity_type.value}({self.x}, {self.y}) - {self.state.value}"
    
    def __repr__(self):
        """Detailed string representation"""
        return f"{self.__class__.__name__}(id={self.entity_id}, pos=({self.x}, {self.y}), state={self.state.value})"


class EntityManager:
    """Manages collections of entities"""
    
    def __init__(self):
        self.entities: List[BaseEntity] = []
        self.entities_by_type: Dict[EntityType, List[BaseEntity]] = {}
        self.entities_by_id: Dict[int, BaseEntity] = {}
    
    def add_entity(self, entity: BaseEntity):
        """Add entity to manager"""
        if entity not in self.entities:
            self.entities.append(entity)
            
            # Add to type collection
            if entity.entity_type not in self.entities_by_type:
                self.entities_by_type[entity.entity_type] = []
            self.entities_by_type[entity.entity_type].append(entity)
            
            # Add to ID lookup
            self.entities_by_id[entity.entity_id] = entity
    
    def remove_entity(self, entity: BaseEntity):
        """Remove entity from manager"""
        if entity in self.entities:
            self.entities.remove(entity)
            
            # Remove from type collection
            if entity.entity_type in self.entities_by_type:
                if entity in self.entities_by_type[entity.entity_type]:
                    self.entities_by_type[entity.entity_type].remove(entity)
            
            # Remove from ID lookup
            if entity.entity_id in self.entities_by_id:
                del self.entities_by_id[entity.entity_id]
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[BaseEntity]:
        """Get all entities of a specific type"""
        return self.entities_by_type.get(entity_type, [])
    
    def get_entity_by_id(self, entity_id: int) -> Optional[BaseEntity]:
        """Get entity by ID"""
        return self.entities_by_id.get(entity_id)
    
    def update_all(self, delta_time: float = 1.0, **kwargs):
        """Update all entities"""
        # Update entities
        for entity in self.entities[:]:  # Copy list to avoid modification issues
            if entity.active:
                entity.update(delta_time, **kwargs)
        
        # Remove marked entities
        self.cleanup_deleted_entities()
    
    def cleanup_deleted_entities(self):
        """Remove entities marked for deletion"""
        for entity in self.entities[:]:
            if entity.marked_for_deletion:
                self.remove_entity(entity)
    
    def draw_all(self, surface: pygame.Surface, camera=None):
        """Draw all entities"""
        for entity in self.entities:
            if entity.visible:
                entity.draw(surface, camera)
    
    def draw_debug_all(self, surface: pygame.Surface, camera=None, font=None):
        """Draw debug info for all entities"""
        for entity in self.entities:
            entity.draw_debug_info(surface, camera, font)
    
    def get_entities_near_point(self, x: float, y: float, radius: float) -> List[BaseEntity]:
        """Get entities within radius of a point"""
        nearby = []
        for entity in self.entities:
            if entity.get_distance_to_point(x, y) <= radius:
                nearby.append(entity)
        return nearby
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        total_entities = len(self.entities)
        active_entities = sum(1 for e in self.entities if e.active)
        
        type_counts = {}
        for entity_type, entities in self.entities_by_type.items():
            type_counts[entity_type.value] = len(entities)
        
        return {
            "total_entities": total_entities,
            "active_entities": active_entities,
            "entities_by_type": type_counts
        }
    
    def clear_all(self):
        """Clear all entities"""
        self.entities.clear()
        self.entities_by_type.clear()
        self.entities_by_id.clear()