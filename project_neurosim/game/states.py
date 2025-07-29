"""
Game state definitions
"""
from enum import Enum

class GameState(Enum):
    START_SCREEN = "start_screen"
    PLAYING = "playing"
    INTERACTING = "interacting"
    SETTINGS = "settings"