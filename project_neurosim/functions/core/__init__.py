"""
Core game objects and entities.

This module contains the fundamental game objects like players, NPCs,
buildings, camera system, and other core game entities.
"""

from .player import Player
from .camera import Camera
from .building import Building

# Import npc module (not class directly since it might have multiple classes)
from . import npc

__all__ = [
    'Player',
    'Camera', 
    'Building',
    'npc'
]