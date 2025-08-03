"""
Game Settings and Configuration

This file contains all game constants, settings, and configuration values.
Modify these values to adjust game behavior without changing code.
"""

import os
import pygame

# =============================================================================
# GAME INFORMATION
# =============================================================================

GAME_TITLE = "PROJECT NEUROSIM"
VERSION = "0.8.2 Alpha"
DEVELOPER = "Haoran Fang, Angus Shui, Lucas Guo"

# =============================================================================
# DISPLAY SETTINGS
# =============================================================================

# Screen and Display
FULLSCREEN = True
WINDOWED_WIDTH = 1024
WINDOWED_HEIGHT = 768
TARGET_FPS = 60

# Rendering
VSYNC_ENABLED = True
HARDWARE_ACCELERATION = True

# =============================================================================
# WORLD SETTINGS
# =============================================================================

# Map Configuration
MAP_SIZE = 3000  # Size of the game world in pixels
TILE_SIZE = 32   # Size of individual tiles
MAP_CENTER_X = MAP_SIZE // 2
MAP_CENTER_Y = MAP_SIZE // 2

# Background Generation
BACKGROUND_TILE_VARIETY = True  # Use multiple tile types for background
BACKGROUND_SEED = None          # Random seed for background generation (None = random)

# =============================================================================
# PLAYER SETTINGS
# =============================================================================

# Movement
PLAYER_BASE_SPEED = 200        # Base movement speed in pixels/second
PLAYER_RUN_MULTIPLIER = 1.5    # Speed multiplier when running (holding Shift)
PLAYER_DIAGONAL_FACTOR = 0.707 # Movement factor for diagonal movement (√2/2)

# Player Spawn
PLAYER_SPAWN_X = MAP_CENTER_X
PLAYER_SPAWN_Y = MAP_CENTER_Y

# Player Physics
PLAYER_COLLISION_ENABLED = True
PLAYER_SIZE = (32, 32)  # Player collision box size

# =============================================================================
# NPC SETTINGS
# =============================================================================

# NPC Interaction
NPC_INTERACTION_RANGE = 60     # Pixels within which player can interact with NPCs
NPC_DETECTION_RANGE = 100      # Range at which NPCs notice the player
NPC_MOVEMENT_SPEED = 50        # NPC walking speed

# NPC Spawn Positions (relative to map center)
NPC_SPAWN_POSITIONS = [
    {"name": "Dave", "x": MAP_CENTER_X - 80, "y": MAP_CENTER_Y - 80},
    {"name": "Lisa", "x": MAP_CENTER_X + 80, "y": MAP_CENTER_Y - 80},
    {"name": "Tom",  "x": MAP_CENTER_X,      "y": MAP_CENTER_Y + 100}
]

# NPC Hangout Areas
NPC_HANGOUT_AREA = {
    'x': MAP_CENTER_X - 200,
    'y': MAP_CENTER_Y - 200,
    'width': 400,
    'height': 400
}

# Speech Bubbles
NPC_SPEECH_BUBBLE_WIDTH = 300
NPC_SPEECH_BUBBLE_DURATION = 3000  # milliseconds
NPC_SPEECH_BUBBLE_FADE_TIME = 500  # milliseconds

# =============================================================================
# BUILDING SETTINGS
# =============================================================================

# Building Interaction
BUILDING_INTERACTION_RANGE = 80
BUILDING_ENTRY_KEY = pygame.K_e

# Building Positions (relative to map center)
BUILDING_POSITIONS = [
    {"type": "house", "x": MAP_CENTER_X - 150, "y": MAP_CENTER_Y + 150},
    {"type": "shop",  "x": MAP_CENTER_X + 50,  "y": MAP_CENTER_Y + 150}
]

# Building Names for Display
BUILDING_NAMES = {
    "house": "Residential House",
    "shop": "General Store",
    "default": "Building"
}

# Interior Settings
INTERIOR_CENTER_ON_SCREEN = True
INTERIOR_BACKGROUND_COLOR = (40, 40, 60)  # Dark blue-gray

# =============================================================================
# CAMERA SETTINGS
# =============================================================================

# Camera Behavior
CAMERA_SMOOTH_FOLLOW = True
CAMERA_SMOOTHING = 0.05  # Lower = smoother but more lag, Higher = more responsive
CAMERA_DEADZONE = 50     # Pixels of movement before camera starts following

# Camera Bounds
CAMERA_CLAMP_TO_WORLD = True
CAMERA_MARGIN = 100  # Minimum distance from world edges

# =============================================================================
# CHAT SYSTEM SETTINGS
# =============================================================================

# Chat Mechanics
CHAT_COOLDOWN_MS = 2000        # Cooldown between messages in milliseconds
MAX_CHAT_HISTORY = 50          # Maximum number of messages to keep in history
CHAT_INPUT_BLOCK_TIME = 500    # Time to block input after sending message

# Chat Display
CHAT_TYPING_SPEED = 30         # Characters per second for typing animation
CHAT_MAX_RESPONSE_SENTENCES = 4 # Maximum sentences in AI responses
CHAT_MESSAGE_MAX_LENGTH = 200   # Maximum characters per message

