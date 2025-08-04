import random
from .tilemap import Tile, line

def generate_city(tilemap, x0, y0, w, h, margin=3):
    # fill core
    for x in range(x0, x0+w):
        for y in range(y0, y0+h):
            # distance to nearest city-edge
            d = min(x-x0, x0+w-1-x, y-y0, y0+h-1-y)
            if d < margin:
                blend = d / margin
                tile = Tile.CITY if random.random() < blend else Tile.NATURE
            else:
                tile = Tile.CITY
            tilemap.set_tile(x, y, tile)

def place_buildings(tilemap, buildings):
    # buildings: list of dicts with x0,y0,width,height,door_offset=(dx,dy)
    doors = []
    for b in buildings:
        bx0, by0, bw, bh = b['x0'], b['y0'], b['w'], b['h']
        # mark building as CITY tiles (or a new BUILDING tile)
        for x in range(bx0, bx0+bw):
            for y in range(by0, by0+bh):
                tilemap.set_tile(x, y, Tile.CITY)
        dx, dy = b.get('door_offset', (bw//2, 0))
        door = (bx0 + dx, by0 + dy)
        doors.append(door)
    return doors

def connect_roads(tilemap, doors, spine_y):
    # draw roads from each door down/up to spine_y
    for bx, by in doors:
        for x,y in line(bx, by, bx, spine_y):
            tilemap.set_tile(x, y, Tile.ROAD)

def auto_tile_roads(tilemap, pick_sprite_fn):
    # pick_sprite_fn(bitmask) → sprite
    for x in range(tilemap.width):
        for y in range(tilemap.height):
            if tilemap.get_tile(x,y) != Tile.ROAD:
                continue
            mask = 0
            # N=1, E=2, S=4, W=8
            if y+1 < tilemap.height and tilemap.get_tile(x,y+1)==Tile.ROAD:
                mask |= 1
            if x+1 < tilemap.width and tilemap.get_tile(x+1,y)==Tile.ROAD:
                mask |= 2
            if y-1 >= 0 and tilemap.get_tile(x,y-1)==Tile.ROAD:
                mask |= 4
            if x-1 >= 0 and tilemap.get_tile(x-1,y)==Tile.ROAD:
                mask |= 8
            sprite = pick_sprite_fn(mask)
            # store sprite reference somewhere (e.g. in a parallel sprite grid)
