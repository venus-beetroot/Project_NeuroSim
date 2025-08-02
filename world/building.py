"""
Refactored building.py - now imports and uses the modular components
"""
import pygame
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

# Import the new modular components
from systems.collision_system import CollisionMixin, InteriorWall, CollisionInfo, CollisionSystem
from .interior import InteriorManager, InteriorRenderer, InteriorLayout
from systems.interaction_system import (
    BuildingInteractionSystem, TransitionManager, 
    InteractionZone, PlayerPosition
)
from systems.building_system import Building, BuildingManager, BuildingConfig, create_building_manager

# Re-export everything for backwards compatibility
__all__ = [
    # Core classes
    'Building',
    'BuildingManager', 
    'BuildingConfig',
    
    # Collision system
    'CollisionMixin',
    'InteriorWall',
    'CollisionInfo',
    'CollisionSystem',
    
    # Interior system
    'InteriorManager',
    'InteriorRenderer',
    'InteriorLayout',
    
    # Interaction system
    'BuildingInteractionSystem',
    'TransitionManager',
    'InteractionZone',
    'PlayerPosition',
    
    # Utility functions
    'create_building_manager'
]

# Legacy aliases for backwards compatibility (if needed)
NPCManager = InteriorManager  # InteriorManager now handles NPC management too