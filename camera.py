import pygame

class Camera:
    def __init__(self, width, height, world_width, world_height):
        self.offset = pygame.Vector2(0, 0)
        self.width = width
        self.height = height
        self.world_width = world_width
        self.world_height = world_height

    def follow(self, target):
        raw_x = target.rect.centerx - self.width // 2
        raw_y = target.rect.centery - self.height // 2
        # Constrain camera offset so it doesn't go past the world boundaries.
        self.offset.x = max(0, min(raw_x, self.world_width - self.width))
        self.offset.y = max(0, min(raw_y, self.world_height - self.height))
    def apply(self, rect):
        # Shift a rect by the camera offset
        return rect.move(-self.offset.x, -self.offset.y)