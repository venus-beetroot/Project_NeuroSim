"""
Start screen UI and functionality - Updated with cleaner buttons and settings cog
"""
import pygame
import random
import os
import math

from functions import app

class StartScreen:
    """Handles the start screen with wallpaper and menu buttons"""
    
    def __init__(self, screen, font_large, font_small):
        self.screen = screen
        self.font_large = font_large
        self.font_small = font_small
        
        # Create or load wallpaper
        self.wallpaper = self._create_wallpaper()
        
        # Button properties
        self.button_width = 320
        self.button_height = 65
        self.button_spacing = 25
        self.button_corner_radius = 15

        # Map generation menu state
        self.show_map_menu = False
        self.map_menu_buttons = {}
        self._create_map_menu_buttons()
        self.show_saved_maps = False
        self.saved_maps = []
        
        # Calculate button positions (centered)
        center_x = app.WIDTH // 2
        start_y = app.HEIGHT // 2 + 50
        
        self.buttons = {
            "start": pygame.Rect(center_x - self.button_width//2, start_y, 
                            self.button_width, self.button_height),
            "map_gen": pygame.Rect(center_x - self.button_width//2, 
                                start_y + self.button_height + self.button_spacing,
                                self.button_width, self.button_height),
            "credits": pygame.Rect(center_x - self.button_width//2, 
                                start_y + 2*(self.button_height + self.button_spacing),
                                self.button_width, self.button_height),
            "quit": pygame.Rect(center_x - self.button_width//2, 
                            start_y + 3*(self.button_height + self.button_spacing),
                            self.button_width, self.button_height)
        }
        
        # Settings cog button (bottom right corner)
        cog_size = 50
        self.settings_cog = pygame.Rect(
            app.WIDTH - cog_size - 30, 
            app.HEIGHT - cog_size - 30, 
            cog_size, 
            cog_size
        )
        
        # Button hover states and animations
        self.hovered_button = None
        self.button_animations = {
            "start": {"scale": 1.0, "glow": 0.0},
            "map_gen": {"scale": 1.0, "glow": 0.0},  # Add this line
            "credits": {"scale": 1.0, "glow": 0.0},
            "quit": {"scale": 1.0, "glow": 0.0},
            "settings": {"rotation": 0.0, "glow": 0.0},
            # Map menu buttons
            "random": {"scale": 1.0, "glow": 0.0},
            "load": {"scale": 1.0, "glow": 0.0},
            "blank": {"scale": 1.0, "glow": 0.0},
            "back": {"scale": 1.0, "glow": 0.0},
            "back_to_main": {"scale": 1.0, "glow": 0.0}
        }
        
        # Loading animation variables
        self.loading = False
        self.loading_button = None
        self.loading_start_time = 0
        self.loading_duration = 1500  # 1.5 seconds
        self.loading_dots = 0
        self.loading_dot_timer = 0
        
        # Animation variables
        self.title_pulse = 0
        self.particle_timer = 0
        self.particles = []
    
    def _create_wallpaper(self):
        """Load wallpaper from assets folder with fallback"""
        try:
            # Try to load wallpaper from assets
            wallpaper_path = os.path.join("assets", "images", "loadingscr.png")
            wallpaper = pygame.image.load(wallpaper_path)
            
            # Scale to fit screen while maintaining aspect ratio
            wallpaper = self._scale_wallpaper_to_fit(wallpaper)
            
            print(f"Loaded wallpaper from: {wallpaper_path}")
            return wallpaper
            
        except (pygame.error, FileNotFoundError) as e:
            print(f"Could not load loadingscr.png from assets folder: {e}")
            print("Generating fallback wallpaper...")
            return self._create_fallback_wallpaper()
    
    def _scale_wallpaper_to_fit(self, wallpaper):
        """Scale wallpaper to fit screen while maintaining aspect ratio"""
        wallpaper_width, wallpaper_height = wallpaper.get_size()
        screen_width, screen_height = app.WIDTH, app.HEIGHT
        
        # Calculate scaling factors
        scale_x = screen_width / wallpaper_width
        scale_y = screen_height / wallpaper_height
        
        # Use the larger scale to ensure full coverage
        scale = max(scale_x, scale_y)
        
        # Calculate new dimensions
        new_width = int(wallpaper_width * scale)
        new_height = int(wallpaper_height * scale)
        
        # Scale the wallpaper
        scaled_wallpaper = pygame.transform.scale(wallpaper, (new_width, new_height))
        
        # Create a surface for the final wallpaper
        final_wallpaper = pygame.Surface((screen_width, screen_height))
        
        # Center the scaled wallpaper
        x_offset = (screen_width - new_width) // 2
        y_offset = (screen_height - new_height) // 2
        
        final_wallpaper.blit(scaled_wallpaper, (x_offset, y_offset))
        
        return final_wallpaper
    
    def _create_fallback_wallpaper(self):
        """Create a fallback wallpaper when PNG is not available"""
        wallpaper = pygame.Surface((app.WIDTH, app.HEIGHT))
        
        # Create a gradient background
        for y in range(app.HEIGHT):
            # Create a nice gradient from dark blue to lighter blue
            progress = y / app.HEIGHT
            r = int(20 + (60 * progress))
            g = int(30 + (80 * progress))
            b = int(80 + (120 * progress))
            color = (min(255, r), min(255, g), min(255, b))
            pygame.draw.line(wallpaper, color, (0, y), (app.WIDTH, y))
        
        # Add some decorative elements (optional)
        self._add_decorative_elements(wallpaper)
        
        return wallpaper
    
    def _add_decorative_elements(self, surface):
        """Add decorative elements to the wallpaper"""
        # Add some semi-transparent circles for atmosphere
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        
        for _ in range(20):
            x = random.randint(0, app.WIDTH)
            y = random.randint(0, app.HEIGHT)
            radius = random.randint(30, 100)
            alpha = random.randint(10, 30)
            color = (255, 255, 255, alpha)
            
            # Create a temporary surface for the circle
            circle_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, color, (radius, radius), radius)
            overlay.blit(circle_surf, (x-radius, y-radius))
        
        surface.blit(overlay, (0, 0))
    
    def update(self, mouse_pos):
        """Update start screen animations and hover states"""
        # Update title pulse animation
        self.title_pulse += 0.1
        
        # Update loading animation
        if self.loading:
            current_time = pygame.time.get_ticks()
            
            # Update loading dots animation
            self.loading_dot_timer += 1
            if self.loading_dot_timer > 20:  # Change dots every 20 frames
                self.loading_dot_timer = 0
                self.loading_dots = (self.loading_dots + 1) % 4
            
            # Check if loading is complete
            if current_time - self.loading_start_time > self.loading_duration:
                return self._finish_loading()
        
        # Only update hover state if not loading
        if not self.loading:
            self.hovered_button = None
            
            if self.show_map_menu:
                # Check map menu buttons
                for button_name, button_rect in self.map_menu_buttons.items():
                    if button_rect.collidepoint(mouse_pos):
                        self.hovered_button = button_name
                        break
            else:
                # Check main buttons
                for button_name, button_rect in self.buttons.items():
                    if button_rect.collidepoint(mouse_pos):
                        self.hovered_button = button_name
                        break
            
            # Check settings cog (always visible)
            if self.settings_cog.collidepoint(mouse_pos):
                self.hovered_button = "settings"
        
        # Update button animations
        self._update_button_animations()
        
        # Update floating particles
        self.particle_timer += 1
        if self.particle_timer > 30:  # Add new particle every 30 frames
            self.particle_timer = 0
            self.particles.append({
                'x': random.randint(0, app.WIDTH),
                'y': app.HEIGHT + 10,
                'speed': random.uniform(0.5, 2.0),
                'size': random.randint(2, 5),
                'alpha': random.randint(100, 200)
            })
        
        # Update existing particles
        for particle in self.particles[:]:
            particle['y'] -= particle['speed']
            particle['alpha'] -= 1
            if particle['alpha'] <= 0 or particle['y'] < -10:
                self.particles.remove(particle)
    
    def _update_button_animations(self):
        """Update smooth button animations"""
        animation_speed = 0.15
        
        for button_name in self.button_animations:
            anim = self.button_animations[button_name]
            
            if self.hovered_button == button_name and not self.loading:
                # Animate to hover state
                if button_name == "settings":
                    anim["rotation"] = min(anim["rotation"] + 3, 360)
                    if anim["rotation"] >= 360:
                        anim["rotation"] = 0
                    anim["glow"] = min(anim["glow"] + animation_speed, 1.0)
                else:
                    anim["scale"] = min(anim["scale"] + animation_speed * 0.5, 1.05)
                    anim["glow"] = min(anim["glow"] + animation_speed, 1.0)
            else:
                # Animate to normal state
                if button_name == "settings":
                    anim["glow"] = max(anim["glow"] - animation_speed, 0.0)
                else:
                    anim["scale"] = max(anim["scale"] - animation_speed * 0.5, 1.0)
                    anim["glow"] = max(anim["glow"] - animation_speed, 0.0)
    
    def handle_click(self, mouse_pos):
        """Handle mouse clicks on buttons"""
        # Don't handle clicks if already loading
        if self.loading:
            return None
        
        if self.show_map_menu:
            # Handle map menu clicks
            for button_name, button_rect in self.map_menu_buttons.items():
                if button_rect.collidepoint(mouse_pos):
                    if button_name == "back":
                        self.show_map_menu = False
                        return None
                    elif button_name == "load":
                        self.show_saved_maps = True
                        self._create_map_menu_buttons()  # Recreate buttons for saved maps view
                        return None
                    elif button_name == "back_to_main":
                        self.show_saved_maps = False
                        self.show_map_menu = False
                        return None
                    elif button_name.startswith("map_"):
                        # Extract map number and load it
                        map_number = int(button_name.split('_')[1])
                        self.start_loading(button_name)
                        return ("map_gen", "load", map_number)  # Return tuple with map number
                    else:
                        # Regular map generation options
                        self.start_loading(button_name)
                        return ("map_gen", button_name)
            
        else:
            # Check main buttons
            for button_name, button_rect in self.buttons.items():
                if button_rect.collidepoint(mouse_pos):
                    if button_name == "map_gen":
                        self.show_map_menu = True
                        return None
                    else:
                        # Start loading animation
                        self.start_loading(button_name)
                        return None  # Don't return the action immediately
        
        # Check settings cog
        if self.settings_cog.collidepoint(mouse_pos):
            self.start_loading("settings")
            return None
        
        return None
    
    def start_loading(self, button_name):
        """Start the loading animation for a button"""
        self.loading = True
        self.loading_button = button_name
        self.loading_start_time = pygame.time.get_ticks()
        self.loading_dots = 0
        self.loading_dot_timer = 0

    def _finish_loading(self):
        """Finish loading and return the button action"""
        button_action = self.loading_button
        self.loading = False
        self.loading_button = None
        
        # Handle map generation actions
        if button_action in ["random", "load", "blank"]:
            return ("map_gen", button_action)
        
        return button_action  # Return the action to be handled by the game
    
    def draw(self):
        """Draw the complete start screen"""
        # Draw wallpaper
        self.screen.blit(self.wallpaper, (0, 0))
        
        # Draw floating particles
        self._draw_particles()

        # Only draw main title and subtitle when not in map menu
        if not self.show_map_menu:
            # Draw title with pulse effect
            self._draw_title()
            
            # Draw subtitle
            self._draw_subtitle()
        
        if self.show_map_menu:
            # Draw map generation menu
            self._draw_map_menu_title()
            self._draw_map_menu_buttons()
        else:
            # Draw main menu buttons
            self._draw_buttons()
        
        # Draw settings cog (always visible)
        self._draw_settings_cog()
        
        # Draw version info
        self._draw_version_info()
    
    def _draw_particles(self):
        """Draw floating particles for atmosphere"""
        for particle in self.particles:
            color = (255, 255, 255, particle['alpha'])
            # Create a small surface for the particle
            particle_surf = pygame.Surface((particle['size']*2, particle['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, color, (particle['size'], particle['size']), particle['size'])
            self.screen.blit(particle_surf, (particle['x']-particle['size'], particle['y']-particle['size']))
    
    def _draw_title(self):
        """Draw the main game title with pulse effect"""
        title_text = "PROJECT NEUROSIM"
        
        # Create pulse effect
        pulse_scale = 1.0 + 0.1 * math.sin(self.title_pulse)
        
        # Create title surface
        title_surf = self.font_large.render(title_text, True, (255, 255, 255))
        
        # Scale the title
        scaled_width = int(title_surf.get_width() * pulse_scale)
        scaled_height = int(title_surf.get_height() * pulse_scale)
        scaled_title = pygame.transform.scale(title_surf, (scaled_width, scaled_height))
        
        # Center and draw
        title_rect = scaled_title.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 150))
        
        # Add glow effect
        glow_surf = pygame.transform.scale(scaled_title, (scaled_width + 10, scaled_height + 10))
        glow_surf.set_alpha(50)
        glow_rect = glow_surf.get_rect(center=title_rect.center)
        self.screen.blit(glow_surf, glow_rect)
        
        # Draw main title
        self.screen.blit(scaled_title, title_rect)
    
    def _draw_subtitle(self):
        """Draw subtitle text"""
        subtitle_text = "A Neural Simulation Adventure"
        subtitle_surf = self.font_small.render(subtitle_text, True, (200, 200, 200))
        subtitle_rect = subtitle_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 100))
        self.screen.blit(subtitle_surf, subtitle_rect)
    
    def _draw_icon(self, surface, icon_type, rect, color, is_loading=False):
        """Draw icons for buttons"""
        icon_size = 18
        icon_x = rect.x + 25
        icon_y = rect.centery
        
        if is_loading:
            # Loading spinner - rotating circle with gap
            center_x, center_y = icon_x + icon_size//2, icon_y
            radius = icon_size//2 - 2
            
            # Calculate rotation for spinner
            current_time = pygame.time.get_ticks()
            rotation = (current_time * 0.3) % 360  # Rotation speed
            
            # Draw spinner arc (3/4 of a circle)
            start_angle = rotation
            end_angle = rotation + 270  # 3/4 circle
            
            # Draw the spinner arc using small lines
            arc_points = []
            for angle in range(int(start_angle), int(end_angle), 5):
                rad = math.radians(angle)
                x = center_x + math.cos(rad) * radius
                y = center_y + math.sin(rad) * radius
                arc_points.append((x, y))
            
            if len(arc_points) > 1:
                pygame.draw.lines(surface, color, False, arc_points, 3)
            
            return
        
        if icon_type == "start":
            # Play arrow/triangle
            points = [
                (icon_x, icon_y - icon_size//2),
                (icon_x, icon_y + icon_size//2),
                (icon_x + icon_size, icon_y)
            ]
            pygame.draw.polygon(surface, color, points)
            
        elif icon_type == "credits":
            # Star shape
            center_x, center_y = icon_x + icon_size//2, icon_y
            outer_radius = icon_size//2
            inner_radius = icon_size//4
            points = []
            
            for i in range(10):  # 5-pointed star = 10 points
                angle = math.radians(i * 36 - 90)  # Start from top
                if i % 2 == 0:  # Outer points
                    radius = outer_radius
                else:  # Inner points
                    radius = inner_radius
                x = center_x + math.cos(angle) * radius
                y = center_y + math.sin(angle) * radius
                points.append((x, y))
            
            pygame.draw.polygon(surface, color, points)
            
        elif icon_type == "quit":
            # X shape
            line_width = 3
            offset = icon_size//3
            
            # Draw X with two lines
            pygame.draw.line(surface, color, 
                           (icon_x + offset, icon_y - offset), 
                           (icon_x + icon_size - offset, icon_y + offset), 
                           line_width)
            pygame.draw.line(surface, color, 
                           (icon_x + offset, icon_y + offset), 
                           (icon_x + icon_size - offset, icon_y - offset), 
                           line_width)
    
    def _draw_floral_decoration(self, surface, rect, color, alpha=100):
        """Draw floral decorations on button corners"""
        decoration_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Corner decorations
        corner_size = 12
        petal_size = 6
        
        corners = [
            (corner_size, corner_size),  # Top-left
            (rect.width - corner_size, corner_size),  # Top-right
            (corner_size, rect.height - corner_size),  # Bottom-left
            (rect.width - corner_size, rect.height - corner_size)  # Bottom-right
        ]
        
        for corner_x, corner_y in corners:
            # Draw small floral pattern
            center = (corner_x, corner_y)
            
            # Draw petals around center
            for i in range(4):
                angle = math.radians(i * 90)
                petal_x = corner_x + math.cos(angle) * petal_size
                petal_y = corner_y + math.sin(angle) * petal_size
                
                # Draw petal as small circle
                petal_color = (*color, alpha)
                petal_surf = pygame.Surface((petal_size*2, petal_size*2), pygame.SRCALPHA)
                pygame.draw.circle(petal_surf, petal_color, (petal_size, petal_size), petal_size//2)
                decoration_surf.blit(petal_surf, (petal_x - petal_size, petal_y - petal_size))
            
            # Center dot
            center_color = (*color, alpha + 50)
            pygame.draw.circle(decoration_surf, center_color, center, 2)
        
        # Edge decorations (small dots along the border)
        dot_spacing = 20
        dot_size = 2
        
        # Top and bottom edges
        for x in range(dot_spacing, rect.width - dot_spacing, dot_spacing):
            dot_color = (*color, alpha//2)
            # Top edge
            pygame.draw.circle(decoration_surf, dot_color, (x, 5), dot_size)
            # Bottom edge
            pygame.draw.circle(decoration_surf, dot_color, (x, rect.height - 5), dot_size)
        
        # Left and right edges
        for y in range(dot_spacing, rect.height - dot_spacing, dot_spacing):
            dot_color = (*color, alpha//2)
            # Left edge
            pygame.draw.circle(decoration_surf, dot_color, (5, y), dot_size)
            # Right edge
            pygame.draw.circle(decoration_surf, dot_color, (rect.width - 5, y), dot_size)
        
        surface.blit(decoration_surf, (0, 0))
    
    def _draw_rounded_rect(self, surface, color, rect, corner_radius):
        """Draw a rounded rectangle"""
        # Draw main rectangle
        main_rect = pygame.Rect(rect.x, rect.y + corner_radius, rect.width, rect.height - 2*corner_radius)
        pygame.draw.rect(surface, color, main_rect)
        
        # Draw top and bottom rectangles
        top_rect = pygame.Rect(rect.x + corner_radius, rect.y, rect.width - 2*corner_radius, corner_radius)
        bottom_rect = pygame.Rect(rect.x + corner_radius, rect.bottom - corner_radius, rect.width - 2*corner_radius, corner_radius)
        pygame.draw.rect(surface, color, top_rect)
        pygame.draw.rect(surface, color, bottom_rect)
        
        # Draw corner circles
        pygame.draw.circle(surface, color, (rect.x + corner_radius, rect.y + corner_radius), corner_radius)
        pygame.draw.circle(surface, color, (rect.right - corner_radius, rect.y + corner_radius), corner_radius)
        pygame.draw.circle(surface, color, (rect.x + corner_radius, rect.bottom - corner_radius), corner_radius)
        pygame.draw.circle(surface, color, (rect.right - corner_radius, rect.bottom - corner_radius), corner_radius)
    
    def _draw_buttons(self):
        """Draw menu buttons with enhanced styling"""
        button_texts = {
            "start": "START GAME",
            "map_gen": "MAP GENERATION",
            "credits": "CREDITS", 
            "quit": "QUIT GAME"
        }

        button_icons = {
            "start": "start",
            "map_gen": "map",
            "credits": "credits",
            "quit": "quit"
        }
        
        for button_name, button_rect in self.buttons.items():
            anim = self.button_animations[button_name]
            
            # Determine if this button is loading
            is_loading = self.loading and self.loading_button == button_name
            is_hovered = self.hovered_button == button_name and not self.loading
            
            # Calculate scaled rect
            scale = anim["scale"]
            scaled_width = int(button_rect.width * scale)
            scaled_height = int(button_rect.height * scale)
            scaled_rect = pygame.Rect(
                button_rect.centerx - scaled_width // 2,
                button_rect.centery - scaled_height // 2,
                scaled_width,
                scaled_height
            )
            
            # Define color schemes
            if is_loading:
                # Inverted colors for loading state
                bg_color1 = (220, 240, 220)  # Light green
                bg_color2 = (180, 220, 180)  # Darker light green
                border_color = (100, 200, 100)
                text_color = (40, 80, 40)  # Dark green text
                icon_color = (40, 80, 40)
                decoration_color = (100, 150, 100)
            elif is_hovered:
                # Enhanced colors for hover
                bg_color1 = (25, 35, 55)    # Dark blue-gray
                bg_color2 = (15, 25, 45)    # Darker blue-gray
                border_color = (120, 180, 255)  # Bright blue
                text_color = (220, 240, 255)    # Light blue-white
                icon_color = (120, 180, 255)
                decoration_color = (80, 140, 200)
            elif self.loading and not is_loading:
                # Disabled during loading
                bg_color1 = (20, 20, 25)
                bg_color2 = (15, 15, 20)
                border_color = (60, 60, 70)
                text_color = (80, 80, 90)
                icon_color = (60, 60, 70)
                decoration_color = (40, 40, 50)
            else:
                # Normal state - dark background with complementary colors
                bg_color1 = (30, 25, 45)    # Dark purple-gray
                bg_color2 = (20, 15, 35)    # Darker purple-gray
                border_color = (100, 120, 160)  # Muted blue
                text_color = (200, 220, 255)    # Light blue-white
                icon_color = (150, 170, 200)
                decoration_color = (70, 85, 120)
            
            # Create button surface for rounded corners
            button_surf = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
            
            # Draw gradient background with rounded corners
            self._draw_gradient_rounded_button(button_surf, bg_color1, bg_color2, scaled_rect.size, self.button_corner_radius)
            
            # Add floral decorations
            self._draw_floral_decoration(button_surf, pygame.Rect(0, 0, scaled_rect.width, scaled_rect.height), 
                                       decoration_color, alpha=60 + int(anim["glow"] * 40))
            
            # Draw border with rounded corners
            border_width = 2 + int(anim["glow"] * 2)
            self._draw_rounded_rect_border(button_surf, border_color, 
                                         pygame.Rect(0, 0, scaled_rect.width, scaled_rect.height),
                                         self.button_corner_radius, border_width)
            
            # Blit button surface to screen
            self.screen.blit(button_surf, scaled_rect)
            
            # Draw glow effect around button
            if anim["glow"] > 0:
                self._draw_button_glow(scaled_rect, border_color, anim["glow"])
            
            # Draw icon
            is_loading_this_button = is_loading
            self._draw_icon(self.screen, button_icons[button_name], scaled_rect, icon_color, is_loading_this_button)
            
            # Draw button text with loading animation
            if is_loading:
                # Create loading text with animated dots
                dots = "." * self.loading_dots
                loading_text = f"Loading{dots}"
                text_surf = self.font_small.render(loading_text, True, text_color)
                
                # Add loading progress bar
                self._draw_loading_progress(scaled_rect, bg_color1)
            else:
                text_surf = self.font_small.render(button_texts[button_name], True, text_color)
            
            # Adjust text position to account for icon
            text_rect = text_surf.get_rect()
            text_rect.centerx = scaled_rect.centerx + 15  # Offset for icon
            text_rect.centery = scaled_rect.centery
            self.screen.blit(text_surf, text_rect)
    
    def _draw_gradient_rounded_button(self, surface, color1, color2, size, corner_radius):
        """Draw a rounded button with gradient background"""
        width, height = size
        
        for y in range(height):
            # Create vertical gradient
            progress = y / height
            
            # Interpolate between colors
            r = int(color1[0] * (1 - progress) + color2[0] * progress)
            g = int(color1[1] * (1 - progress) + color2[1] * progress)
            b = int(color1[2] * (1 - progress) + color2[2] * progress)
            color = (r, g, b)
            
            # Draw line with rounded corners consideration
            if y < corner_radius:
                # Top rounded section
                line_width = self._get_rounded_line_width(y, corner_radius, width)
                line_start = (width - line_width) // 2
                if line_width > 0:
                    pygame.draw.line(surface, color, (line_start, y), (line_start + line_width, y))
            elif y >= height - corner_radius:
                # Bottom rounded section
                dist_from_bottom = height - y - 1
                line_width = self._get_rounded_line_width(dist_from_bottom, corner_radius, width)
                line_start = (width - line_width) // 2
                if line_width > 0:
                    pygame.draw.line(surface, color, (line_start, y), (line_start + line_width, y))
            else:
                # Middle section - full width
                pygame.draw.line(surface, color, (0, y), (width, y))
    
    def _get_rounded_line_width(self, distance_from_edge, corner_radius, full_width):
        """Calculate line width for rounded corners"""
        if distance_from_edge >= corner_radius:
            return full_width
        
        # Use circle equation to determine width
        y_offset = corner_radius - distance_from_edge
        if y_offset >= corner_radius:
            return 0
        
        # Calculate how much of the circle width we have at this y position
        circle_width = 2 * math.sqrt(corner_radius * corner_radius - y_offset * y_offset)
        return int(full_width - 2 * corner_radius + circle_width)
    
    def _draw_rounded_rect_border(self, surface, color, rect, corner_radius, border_width):
        """Draw border for rounded rectangle"""
        # Draw border as multiple rounded rectangles with decreasing size
        for i in range(border_width):
            border_rect = pygame.Rect(
                rect.x + i, 
                rect.y + i, 
                rect.width - 2*i, 
                rect.height - 2*i
            )
            
            if border_rect.width <= 0 or border_rect.height <= 0:
                break
                
            # Draw border outline (not filled)
            self._draw_rounded_rect_outline(surface, color, border_rect, max(1, corner_radius - i))
    
    def _draw_rounded_rect_outline(self, surface, color, rect, corner_radius):
        """Draw outline of rounded rectangle"""
        # Draw the four sides
        # Top
        pygame.draw.line(surface, color, 
                        (rect.x + corner_radius, rect.y), 
                        (rect.right - corner_radius, rect.y))
        # Bottom
        pygame.draw.line(surface, color, 
                        (rect.x + corner_radius, rect.bottom - 1), 
                        (rect.right - corner_radius, rect.bottom - 1))
        # Left
        pygame.draw.line(surface, color, 
                        (rect.x, rect.y + corner_radius), 
                        (rect.x, rect.bottom - corner_radius))
        # Right
        pygame.draw.line(surface, color, 
                        (rect.right - 1, rect.y + corner_radius), 
                        (rect.right - 1, rect.bottom - corner_radius))
        
        # Draw corner arcs (approximated with small lines)
        self._draw_corner_arc(surface, color, rect.x + corner_radius, rect.y + corner_radius, corner_radius, 180, 270)
        self._draw_corner_arc(surface, color, rect.right - corner_radius, rect.y + corner_radius, corner_radius, 270, 360)
        self._draw_corner_arc(surface, color, rect.x + corner_radius, rect.bottom - corner_radius, corner_radius, 90, 180)
        self._draw_corner_arc(surface, color, rect.right - corner_radius, rect.bottom - corner_radius, corner_radius, 0, 90)
    
    def _draw_corner_arc(self, surface, color, center_x, center_y, radius, start_angle, end_angle):
        """Draw a corner arc"""
        points = []
        for angle in range(int(start_angle), int(end_angle) + 1, 2):
            rad = math.radians(angle)
            x = center_x + math.cos(rad) * radius
            y = center_y + math.sin(rad) * radius
            points.append((int(x), int(y)))
        
        if len(points) > 1:
            pygame.draw.lines(surface, color, False, points)
    
    def _draw_button_glow(self, rect, color, intensity):
        """Draw glow effect around button"""
        glow_size = int(12 * intensity)
        glow_alpha = int(80 * intensity)
        
        # Create glow surface
        glow_surf = pygame.Surface((rect.width + glow_size * 2, rect.height + glow_size * 2), pygame.SRCALPHA)
        
        # Draw multiple glow layers
        for i in range(glow_size):
            alpha = int(glow_alpha * (1 - i / glow_size))
            glow_color = (*color, alpha)
            
            glow_rect = pygame.Rect(glow_size - i, glow_size - i, 
                                  rect.width + i * 2, rect.height + i * 2)
            
            # Draw rounded glow
            self._draw_rounded_rect(glow_surf, glow_color, glow_rect, self.button_corner_radius + i)
        
        # Blit glow surface
        glow_pos = (rect.x - glow_size, rect.y - glow_size)
        self.screen.blit(glow_surf, glow_pos)
    
    def _draw_settings_cog(self):
        """Draw animated settings cog with rounded background"""
        anim = self.button_animations["settings"]
        
        # Determine if this button is loading
        is_loading = self.loading and self.loading_button == "settings"
        is_hovered = self.hovered_button == "settings" and not self.loading
        
        # Define color schemes similar to main buttons
        if is_loading:
            # Inverted colors for loading state
            bg_color1 = (220, 240, 220)  # Light green
            bg_color2 = (180, 220, 180)  # Darker light green
            border_color = (100, 200, 100)
            cog_color = (40, 80, 40)  # Dark green
            decoration_color = (100, 150, 100)
        elif is_hovered:
            # Enhanced colors for hover
            bg_color1 = (25, 35, 55)    # Dark blue-gray
            bg_color2 = (15, 25, 45)    # Darker blue-gray
            border_color = (120, 180, 255)  # Bright blue
            cog_color = (220, 240, 255)    # Light blue-white
            decoration_color = (80, 140, 200)
        elif self.loading:
            # Disabled during loading
            bg_color1 = (20, 20, 25)
            bg_color2 = (15, 15, 20)
            border_color = (60, 60, 70)
            cog_color = (80, 80, 90)
            decoration_color = (40, 40, 50)
        else:
            # Normal state - dark background with complementary colors
            bg_color1 = (30, 25, 45)    # Dark purple-gray
            bg_color2 = (20, 15, 35)    # Darker purple-gray
            border_color = (100, 120, 160)  # Muted blue
            cog_color = (200, 220, 255)    # Light blue-white
            decoration_color = (70, 85, 120)
        
        # Create settings button surface for rounded corners
        settings_surf = pygame.Surface((self.settings_cog.width, self.settings_cog.height), pygame.SRCALPHA)
        
        # Draw gradient background with rounded corners
        corner_radius = 12
        self._draw_gradient_rounded_button(settings_surf, bg_color1, bg_color2, 
                                         (self.settings_cog.width, self.settings_cog.height), corner_radius)
        
        # Add floral decorations
        self._draw_floral_decoration(settings_surf, 
                                   pygame.Rect(0, 0, self.settings_cog.width, self.settings_cog.height), 
                                   decoration_color, alpha=60 + int(anim["glow"] * 40))
        
        # Draw border with rounded corners
        border_width = 2 + int(anim["glow"] * 2)
        self._draw_rounded_rect_border(settings_surf, border_color, 
                                     pygame.Rect(0, 0, self.settings_cog.width, self.settings_cog.height),
                                     corner_radius, border_width)
        
        # Blit settings surface to screen
        self.screen.blit(settings_surf, self.settings_cog)
        
        # Draw glow effect around settings button
        if anim["glow"] > 0:
            self._draw_button_glow(self.settings_cog, border_color, anim["glow"])
        
        # Draw the cog icon in the center
        center = self.settings_cog.center
        cog_radius = 15  # Smaller radius for cleaner look
        
        if is_loading:
            # Draw loading spinner instead of cog
            self._draw_loading_spinner(center, cog_radius, cog_color)
        else:
            # Draw improved cog design
            self._draw_improved_cog(center, cog_radius, cog_color, anim["rotation"])
    
    def _draw_loading_spinner(self, center, radius, color):
        """Draw a loading spinner for the settings button"""
        current_time = pygame.time.get_ticks()
        rotation = (current_time * 0.5) % 360  # Rotation speed
        
        # Draw spinner arc (3/4 of a circle)
        start_angle = rotation
        end_angle = rotation + 270  # 3/4 circle
        
        # Draw the spinner arc using small lines
        arc_points = []
        for angle in range(int(start_angle), int(end_angle), 8):
            rad = math.radians(angle)
            x = center[0] + math.cos(rad) * radius
            y = center[1] + math.sin(rad) * radius
            arc_points.append((x, y))
        
        if len(arc_points) > 1:
            pygame.draw.lines(self.screen, color, False, arc_points, 4)
    
    def _draw_improved_cog(self, center, radius, cog_color, rotation):
        """Draw an improved, cleaner and rounder cog design"""
        # Create surface for the cog
        cog_surf = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
        cog_center = (radius * 3 // 2, radius * 3 // 2)
        
        # Cog parameters
        num_teeth = 8
        tooth_angle = 360 / num_teeth
        outer_radius = radius
        inner_radius = radius - 4
        tooth_height = 5
        
        # Draw base circle with anti-aliasing effect
        pygame.draw.circle(cog_surf, cog_color, cog_center, outer_radius)
        
        # Draw teeth as rounded rectangles
        for i in range(num_teeth):
            angle = math.radians(i * tooth_angle + rotation)
            
            # Calculate tooth position
            tooth_distance = outer_radius + tooth_height // 2
            tooth_x = cog_center[0] + math.cos(angle) * tooth_distance
            tooth_y = cog_center[1] + math.sin(angle) * tooth_distance
            
            # Draw tooth as a small rounded rectangle
            tooth_width = 4
            tooth_rect = pygame.Rect(0, 0, tooth_width, tooth_height)
            tooth_rect.center = (tooth_x, tooth_y)
            
            # Create small rounded tooth
            tooth_surf = pygame.Surface((tooth_width + 2, tooth_height + 2), pygame.SRCALPHA)
            pygame.draw.rect(tooth_surf, cog_color, 
                           pygame.Rect(1, 1, tooth_width, tooth_height), 
                           border_radius=2)
            
            cog_surf.blit(tooth_surf, (tooth_rect.x - 1, tooth_rect.y - 1))
        
        # Draw inner circle (hole) with better proportions
        inner_hole_radius = radius // 3
        pygame.draw.circle(cog_surf, (0, 0, 0, 0), cog_center, inner_hole_radius)  # Transparent hole
        pygame.draw.circle(cog_surf, cog_color, cog_center, inner_hole_radius, 2)  # Border
        
        # Add subtle detail spokes
        spoke_length = inner_hole_radius + 2
        for i in range(4):
            angle = math.radians(i * 90 + rotation * 0.3)  # Slower rotation for spokes
            
            start_x = cog_center[0] + math.cos(angle) * (inner_hole_radius + 1)
            start_y = cog_center[1] + math.sin(angle) * (inner_hole_radius + 1)
            end_x = cog_center[0] + math.cos(angle) * spoke_length
            end_y = cog_center[1] + math.sin(angle) * spoke_length
            
            pygame.draw.line(cog_surf, cog_color, (start_x, start_y), (end_x, end_y), 1)
        
        # Add center dot for more detail
        pygame.draw.circle(cog_surf, cog_color, cog_center, 2)
        
        # Blit the cog surface to screen
        cog_rect = cog_surf.get_rect(center=center)
        self.screen.blit(cog_surf, cog_rect)
    
    def _draw_loading_progress(self, button_rect, bg_color):
        """Draw loading progress bar inside button"""
        current_time = pygame.time.get_ticks()
        progress = min(1.0, (current_time - self.loading_start_time) / self.loading_duration)
        
        # Progress bar dimensions
        bar_width = button_rect.width - 40
        bar_height = 4
        bar_x = button_rect.x + 20
        bar_y = button_rect.bottom - 15
        
        # Background bar with rounded corners
        bg_bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (60, 60, 60), bg_bar_rect, border_radius=2)
        
        # Progress bar with rounded corners
        progress_width = int(bar_width * progress)
        if progress_width > 0:
            progress_rect = pygame.Rect(bar_x, bar_y, progress_width, bar_height)
            pygame.draw.rect(self.screen, (100, 255, 100), progress_rect, border_radius=2)
    
    def _draw_version_info(self):
        """Draw version information in corner"""
        version_text = "v0.8.2 Alpha - May/June 2025"
        version_surf = pygame.font.Font(None, 24).render(version_text, True, (150, 150, 150))
        version_rect = version_surf.get_rect(bottomleft=(10, app.HEIGHT - 10))
        self.screen.blit(version_surf, version_rect)

    def _create_map_menu_buttons(self):
        """Create buttons for map generation menu"""
        center_x = app.WIDTH // 2
        start_y = app.HEIGHT // 2 + 50  # Move down from -50 to +50
        
        if not hasattr(self, 'show_saved_maps') or not self.show_saved_maps:
            # Main map menu
            self.map_menu_buttons = {
                "random": pygame.Rect(center_x - self.button_width//2, start_y, 
                                    self.button_width, self.button_height),
                "load": pygame.Rect(center_x - self.button_width//2, 
                                start_y + self.button_height + self.button_spacing,
                                self.button_width, self.button_height),
                "blank": pygame.Rect(center_x - self.button_width//2, 
                                    start_y + 2*(self.button_height + self.button_spacing),
                                    self.button_width, self.button_height),
                "back": pygame.Rect(center_x - self.button_width//2, 
                                start_y + 3*(self.button_height + self.button_spacing),
                                self.button_width, self.button_height)
            }
        else:
            # Instead of calling _get_saved_maps() every frame
            if not hasattr(self, '_maps_loaded'):
                self.saved_maps = self._get_saved_maps()
                self._maps_loaded = True
            self.map_menu_buttons = {}
            
            # Show up to 6 saved maps + back button
            visible_maps = self.saved_maps[:6]
            for i, map_data in enumerate(visible_maps):
                button_key = f"map_{map_data['map_number']}"
                self.map_menu_buttons[button_key] = pygame.Rect(
                    center_x - self.button_width//2,
                    start_y + i * (self.button_height + self.button_spacing),
                    self.button_width,
                    self.button_height
                )
            
            # Back button
            back_y = start_y + len(visible_maps) * (self.button_height + self.button_spacing)
            self.map_menu_buttons["back_to_main"] = pygame.Rect(
                center_x - self.button_width//2,
                back_y,
                self.button_width,
                self.button_height
            )
            # Initialize animations for dynamically created map buttons
            for button_key in self.map_menu_buttons.keys():
                if button_key not in self.button_animations:
                    self.button_animations[button_key] = {"scale": 1.0, "glow": 0.0}

    def _get_saved_maps(self):
        """Get list of saved maps from saves folder"""
        import os
        import json
        
        # Add loop detection
        if hasattr(self, '_getting_saves') and self._getting_saves:
            print("DEBUG: Preventing infinite loop in _get_saved_maps")
            return getattr(self, '_cached_saved_maps', [])
        
        self._getting_saves = True
        
        saves_dir = "saves"
        print(f"DEBUG: _get_saved_maps called once")
        saved_maps = []
        
        if os.path.exists(saves_dir):
            for filename in os.listdir(saves_dir):
                if filename.endswith(".json"):
                    try:
                        filepath = os.path.join(saves_dir, filename)
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        
                        # Extract map info
                        metadata = data.get('metadata', {})
                        map_info = data.get('map_info', {})
                        
                        saved_maps.append({
                            'filename': filename,
                            'map_number': metadata.get('map_number', 0),
                            'save_time': metadata.get('save_time', 'Unknown'),
                            'generation_mode': metadata.get('generation_mode', 'Unknown'),
                            'size': f"{map_info.get('width', 0)}x{map_info.get('height', 0)}"
                        })
                    except Exception as e:
                        print(f"Error reading save file {filename}: {e}")
                        continue
        
        def safe_map_number(x):
            map_num = x['map_number']
            if isinstance(map_num, int):
                return map_num
            elif isinstance(map_num, str) and map_num.isdigit():
                return int(map_num)
            else:
                return 999999  # Put 'Unknown' maps at the end

        sorted_maps = sorted(saved_maps, key=safe_map_number)
        self._cached_saved_maps = sorted_maps
        self._getting_saves = False
        
        return sorted_maps

    def _draw_map_menu_title(self):
        """Draw map generation menu title"""
        title_text = "MAP GENERATION"
        title_surf = self.font_small.render(title_text, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 150))
        self.screen.blit(title_surf, title_rect)
        
        subtitle_text = "Choose how to generate your world"
        subtitle_surf = pygame.font.Font(None, 28).render(subtitle_text, True, (200, 200, 200))
        subtitle_rect = subtitle_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 120))
        self.screen.blit(subtitle_surf, subtitle_rect)

    def _draw_map_menu_buttons(self):
        """Draw map generation menu buttons"""
        if hasattr(self, 'show_saved_maps') and self.show_saved_maps:
            # Draw saved maps selection
            self._draw_saved_maps_buttons()  # Call the actual button drawing
            return
        
        # Regular map menu buttons code...
        button_texts = {
            "random": "RANDOM MAP",
            "load": "LOAD SAVED MAP", 
            "blank": "BLANK MAP",
            "back": "BACK TO MAIN"
        }
        
        for button_name, button_rect in self.map_menu_buttons.items():
            anim = self.button_animations[button_name]
            
            # Determine if this button is loading
            is_loading = self.loading and self.loading_button == button_name
            is_hovered = self.hovered_button == button_name and not self.loading
            
            # Calculate scaled rect
            scale = anim["scale"]
            scaled_width = int(button_rect.width * scale)
            scaled_height = int(button_rect.height * scale)
            scaled_rect = pygame.Rect(
                button_rect.centerx - scaled_width // 2,
                button_rect.centery - scaled_height // 2,
                scaled_width,
                scaled_height
            )
            
            # Use same color scheme as main buttons
            if is_loading:
                bg_color1 = (220, 240, 220)
                bg_color2 = (180, 220, 180)
                border_color = (100, 200, 100)
                text_color = (40, 80, 40)
                icon_color = (40, 80, 40)
                decoration_color = (100, 150, 100)
            elif is_hovered:
                bg_color1 = (25, 35, 55)
                bg_color2 = (15, 25, 45)
                border_color = (120, 180, 255)
                text_color = (220, 240, 255)
                icon_color = (120, 180, 255)
                decoration_color = (80, 140, 200)
            else:
                bg_color1 = (30, 25, 45)
                bg_color2 = (20, 15, 35)
                border_color = (100, 120, 160)
                text_color = (200, 220, 255)
                icon_color = (150, 170, 200)
                decoration_color = (70, 85, 120)
            
            # Create button surface for rounded corners
            button_surf = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
            
            # Draw gradient background with rounded corners
            self._draw_gradient_rounded_button(button_surf, bg_color1, bg_color2, scaled_rect.size, self.button_corner_radius)
            
            # Add floral decorations
            self._draw_floral_decoration(button_surf, pygame.Rect(0, 0, scaled_rect.width, scaled_rect.height), 
                                    decoration_color, alpha=60 + int(anim["glow"] * 40))
            
            # Draw border with rounded corners
            border_width = 2 + int(anim["glow"] * 2)
            self._draw_rounded_rect_border(button_surf, border_color, 
                                        pygame.Rect(0, 0, scaled_rect.width, scaled_rect.height),
                                        self.button_corner_radius, border_width)
            
            # Blit button surface to screen
            self.screen.blit(button_surf, scaled_rect)
            
            # Draw glow effect around button
            if anim["glow"] > 0:
                self._draw_button_glow(scaled_rect, border_color, anim["glow"])
            
            # Draw icon (customize for map menu)
            self._draw_map_icon(scaled_rect, button_name, icon_color, is_loading)
            
            # Handle saved map buttons differently
            if hasattr(self, 'show_saved_maps') and self.show_saved_maps:
                # Draw saved map buttons
                for i, (button_name, button_rect) in enumerate(self.map_menu_buttons.items()):
                    if button_name == "back_to_main":
                        # Draw back button normally
                        text_to_show = "BACK TO MENU"
                        icon_to_show = "back"
                    elif button_name.startswith("map_"):
                        # Draw saved map button
                        map_num = button_name.split('_')[1]
                        map_data = next((m for m in self.saved_maps if str(m['map_number']) == map_num), None)
                        if map_data:
                            text_to_show = f"MAP #{map_data['map_number']} ({map_data['size']})"
                            icon_to_show = "load"
                        else:
                            continue
                    else:
                        continue
                        
                    # [Draw the button using existing drawing code but with text_to_show and icon_to_show]
                    # ... (use existing button drawing code here)
                return  # Exit early for saved maps view

            # Draw button text
            if is_loading:
                dots = "." * self.loading_dots
                loading_text = f"Loading{dots}"
                text_surf = self.font_small.render(loading_text, True, text_color)
                self._draw_loading_progress(scaled_rect, bg_color1)
            else:
                text_surf = self.font_small.render(button_texts[button_name], True, text_color)
            
            # Adjust text position to account for icon
            text_rect = text_surf.get_rect()
            text_rect.centerx = scaled_rect.centerx + 15
            text_rect.centery = scaled_rect.centery
            self.screen.blit(text_surf, text_rect)

    def _draw_map_icon(self, rect, icon_type, color, is_loading):
        """Draw icons specific to map menu"""
        if is_loading:
            self._draw_icon(self.screen, "loading", rect, color, True)
            return
        
        icon_size = 18
        icon_x = rect.x + 25
        icon_y = rect.centery
        
        if icon_type == "random":
            # Dice-like pattern
            center_x, center_y = icon_x + icon_size//2, icon_y
            # Draw square
            square_size = icon_size - 4
            square_rect = pygame.Rect(center_x - square_size//2, center_y - square_size//2, square_size, square_size)
            pygame.draw.rect(self.screen, color, square_rect, 2)
            # Draw dots
            dot_size = 2
            pygame.draw.circle(self.screen, color, (center_x - 3, center_y - 3), dot_size)
            pygame.draw.circle(self.screen, color, (center_x + 3, center_y + 3), dot_size)
            pygame.draw.circle(self.screen, color, (center_x, center_y), dot_size)
            
        elif icon_type == "load":
            # Folder icon
            folder_width = icon_size - 2
            folder_height = icon_size - 4
            folder_rect = pygame.Rect(icon_x, icon_y - folder_height//2, folder_width, folder_height)
            pygame.draw.rect(self.screen, color, folder_rect, 2)
            # Folder tab
            tab_rect = pygame.Rect(icon_x, icon_y - folder_height//2 - 3, folder_width//2, 3)
            pygame.draw.rect(self.screen, color, tab_rect)

        elif icon_type == "map":
            # Map/grid icon
            center_x, center_y = icon_x + icon_size//2, icon_y
            # Draw grid pattern
            grid_size = icon_size - 4
            start_x = center_x - grid_size//2
            start_y = center_y - grid_size//2
            
            # Vertical lines
            for i in range(4):
                x = start_x + (grid_size * i // 3)
                pygame.draw.line(self.screen, color, (x, start_y), (x, start_y + grid_size), 2)
            
            # Horizontal lines  
            for i in range(4):
                y = start_y + (grid_size * i // 3)
                pygame.draw.line(self.screen, color, (start_x, y), (start_x + grid_size, y), 2)
            
        elif icon_type == "blank":
            # Empty rectangle
            blank_rect = pygame.Rect(icon_x + 2, icon_y - icon_size//2 + 2, icon_size - 4, icon_size - 4)
            pygame.draw.rect(self.screen, color, blank_rect, 2)
            
        elif icon_type == "back":
            # Left arrow
            arrow_points = [
                (icon_x + icon_size - 2, icon_y - icon_size//3),
                (icon_x + 2, icon_y),
                (icon_x + icon_size - 2, icon_y + icon_size//3)
            ]
            pygame.draw.lines(self.screen, color, False, arrow_points, 3)

    def _draw_saved_maps_menu(self):
        """Draw the saved maps selection menu"""
        if not hasattr(self, '_maps_loaded'):
            self.saved_maps = self._get_saved_maps()
            self._maps_loaded = True
        
        if not self.saved_maps:
            # No saved maps found
            no_maps_text = "No saved maps found"
            text_surf = self.font_small.render(no_maps_text, True, (255, 100, 100))
            text_rect = text_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2))
            self.screen.blit(text_surf, text_rect)
            return
        
        # Draw saved map buttons
        visible_maps = self.saved_maps[:6]  # Show up to 6 maps
        
        for i, map_data in enumerate(visible_maps):
            button_key = f"map_{map_data['map_number']}"
            button_rect = self.map_menu_buttons.get(button_key)
            
            if button_rect:
                # Create display text for saved map
                map_text = f"MAP #{map_data['map_number']} ({map_data['size']})"
                self._draw_single_map_button(button_rect, map_text, "load", button_key)
        
        # Draw back button
        back_button = self.map_menu_buttons.get("back_to_main")
        if back_button:
            self._draw_single_map_button(back_button, "BACK TO MENU", "back", "back_to_main")

    def _draw_single_map_button(self, button_rect, text, icon_type, button_name):
        """Draw a single map menu button with proper styling"""
        anim = self.button_animations.get(button_name, {"scale": 1.0, "glow": 0.0})
        
        # Determine if this button is loading
        is_loading = self.loading and self.loading_button == button_name
        is_hovered = self.hovered_button == button_name and not self.loading
        
        # Calculate scaled rect
        scale = anim["scale"]
        scaled_width = int(button_rect.width * scale)
        scaled_height = int(button_rect.height * scale)
        scaled_rect = pygame.Rect(
            button_rect.centerx - scaled_width // 2,
            button_rect.centery - scaled_height // 2,
            scaled_width,
            scaled_height
        )
        
        # Color scheme (same as other buttons)
        if is_loading:
            bg_color1 = (220, 240, 220)
            bg_color2 = (180, 220, 180)
            border_color = (100, 200, 100)
            text_color = (40, 80, 40)
            icon_color = (40, 80, 40)
            decoration_color = (100, 150, 100)
        elif is_hovered:
            bg_color1 = (25, 35, 55)
            bg_color2 = (15, 25, 45)
            border_color = (120, 180, 255)
            text_color = (220, 240, 255)
            icon_color = (120, 180, 255)
            decoration_color = (80, 140, 200)
        else:
            bg_color1 = (30, 25, 45)
            bg_color2 = (20, 15, 35)
            border_color = (100, 120, 160)
            text_color = (200, 220, 255)
            icon_color = (150, 170, 200)
            decoration_color = (70, 85, 120)
        
        # Create button surface for rounded corners
        button_surf = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
        
        # Draw gradient background with rounded corners
        self._draw_gradient_rounded_button(button_surf, bg_color1, bg_color2, scaled_rect.size, self.button_corner_radius)
        
        # Add floral decorations
        self._draw_floral_decoration(button_surf, pygame.Rect(0, 0, scaled_rect.width, scaled_rect.height), 
                                decoration_color, alpha=60 + int(anim["glow"] * 40))
        
        # Draw border with rounded corners
        border_width = 2 + int(anim["glow"] * 2)
        self._draw_rounded_rect_border(button_surf, border_color, 
                                    pygame.Rect(0, 0, scaled_rect.width, scaled_rect.height),
                                    self.button_corner_radius, border_width)
        
        # Blit button surface to screen
        self.screen.blit(button_surf, scaled_rect)
        
        # Draw glow effect around button
        if anim["glow"] > 0:
            self._draw_button_glow(scaled_rect, border_color, anim["glow"])
        
        # Draw icon
        self._draw_map_icon(scaled_rect, icon_type, icon_color, is_loading)
        
        # Draw button text
        if is_loading:
            dots = "." * self.loading_dots
            loading_text = f"Loading{dots}"
            text_surf = self.font_small.render(loading_text, True, text_color)
            self._draw_loading_progress(scaled_rect, bg_color1)
        else:
            text_surf = self.font_small.render(text, True, text_color)
        
        # Adjust text position to account for icon
        text_rect = text_surf.get_rect()
        text_rect.centerx = scaled_rect.centerx + 15
        text_rect.centery = scaled_rect.centery
        self.screen.blit(text_surf, text_rect)

    def _draw_saved_maps_buttons(self):
        """Draw saved maps as clickable buttons"""
        if not hasattr(self, '_maps_loaded'):
            self.saved_maps = self._get_saved_maps()
            self._maps_loaded = True
        
        if not self.saved_maps:
            # No saved maps - just draw back button
            back_button = self.map_menu_buttons.get("back_to_main")
            if back_button:
                self._draw_single_map_button(back_button, "BACK TO MENU", "back", "back_to_main")
            return
        
        # Draw each saved map button
        for button_key, button_rect in self.map_menu_buttons.items():
            if button_key == "back_to_main":
                self._draw_single_map_button(button_rect, "BACK TO MENU", "back", button_key)
            elif button_key.startswith("map_"):
                # Find the corresponding map data
                map_num = int(button_key.split('_')[1])
                map_data = next((m for m in self.saved_maps if m['map_number'] == map_num), None)
                
                if map_data:
                    map_text = f"MAP #{map_data['map_number']} ({map_data['size']})"
                    self._draw_single_map_button(button_rect, map_text, "load", button_key)