import pygame


class Camera:
    def __init__(self, width, height, world_width, world_height):
        self.offset = pygame.Vector2(0, 0)
        self.width = width
        self.height = height
        self.world_width = world_width
        self.world_height = world_height
        
        # Optional: Add smoothing for camera movement
        self.smoothing = 0.1  # Lower = smoother, higher = more responsive
        self.target_offset = pygame.Vector2(0, 0)
        self.smooth_follow = False  # Set to True for smooth camera
    
    def follow(self, target):
        ## Make the camera follow a target (usually the player)
        # Calculate where the camera should be centered on the target
        target_x = target.rect.centerx - self.width // 2
        target_y = target.rect.centery - self.height // 2
        
        # Constrain camera offset so it doesn't go past the world boundaries
        constrained_x = max(0, min(target_x, self.world_width - self.width))
        constrained_y = max(0, min(target_y, self.world_height - self.height))
        
        if self.smooth_follow:
            # Smooth camera movement
            self.target_offset.x = constrained_x
            self.target_offset.y = constrained_y
            
            # Interpolate between current and target position
            self.offset.x += (self.target_offset.x - self.offset.x) * self.smoothing
            self.offset.y += (self.target_offset.y - self.offset.y) * self.smoothing
        else:
            # Direct camera movement (your original implementation)
            self.offset.x = constrained_x
            self.offset.y = constrained_y
    
    def apply(self, rect):
        ## Apply camera offset to a rectangle (for drawing objects)
        return rect.move(-self.offset.x, -self.offset.y)
    
    def apply_point(self, point):
        ## Apply camera offset to a point (x, y tuple or Vector2)
        if isinstance(point, pygame.Vector2):
            return point - self.offset
        else:
            return (point[0] - self.offset.x, point[1] - self.offset.y)
    
    def world_to_screen(self, world_pos):
        ## Convert world coordinates to screen coordinates
        return self.apply_point(world_pos)
    
    def screen_to_world(self, screen_pos):
        ## Convert screen coordinates to world coordinates
        if isinstance(screen_pos, pygame.Vector2):
            return screen_pos + self.offset
        else:
            return (screen_pos[0] + self.offset.x, screen_pos[1] + self.offset.y)
    
    def is_visible(self, rect):
        ## Check if a rectangle is visible on screen (for optimization)
        camera_rect = pygame.Rect(self.offset.x, self.offset.y, self.width, self.height)
        return camera_rect.colliderect(rect)
    
    def get_visible_area(self):
        ## Get the rectangle representing the visible area in world coordinates
        return pygame.Rect(self.offset.x, self.offset.y, self.width, self.height)
    
    def set_position(self, x, y):
        ## Manually set camera position (useful for cutscenes or specific positioning)
        self.offset.x = max(0, min(x, self.world_width - self.width))
        self.offset.y = max(0, min(y, self.world_height - self.height))
    
    def shake(self, intensity=5, duration=10):
        ## Add camera shake effect (you'd need to call this in your game loop)
        import random
        shake_x = random.randint(-intensity, intensity)
        shake_y = random.randint(-intensity, intensity)
        
        # Apply shake offset (you'd want to handle the duration in your game loop)
        original_offset = self.offset.copy()
        self.offset.x += shake_x
        self.offset.y += shake_y
        
        # Return original offset so you can restore it after the shake
        return original_offset
