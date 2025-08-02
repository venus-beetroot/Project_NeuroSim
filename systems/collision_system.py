"""
Collision detection and resolution system for buildings and interior walls
"""
import pygame
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple


@dataclass
class CollisionInfo:
    """Data class for collision information"""
    overlap_x: float
    overlap_y: float
    from_left: bool
    from_top: bool


class CollisionMixin:
    """Mixin class providing collision detection and resolution"""
    
    def check_collision(self, other_rect: pygame.Rect) -> bool:
        """Check if another rectangle collides with this object's hitbox"""
        return self.hitbox.colliderect(other_rect)
    
    def get_collision_info(self, other_rect: pygame.Rect) -> Optional[CollisionInfo]:
        """Get detailed collision information for collision resolution"""
        if not self.check_collision(other_rect):
            return None
        
        overlap_x = min(other_rect.right - self.hitbox.left, 
                       self.hitbox.right - other_rect.left)
        overlap_y = min(other_rect.bottom - self.hitbox.top, 
                       self.hitbox.bottom - other_rect.top)
        
        return CollisionInfo(
            overlap_x=overlap_x,
            overlap_y=overlap_y,
            from_left=other_rect.centerx < self.hitbox.centerx,
            from_top=other_rect.centery < self.hitbox.centery
        )
    
    def resolve_collision(self, other_rect: pygame.Rect) -> pygame.Rect:
        """Resolve collision by pushing the other rect out of this object"""
        collision_info = self.get_collision_info(other_rect)
        if not collision_info:
            return other_rect
        
        resolved_rect = other_rect.copy()
        
        # Push out along the axis with smallest overlap
        if collision_info.overlap_x < collision_info.overlap_y:
            # Push horizontally
            if collision_info.from_left:
                resolved_rect.right = self.hitbox.left
            else:
                resolved_rect.left = self.hitbox.right
        else:
            # Push vertically
            if collision_info.from_top:
                resolved_rect.bottom = self.hitbox.top
            else:
                resolved_rect.top = self.hitbox.bottom
        
        return resolved_rect


class InteriorWall(CollisionMixin):
    """Represents a wall inside a building with collision detection"""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.hitbox = self.rect  # For compatibility with collision system
        self.is_solid = True
        self.can_enter = False
    
    def update_position(self, x: int, y: int):
        """Update wall position"""
        self.rect.topleft = (x, y)
        self.hitbox = self.rect


class CollisionSystem:
    """System for managing and checking collisions"""
    
    def __init__(self):
        self.collision_objects: List[CollisionMixin] = []
    
    def add_collision_object(self, obj: CollisionMixin):
        """Add an object to the collision system"""
        if obj not in self.collision_objects and hasattr(obj, 'hitbox'):
            self.collision_objects.append(obj)
    
    def remove_collision_object(self, obj: CollisionMixin):
        """Remove an object from the collision system"""
        if obj in self.collision_objects:
            self.collision_objects.remove(obj)
    
    def check_collisions(self, rect: pygame.Rect) -> List[CollisionMixin]:
        """Check collisions against all registered objects"""
        colliding_objects = []
        for obj in self.collision_objects:
            if obj.check_collision(rect):
                colliding_objects.append(obj)
        return colliding_objects
    
    def resolve_all_collisions(self, rect: pygame.Rect) -> pygame.Rect:
        """Resolve collisions with all objects and return adjusted rect"""
        resolved_rect = rect.copy()
        
        for obj in self.collision_objects:
            if obj.check_collision(resolved_rect):
                resolved_rect = obj.resolve_collision(resolved_rect)
        
        return resolved_rect
    
    def clear(self):
        """Clear all collision objects"""
        self.collision_objects.clear()
    
    def get_collision_count(self) -> int:
        """Get the number of collision objects"""
        return len(self.collision_objects)