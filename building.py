import pygame

class Building:
    def __init__(self, x, y, building_type, assets):
        self.x = x
        self.y = y
        self.building_type = building_type  # "house" or "shop"
        # Load the building image from assets. We assume the asset is a list of frames.
        self.image = assets["building"][building_type][0]
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface, camera):
        # Apply the camera offset when drawing the building.
        draw_rect = camera.apply(self.rect)
        surface.blit(self.image, draw_rect)