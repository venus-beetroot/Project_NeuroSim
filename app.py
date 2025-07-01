# app.py
import pygame
import os

# --------------------------------------------------------------------------
#                               CONSTANTS
# --------------------------------------------------------------------------
_temp_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = _temp_screen.get_size()
FPS = 60


PLAYER_SPEED = 3
DEFAULT_ENEMY_SPEED = 1

SPAWN_MARGIN = 50

ENEMY_SCALE_FACTOR = 2
PLAYER_SCALE_FACTOR = 2
FLOOR_TILE_SCALE_FACTOR = 2
HEALTH_SCALE_FACTOR = 3


PUSHBACK_DISTANCE = 80
ENEMY_KNOCKBACK_SPEED = 5

# --------------------------------------------------------------------------
#                       ASSET LOADING FUNCTIONS
# --------------------------------------------------------------------------

def load_frames(prefix, frame_count, scale_factor=1, folder="assets"):
    frames = []
    for i in range(frame_count):
        image_path = os.path.join(folder, f"{prefix}_{i}.png")
        img = pygame.image.load(image_path).convert_alpha()

        if scale_factor != 1:
            w = img.get_width() * scale_factor
            h = img.get_height() * scale_factor
            img = pygame.transform.scale(img, (w, h))

        frames.append(img)


    return frames

def load_floor_tiles(folder="assets"):
    floor_tiles = []
    for i in range(8):
        path = os.path.join(folder, f"floor_{i}.png")
        tile = pygame.image.load(path).convert()

        if FLOOR_TILE_SCALE_FACTOR != 1:
            tw = tile.get_width() * FLOOR_TILE_SCALE_FACTOR
            th = tile.get_height() * FLOOR_TILE_SCALE_FACTOR
            tile = pygame.transform.scale(tile, (tw, th))

        floor_tiles.append(tile)
    return floor_tiles

def load_assets():
    assets = {}
    # Player
    assets["player"] = {
        "idle": load_frames("player_idle", 4, scale_factor=PLAYER_SCALE_FACTOR),
        "run":  load_frames("player_run",  4, scale_factor=PLAYER_SCALE_FACTOR),
    }

    # NPC
    assets["npc"] = {
        "idle": load_frames("player_idle", 4, scale_factor=PLAYER_SCALE_FACTOR),
        "run":  load_frames("player_run",  4, scale_factor=PLAYER_SCALE_FACTOR),
    }

    # Floor tiles
    assets["floor_tiles"] = load_floor_tiles()

    # Health images
    assets["health"] = load_frames("health", 6, scale_factor=HEALTH_SCALE_FACTOR)

    # Example coin image (uncomment if you have coin frames / images)
    # assets["coin"] = pygame.image.load(os.path.join("assets", "coin.png")).convert_alpha()

    return assets