"""
Building Arrow System - Directional indicators and compass

This module handles:
- Directional arrows pointing to buildings
- Distance-based arrow sizing and behavior
- Building type identification and coloring
- Compass rendering for navigation
- Screen edge positioning for off-screen buildings
"""

import pygame
import math
from typing import Tuple, Optional, List
from config.settings import (
    ARROW_MAX_DISTANCE, ARROW_MIN_DISTANCE, ARROW_LOCK_DISTANCE,
    BUILDING_NAMES, ARROW_BASE_SIZE, COMPASS_SIZE
)

class BuildingArrowSystem:
    """Manages directional arrows pointing to buildings"""
    
    def __init__(self, font_small, font_chat, font_smallest):
        self.font_small = font_small
        self.font_chat = font_chat
        self.font_smallest = font_smallest
        self.max_distance = 2400  # Maximum distance to show arrows (in pixels)
        self.min_distance = 200   # Minimum distance for edge arrows (reduced from 640)
        self.lock_distance = 640  # Distance at which arrows lock onto buildings
        
        # Building display names
        self.building_names = {
            "house": "Residential House",
            "shop": "General Store"
        }
    
    def calculate_distance(self, pos1, pos2):
        """Calculate distance between two points"""
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
    
    def calculate_angle(self, from_pos, to_pos):
        """Calculate angle from one position to another (in radians)"""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        return math.atan2(dy, dx)
    
    def create_arrow_points(self, center_x, center_y, angle, size):
        """Create arrow points for drawing"""
        # Arrow head points
        head_length = size * 0.8
        head_width = size * 0.5
        
        # Main arrow tip
        tip_x = center_x + math.cos(angle) * head_length
        tip_y = center_y + math.sin(angle) * head_length
        
        # Arrow base corners
        base_angle1 = angle + 2.8  # About 160 degrees
        base_angle2 = angle - 2.8  # About -160 degrees
        
        base1_x = center_x + math.cos(base_angle1) * head_width
        base1_y = center_y + math.sin(base_angle1) * head_width
        
        base2_x = center_x + math.cos(base_angle2) * head_width
        base2_y = center_y + math.sin(base_angle2) * head_width
        
        return [(tip_x, tip_y), (base1_x, base1_y), (base2_x, base2_y)]
    
    def get_screen_edge_position(self, player_screen_pos, building_screen_pos, screen_size, margin=60):
        """Get position for arrow based on where building appears relative to screen"""
        screen_width, screen_height = screen_size
        screen_center_x = screen_width // 2
        screen_center_y = screen_height // 2
        
        # Calculate direction from screen center to building
        dx = building_screen_pos[0] - screen_center_x
        dy = building_screen_pos[1] - screen_center_y
        
        # Normalize direction
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0:
            return None
        
        dx /= length
        dy /= length
        
        # Determine which screen edge to use based on direction
        arrow_x = screen_center_x
        arrow_y = screen_center_y
        
        # Calculate intersection with screen edges
        if abs(dx) > abs(dy):  # More horizontal movement
            if dx > 0:  # Building is to the right
                arrow_x = screen_width - margin
                arrow_y = screen_center_y + (dy / dx) * (screen_width - margin - screen_center_x)
            else:  # Building is to the left
                arrow_x = margin
                arrow_y = screen_center_y + (dy / dx) * (margin - screen_center_x)
        else:  # More vertical movement
            if dy > 0:  # Building is below
                arrow_y = screen_height - margin
                arrow_x = screen_center_x + (dx / dy) * (screen_height - margin - screen_center_y)
            else:  # Building is above
                arrow_y = margin
                arrow_x = screen_center_x + (dx / dy) * (margin - screen_center_y)
        
        # Clamp to screen bounds
        arrow_x = max(margin, min(screen_width - margin, arrow_x))
        arrow_y = max(margin, min(screen_height - margin, arrow_y))
        
        return (int(arrow_x), int(arrow_y))
    
    def get_locked_arrow_position(self, building_screen_pos, screen_size, arrow_size):
        """Get position for locked arrow directly pointing to building on screen"""
        screen_width, screen_height = screen_size
        building_x, building_y = building_screen_pos
        
        # Check if building is visible on screen
        margin = arrow_size + 20  # Ensure arrow doesn't go off screen
        
        # If building is on screen, position arrow slightly offset from building
        if (margin < building_x < screen_width - margin and 
            margin < building_y < screen_height - margin):
            # Position arrow above the building
            return (building_x, building_y - arrow_size - 30)
        
        # If building is off-screen, still lock to its position but clamp to screen edges
        clamped_x = max(margin, min(screen_width - margin, building_x))
        clamped_y = max(margin, min(screen_height - margin, building_y))
        
        return (clamped_x, clamped_y)
    
    def draw_building_arrows(self, surface, player, buildings, camera, building_manager):
        """Draw arrows pointing to all buildings"""
        # Don't show arrows when inside a building
        if building_manager.is_inside_building():
            return
        
        screen_size = (surface.get_width(), surface.get_height())
        screen_center_x = screen_size[0] // 2
        screen_center_y = screen_size[1] // 2
        player_world_pos = (player.rect.centerx, player.rect.centery)
        
        for building in buildings:
            building_world_pos = (building.rect.centerx, building.rect.centery)
            distance = self.calculate_distance(player_world_pos, building_world_pos)
            
            # Skip if too close or too far
            if distance < self.min_distance or distance > self.max_distance:
                continue
            
            # Calculate building position on screen using camera
            building_screen_rect = camera.apply(building.rect)
            building_screen_pos = (building_screen_rect.centerx, building_screen_rect.centery)
            
            # Calculate size based on distance (closer = bigger)
            size_factor = 1.0 - ((distance - self.min_distance) / (self.max_distance - self.min_distance))
            size_factor = max(0.2, min(1.0, size_factor))  # Clamp between 0.2 and 1.0
            
            arrow_size = int(20 * size_factor)  # Base size 20 pixels
            text_size_multiplier = size_factor
            
            # Determine arrow behavior based on distance
            is_locked = distance <= self.lock_distance
            
            if is_locked:
                # Lock onto building - arrow points directly to building position
                arrow_pos = self.get_locked_arrow_position(building_screen_pos, screen_size, arrow_size)
                # Calculate angle from arrow position to building
                angle = self.calculate_angle(arrow_pos, building_screen_pos)
                
                # Make locked arrows more prominent
                arrow_size = int(arrow_size * 1.3)  # 30% bigger when locked
                
            else:
                # Normal behavior - arrow at screen edge
                arrow_pos = self.get_screen_edge_position(
                    (screen_center_x, screen_center_y), building_screen_pos, screen_size
                )
                
                if not arrow_pos:
                    continue
                
                # Calculate angle from screen center to building screen position
                angle = self.calculate_angle((screen_center_x, screen_center_y), building_screen_pos)
            
            # Draw arrow
            arrow_points = self.create_arrow_points(arrow_pos[0], arrow_pos[1], angle, arrow_size)
            
            # Arrow colors based on building type (brighter when locked)
            brightness_multiplier = 1.2 if is_locked else 1.0
            
            if building.building_type == "house":
                base_arrow_color = (100, 150, 255)  # Light blue
                base_outline_color = (50, 100, 200)  # Darker blue
            elif building.building_type == "shop":
                base_arrow_color = (255, 150, 100)  # Light orange
                base_outline_color = (200, 100, 50)  # Darker orange
            else:
                base_arrow_color = (150, 150, 150)  # Gray
                base_outline_color = (100, 100, 100)  # Darker gray
            
            # Apply brightness multiplier for locked arrows
            arrow_color = tuple(min(255, int(c * brightness_multiplier)) for c in base_arrow_color)
            outline_color = tuple(min(255, int(c * brightness_multiplier)) for c in base_outline_color)
            
            # Draw arrow with outline (thicker outline when locked)
            outline_width = 3 if is_locked else 2
            pygame.draw.polygon(surface, outline_color, arrow_points)
            pygame.draw.polygon(surface, arrow_color, arrow_points, 0)
            
            # Add pulsing effect for locked arrows
            if is_locked:
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 0.3 + 0.7
                pulse_color = tuple(int(c * pulse) for c in arrow_color)
                pygame.draw.polygon(surface, pulse_color, arrow_points, 0)
            
            # Convert distance to "tiles" (assuming ~32 pixels per tile)
            distance_in_tiles = int(distance / 32)
            distance_text = f"{distance_in_tiles} tiles"
            building_name = self.building_names.get(building.building_type, building.building_type.title())
            
            # Add "NEARBY" indicator for locked arrows
            if is_locked:
                building_name = f">>> {building_name} <<<"
                distance_text = "NEARBY, Press E to Enter"
            
            # Choose font based on size
            if text_size_multiplier > 0.7:
                font = self.font_chat
            else:
                font = self.font_smallest
            
            # Create text surfaces
            name_surface = font.render(building_name, True, (255, 255, 255))
            distance_surface = font.render(distance_text, True, (200, 200, 200))
            
            # Scale text if very small
            if text_size_multiplier < 0.8 and not is_locked:
                scale_factor = max(0.6, text_size_multiplier)
                original_size = name_surface.get_size()
                new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                name_surface = pygame.transform.scale(name_surface, new_size)
                
                original_size = distance_surface.get_size()
                new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                distance_surface = pygame.transform.scale(distance_surface, new_size)
            
            # Position text near arrow (offset based on arrow direction)
            text_offset_distance = arrow_size + 15
            if is_locked:
                # For locked arrows, position text more prominently
                text_offset_distance = arrow_size + 25
            
            text_offset_x = -math.cos(angle) * text_offset_distance
            text_offset_y = -math.sin(angle) * text_offset_distance
            
            name_x = arrow_pos[0] + text_offset_x - name_surface.get_width() // 2
            name_y = arrow_pos[1] + text_offset_y - name_surface.get_height()
            
            distance_x = arrow_pos[0] + text_offset_x - distance_surface.get_width() // 2
            distance_y = name_y + name_surface.get_height() + 2
            
            # Draw text background for better readability (more prominent for locked)
            bg_alpha = 160 if is_locked else 128
            name_bg_rect = pygame.Rect(name_x - 4, name_y - 2, 
                                     name_surface.get_width() + 8, 
                                     name_surface.get_height() + distance_surface.get_height() + 6)
            
            # Semi-transparent background
            bg_surface = pygame.Surface((name_bg_rect.width, name_bg_rect.height))
            bg_surface.set_alpha(bg_alpha)
            bg_surface.fill((0, 0, 0))
            surface.blit(bg_surface, (name_bg_rect.x, name_bg_rect.y))
            
            # Draw text
            surface.blit(name_surface, (name_x, name_y))
            surface.blit(distance_surface, (distance_x, distance_y))
    
    def draw_compass(self, surface, player_direction=(0, -1)):
        """Draw a small compass at the top-left corner"""
        compass_size = 80
        compass_x = 20
        compass_y = 20
        compass_center = (compass_x + compass_size // 2, compass_y + compass_size // 2)
        
        # Create semi-transparent background
        compass_bg = pygame.Surface((compass_size, compass_size))
        compass_bg.set_alpha(120)
        compass_bg.fill((0, 0, 0))
        surface.blit(compass_bg, (compass_x, compass_y))
        
        # Draw compass circle outline
        pygame.draw.circle(surface, (200, 200, 200), compass_center, compass_size // 2 - 2, 2)
        
        # Draw cardinal directions
        directions = [
            ("N", 0, -1, (255, 100, 100)),  # North - Red
            ("E", 1, 0, (100, 255, 100)),   # East - Green  
            ("S", 0, 1, (100, 100, 255)),   # South - Blue
            ("W", -1, 0, (255, 255, 100))   # West - Yellow
        ]
        
        for label, dx, dy, color in directions:
            # Calculate position for direction label
            label_distance = compass_size // 2 - 15
            label_x = compass_center[0] + dx * label_distance
            label_y = compass_center[1] + dy * label_distance
            
            # Draw direction letter
            font = self.font_chat
            text_surface = font.render(label, True, color)
            text_rect = text_surface.get_rect(center=(label_x, label_y))
            surface.blit(text_surface, text_rect)
        
        # Draw compass needle pointing north
        needle_length = compass_size // 2 - 20
        needle_end_x = compass_center[0] + 0 * needle_length  # Always point north (up)
        needle_end_y = compass_center[1] + -1 * needle_length
        
        # Draw needle (thicker line)
        pygame.draw.line(surface, (255, 50, 50), compass_center, 
                        (needle_end_x, needle_end_y), 3)
        
        # Draw needle tip (small triangle)
        tip_size = 6
        tip_points = [
            (needle_end_x, needle_end_y - tip_size),
            (needle_end_x - tip_size//2, needle_end_y + tip_size//2),
            (needle_end_x + tip_size//2, needle_end_y + tip_size//2)
        ]
        pygame.draw.polygon(surface, (255, 50, 50), tip_points)
        
        # Draw center dot
        pygame.draw.circle(surface, (255, 255, 255), compass_center, 3)