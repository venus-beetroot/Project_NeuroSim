import pygame

def draw_text_box(surface, font, text, center_pos, 
                  text_color=(255, 255, 255), 
                  box_color=(0, 0, 0, 180), 
                  padding_x=10, padding_y=5):
    """
    Draws a semi-transparent text box with centered text on the given surface.

    Parameters:
    - surface: pygame.Surface to draw on
    - font: pygame.font.Font object to render text
    - text: string to display
    - center_pos: (x, y) tuple for the center position of the text box
    - text_color: RGB tuple for text color (default white)
    - box_color: RGBA tuple for box background color (default semi-transparent black)
    - padding_x: horizontal padding around text inside the box
    - padding_y: vertical padding around text inside the box
    """
    text_surf = font.render(text, True, text_color)
    rect = text_surf.get_rect(center=center_pos)
    bg_rect = pygame.Rect(rect.left - padding_x, rect.top - padding_y,
                          rect.width + 2 * padding_x, rect.height + 2 * padding_y)
    
    # Create a surface with per-pixel alpha for transparency
    box_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
    box_surf.fill(box_color)
    
    surface.blit(box_surf, (bg_rect.left, bg_rect.top))
    surface.blit(text_surf, rect)

def draw_centered_text_box(self, text, y_position):
    """Draw a text box centered horizontally at the given y position"""
    # Create text surface
    text_surface = self.font_small.render(text, True, (255, 255, 255))
    text_width = text_surface.get_width()
    text_height = text_surface.get_height()
    
    # Calculate centered position
    screen_width = self.screen.get_width()
    x_position = (screen_width - text_width) // 2
    
    # Draw background box
    padding = 10
    box_rect = pygame.Rect(
        x_position - padding, 
        y_position - padding, 
        text_width + padding * 2, 
        text_height + padding * 2
    )
    
    # Draw semi-transparent background
    background_surface = pygame.Surface((box_rect.width, box_rect.height))
    background_surface.set_alpha(180)  # Semi-transparent
    background_surface.fill((0, 0, 0))  # Black background
    self.screen.blit(background_surface, box_rect.topleft)
    
    # Draw border
    pygame.draw.rect(self.screen, (255, 255, 255), box_rect, 2)
    
    # Draw text
    self.screen.blit(text_surface, (x_position, y_position))