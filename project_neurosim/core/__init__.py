"""
Game module containing main game logic and states.

This module handles the core game loop, state management, and coordinates
all game systems.
"""

from .states import GameState
from .game import Game

__all__ = [
    'GameState',
    'Game'
]

# Version info for the game module
__version__ = '1.0.0'