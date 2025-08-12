# import pygame
# from world.tilemap       import TileMap, Tile
# from world.city_generator import generate_city, place_buildings, connect_roads, auto_tile_roads
# import assets

# def main():
#     W, H, TS = 100, 60, 16
#     tm = TileMap(W, H)
#     generate_city(tm, 5, 5, 80, 40, margin=4)
#     buildings = [
#         {'x0':20,'y0':20,'w':6,'h':4,'door_offset':(3,0)},
#         # … more…
#     ]
#     doors = place_buildings(tm, buildings)
#     connect_roads(tm, doors, spine_y=25)
#     auto_tile_roads(tm, assets)

#     pygame.init()
#     surf = pygame.Surface((W*TS, H*TS))
#     for x in range(W):
#         for y in range(H):
#             tile = tm.get_tile(x,y)
#             img  = TILE_IMAGE_MAP[tile]  # preload these
#             surf.blit(img, (x*TS, (H-1-y)*TS))
#     pygame.image.save(surf, "map_debug.png")
#     print("Saved map_debug.png")

# if __name__ == "__main__":
#     main()