# Chat UI
CHAT_BOX_WIDTH = 600
CHAT_BOX_HEIGHT = 400
CHAT_BOX_ALPHA = 180           # Transparency of chat background
CHAT_LINE_SPACING = 2          # Pixels between lines

# =============================================================================
# UI SETTINGS
# =============================================================================

# General UI
UI_SCALE = 1.0                 # Scale factor for UI elements
UI_ANIMATION_SPEED = 300       # UI animation duration in milliseconds

# Colors
UI_PRIMARY_COLOR = (100, 150, 255)    # Main UI color (blue)
UI_SECONDARY_COLOR = (80, 120, 200)   # Secondary UI color (darker blue)
UI_ACCENT_COLOR = (255, 200, 100)     # Accent color (yellow/orange)
UI_TEXT_COLOR = (255, 255, 255)       # Primary text color (white)
UI_TEXT_SECONDARY = (200, 200, 200)   # Secondary text color (light gray)
UI_BACKGROUND_COLOR = (20, 40, 80)    # UI background color (dark blue)
UI_BORDER_COLOR = (100, 150, 255)     # UI border color

# Button Settings
BUTTON_HOVER_BRIGHTNESS = 1.2
BUTTON_PRESS_SCALE = 0.95
BUTTON_BORDER_WIDTH = 2

# =============================================================================
# TIP SYSTEM SETTINGS
# =============================================================================

# Tip Display
TIP_DISPLAY_DURATION = 3000    # Base duration in milliseconds
TIP_FADE_IN_DURATION = 300     # Fade in time
TIP_FADE_OUT_DURATION = 500    # Fade out time

# Tip Timing
TIP_TUTORIAL_AUTO_START = True
TIP_SETTINGS_DELAY = 120000    # Show settings tip after 2 minutes
TIP_DEBUG_DELAY = 300000       # Show debug tip after 5 minutes

# Tip Positioning
TIP_POSITION_Y = 35            # Distance from top of screen
TIP_MAX_WIDTH = 600            # Maximum tip box width
TIP_PADDING = 20               # Padding inside tip box

# Individual Tip Durations (in milliseconds)
TIP_DURATIONS = {
    "movement": 4000,
    "interact_npc": 3000,
    "enter_building": 3000,
    "exit_building": 3000,
    "debug_mode": 2500,
    "settings": 2500,
    "chat_cooldown": 2000,
    "arrows": 3500
}

# =============================================================================
# ARROW SYSTEM SETTINGS
# =============================================================================

# Arrow Behavior
ARROW_MAX_DISTANCE = 2400      # Maximum distance to show arrows
ARROW_MIN_DISTANCE = 200       # Minimum distance for edge arrows
ARROW_LOCK_DISTANCE = 640      # Distance at which arrows lock onto buildings

# Arrow Appearance
ARROW_BASE_SIZE = 20           # Base arrow size in pixels
ARROW_SIZE_MIN_FACTOR = 0.2    # Minimum size factor for distant arrows
ARROW_LOCKED_SIZE_MULTIPLIER = 1.3  # Size multiplier for locked arrows

# Arrow Colors (defined in building colors section above)
ARROW_PULSE_SPEED = 0.005      # Speed of pulsing animation for locked arrows

# Compass Settings
COMPASS_SIZE = 80
COMPASS_POSITION = (20, 20)    # Top-left corner position
COMPASS_ALPHA = 120            # Background transparency

# =============================================================================
# AUDIO SETTINGS
# =============================================================================

# Audio System
AUDIO_ENABLED = True
MASTER_VOLUME = 0.7
MUSIC_VOLUME = 0.5
SFX_VOLUME = 0.8

# Audio Channels
AUDIO_CHANNELS = 8
AUDIO_FREQUENCY = 22050
AUDIO_BUFFER_SIZE = 1024

# =============================================================================
# INPUT SETTINGS
# =============================================================================

# Keyboard Controls
KEY_MOVE_UP = pygame.K_w
KEY_MOVE_DOWN = pygame.K_s
KEY_MOVE_LEFT = pygame.K_a
KEY_MOVE_RIGHT = pygame.K_d
KEY_RUN = pygame.K_LSHIFT
KEY_INTERACT = pygame.K_RETURN
KEY_BUILDING_ENTER = pygame.K_e
KEY_MENU = pygame.K_ESCAPE

# Debug Keys
KEY_DEBUG_HITBOXES = pygame.K_F1
KEY_DEBUG_TUTORIAL = pygame.K_F2
KEY_DEBUG_TIP_MOVEMENT = pygame.K_F3
KEY_DEBUG_TIP_INTERACT = pygame.K_F4
KEY_DEBUG_TIP_BUILDING = pygame.K_F5

# Mouse Settings
MOUSE_INTERACTION_ENABLED = True
MOUSE_SCROLL_SENSITIVITY = 3

# =============================================================================
# DEBUG SETTINGS
# =============================================================================

