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
PLAYER_SCALE_FACTOR = 2
FLOOR_TILE_SCALE_FACTOR = 2

# --------------------------------------------------------------------------
#                       ASSET LOADING FUNCTIONS
# --------------------------------------------------------------------------


## use for handling animated sprites
def load_frames(prefix, frame_count, scale_factor=1, folders=["assets/images/player", "assets/images/buildings"]):
    if isinstance(folders, str):
        folders = [folders]  # allow single string too

    frames = []

    for i in range(frame_count):
        image_loaded = False
        for folder in folders:
            image_path = os.path.join(folder, f"{prefix}_{i}.png")
            if os.path.exists(image_path):
                img = pygame.image.load(image_path).convert_alpha()
                if scale_factor != 1:
                    w = int(img.get_width() * scale_factor)
                    h = int(img.get_height() * scale_factor)
                    img = pygame.transform.scale(img, (w, h))
                frames.append(img)
                image_loaded = True
                break  # stop checking other folders
        if not image_loaded:
            raise FileNotFoundError(f"Frame {prefix}_{i}.png not found in any provided folders.")

    return frames


## Ussed for rendering images
def load_scaled_image(path, scale_factor=1):
    image = pygame.image.load(path).convert_alpha()
    width, height = image.get_size()
    scaled_image = pygame.transform.scale(image, (int(width * scale_factor), int(height * scale_factor)))
    return scaled_image


def load_floor_tiles(folder="assets/images/environment"):
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

    # building images
    assets["building"] = {
        "shop": load_frames("shop",  1, scale_factor=2),
        "house": load_frames("house", 1,  scale_factor=2),
    }

    # Interior furniture
    assets["interior_furniture"] = {
        "Table": load_scaled_image("assets/images/interiors/Table.png", scale_factor=2),
        "Chair": load_scaled_image("assets/images/interiors/Chair.png", scale_factor=1.5),
    }

    return assets