# Debug Modes
DEBUG_MODE = False
DEBUG_SHOW_HITBOXES = False
DEBUG_SHOW_FPS = False
DEBUG_SHOW_POSITION = False
DEBUG_VERBOSE_LOGGING = False

# Debug Colors
DEBUG_HITBOX_COLOR = (255, 0, 0)      # Red for collision boxes
DEBUG_INTERACTION_COLOR = (0, 255, 0)  # Green for interaction ranges
DEBUG_PATH_COLOR = (255, 255, 0)       # Yellow for movement paths

# Performance Monitoring
PERFORMANCE_MONITORING = False
PERFORMANCE_LOG_INTERVAL = 60000  # Log performance every 60 seconds

# =============================================================================
# FILE PATHS
# =============================================================================

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Asset Directories
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
DATA_DIR = os.path.join(ASSETS_DIR, "data")
ENVIRONMENT_DIR = os.path.join(IMAGES_DIR, "environment")
BUILDINGS_DIR = os.path.join(IMAGES_DIR, "buildings")
CHARACTERS_DIR = os.path.join(IMAGES_DIR, "characters")
FURNITURE_DIR = os.path.join(IMAGES_DIR, "furniture")
PLAYER_DIR = os.path.join(IMAGES_DIR, "player")


# Specific Asset Paths
FONT_PATH = os.path.join(FONTS_DIR, "PressStart2P.ttf")
MAIN_FONT_SIZES = {
    "smallest": 12,
    "small": 18,
    "chat": 14,
    "medium": 24,
    "large": 32,
    "xlarge": 48
}

# Save/Config Files
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
SAVE_DIR = os.path.join(PROJECT_ROOT, "saves")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# =============================================================================
# AI SETTINGS
# =============================================================================

# AI Response Settings
AI_MAX_RESPONSE_LENGTH = 500   # Maximum characters in AI responses
AI_TIMEOUT = 10.0              # Timeout for AI requests in seconds
AI_RETRY_ATTEMPTS = 3          # Number of retry attempts for failed requests

# AI Prompt Settings
AI_SYSTEM_PROMPT_MAX_LENGTH = 1000
AI_CONVERSATION_CONTEXT_LINES = 10  # Number of previous messages to include

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================

# Rendering Optimization
MAX_VISIBLE_NPCS = 20          # Maximum NPCs to render at once
MAX_VISIBLE_BUILDINGS = 50     # Maximum buildings to render at once
CULL_DISTANCE = 1000           # Distance at which objects are culled from rendering

# Update Frequency
NPC_UPDATE_FREQUENCY = 30      # Update NPCs every N milliseconds
PHYSICS_UPDATE_FREQUENCY = 16  # Physics updates every N milliseconds (60 FPS)

# Memory Management
MAX_CACHED_SURFACES = 100      # Maximum number of cached rendering surfaces
GARBAGE_COLLECTION_INTERVAL = 30000  # Force garbage collection every 30 seconds

# =============================================================================
# GAME STATE SETTINGS
# =============================================================================

# Scene Transition
SCENE_TRANSITION_DURATION = 500  # Milliseconds for scene transitions
SCENE_FADE_COLOR = (0, 0, 0)     # Color to fade to during transitions

# Game States
DEFAULT_GAME_STATE = "START_SCREEN"
PAUSE_GAME_ON_FOCUS_LOSS = True

# =============================================================================
# VALIDATION AND DERIVED SETTINGS
# =============================================================================

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [SAVE_DIR, LOG_DIR, CONFIG_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Validate settings
def validate_settings():
    """Validate that settings are within reasonable ranges"""
    assert 30 <= TARGET_FPS <= 120, "FPS should be between 30 and 120"
    assert 0.1 <= PLAYER_RUN_MULTIPLIER <= 3.0, "Run multiplier should be reasonable"
    assert 10 <= NPC_INTERACTION_RANGE <= 200, "Interaction range should be reasonable"
    assert 1000 <= MAP_SIZE <= 10000, "Map size should be reasonable"

# Calculate derived values
SCREEN_CENTER_OFFSET = (MAP_CENTER_X, MAP_CENTER_Y)
DIAGONAL_MOVEMENT_FACTOR = 0.707  # 1/√2 for normalized diagonal movement

# Initialize on import
if __name__ != "__main__":
    ensure_directories()
    validate_settings()

# =============================================================================
# DEVELOPMENT OVERRIDES
# =============================================================================

# Override settings for development/testing
if DEBUG_MODE:
    CHAT_COOLDOWN_MS = 500         # Faster chat for testing
    TIP_DISPLAY_DURATION = 1500    # Shorter tips for testing
    AI_TIMEOUT = 5.0               # Shorter timeout for testing

# =============================================================================
# SETTINGS MENU OPTIONS (for in-game settings menu)
# =============================================================================
SETTINGS_MENU_OPTIONS = [
    {"label": "RETURN TO GAME", "action": "return_to_game"},
    {"label": "SOUND SETTINGS", "action": "toggle_sound"},
    {"label": "VERSION", "action": "show_version"},
    {"label": "RETURN TO TITLE", "action": "return_to_title"},
    {"label": "QUIT GAME", "action": "quit_game"},
]