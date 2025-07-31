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
        
        # Calculate button positions (centered)
        center_x = app.WIDTH // 2
        start_y = app.HEIGHT // 2 + 50
        
        self.buttons = {
            "start": pygame.Rect(center_x - self.button_width//2, start_y, 
                               self.button_width, self.button_height),
            "credits": pygame.Rect(center_x - self.button_width//2, 
                                  start_y + self.button_height + self.button_spacing,
                                  self.button_width, self.button_height),
            "quit": pygame.Rect(center_x - self.button_width//2, 
                              start_y + 2*(self.button_height + self.button_spacing),
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
            "credits": {"scale": 1.0, "glow": 0.0},
            "quit": {"scale": 1.0, "glow": 0.0},
            "settings": {"rotation": 0.0, "glow": 0.0}
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
            
            # Check main buttons
            for button_name, button_rect in self.buttons.items():
                if button_rect.collidepoint(mouse_pos):
                    self.hovered_button = button_name
                    break
            
            # Check settings cog
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
        
        # Check main buttons
        for button_name, button_rect in self.buttons.items():
            if button_rect.collidepoint(mouse_pos):
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
        return button_action  # Return the action to be handled by the game
    
    def draw(self):
        """Draw the complete start screen"""
        # Draw wallpaper
        self.screen.blit(self.wallpaper, (0, 0))
        
        # Draw floating particles
        self._draw_particles()
        
        # Draw title with pulse effect
        self._draw_title()
        
        # Draw subtitle
        self._draw_subtitle()
        
        # Draw menu buttons
        self._draw_buttons()
        
        # Draw settings cog
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
    
    def _draw_buttons(self):
        """Draw menu buttons with smooth animations and gradient effects"""
        button_texts = {
            "start": "START GAME",
            "credits": "CREDITS", 
            "quit": "QUIT GAME"
        }
        
        for button_name, button_rect in self.buttons.items():
            anim = self.button_animations[button_name]
            
            # Determine if this button is loading
            is_loading = self.loading and self.loading_button == button_name
            
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
            
            # Determine button colors
            if is_loading:
                base_color = (60, 120, 60)
                border_color = (100, 255, 100)
                text_color = (200, 255, 200)
            elif self.loading and not is_loading:
                # Disabled during loading
                base_color = (30, 30, 30)
                border_color = (80, 80, 80)
                text_color = (100, 100, 100)
            else:
                # Normal or hovered
                glow_intensity = anim["glow"]
                base_r = int(50 + glow_intensity * 50)
                base_g = int(50 + glow_intensity * 70)
                base_b = int(80 + glow_intensity * 70)
                
                base_color = (base_r, base_g, base_b)
                border_color = (150 + int(glow_intensity * 105), 
                              150 + int(glow_intensity * 105), 
                              150 + int(glow_intensity * 105))
                text_color = (200 + int(glow_intensity * 55), 
                            200 + int(glow_intensity * 55), 
                            200 + int(glow_intensity * 55))
            
            # Draw gradient background
            self._draw_gradient_button(scaled_rect, base_color, anim["glow"])
            
            # Draw border with glow effect
            border_width = 2 + int(anim["glow"] * 2)
            pygame.draw.rect(self.screen, border_color, scaled_rect, border_width)
            
            # Draw glow effect around button
            if anim["glow"] > 0:
                self._draw_button_glow(scaled_rect, border_color, anim["glow"])
            
            # Draw button text with loading animation
            if is_loading:
                # Create loading text with animated dots
                dots = "." * self.loading_dots
                loading_text = f"Loading{dots}"
                text_surf = self.font_small.render(loading_text, True, text_color)
                
                # Add loading progress bar
                self._draw_loading_progress(scaled_rect, base_color)
            else:
                text_surf = self.font_small.render(button_texts[button_name], True, text_color)
            
            text_rect = text_surf.get_rect(center=scaled_rect.center)
            self.screen.blit(text_surf, text_rect)
    
    def _draw_gradient_button(self, rect, base_color, glow_intensity):
        """Draw a button with gradient background"""
        # Create gradient surface
        gradient_surf = pygame.Surface((rect.width, rect.height))
        
        for y in range(rect.height):
            # Create vertical gradient
            progress = y / rect.height
            
            # Darker at top, lighter at bottom
            r = int(base_color[0] * (0.7 + 0.3 * progress))
            g = int(base_color[1] * (0.7 + 0.3 * progress))
            b = int(base_color[2] * (0.7 + 0.3 * progress))
            
            # Add glow effect
            if glow_intensity > 0:
                r = min(255, int(r + glow_intensity * 30))
                g = min(255, int(g + glow_intensity * 30))
                b = min(255, int(b + glow_intensity * 30))
            
            color = (r, g, b)
            pygame.draw.line(gradient_surf, color, (0, y), (rect.width, y))
        
        self.screen.blit(gradient_surf, rect)
    
    def _draw_button_glow(self, rect, color, intensity):
        """Draw glow effect around button"""
        glow_size = int(10 * intensity)
        glow_alpha = int(100 * intensity)
        
        # Create glow surface
        glow_surf = pygame.Surface((rect.width + glow_size * 2, rect.height + glow_size * 2), pygame.SRCALPHA)
        
        # Draw multiple glow layers
        for i in range(glow_size):
            alpha = int(glow_alpha * (1 - i / glow_size))
            glow_color = (*color, alpha)
            glow_rect = pygame.Rect(glow_size - i, glow_size - i, 
                                  rect.width + i * 2, rect.height + i * 2)
            pygame.draw.rect(glow_surf, glow_color, glow_rect, 1)
        
        # Blit glow surface
        glow_pos = (rect.x - glow_size, rect.y - glow_size)
        self.screen.blit(glow_surf, glow_pos)
    
    def _draw_settings_cog(self):
        """Draw animated settings cog in bottom right corner"""
        anim = self.button_animations["settings"]
        
        # Colors based on hover state
        if self.hovered_button == "settings" and not self.loading:
            cog_color = (200, 200, 200)
            bg_color = (80, 80, 80)
        elif self.loading and self.loading_button == "settings":
            cog_color = (100, 255, 100)
            bg_color = (60, 120, 60)
        elif self.loading:
            cog_color = (100, 100, 100)
            bg_color = (40, 40, 40)
        else:
            cog_color = (150, 150, 150)
            bg_color = (60, 60, 60)
        
        center = self.settings_cog.center
        radius = self.settings_cog.width // 2 - 5
        
        # Glow effect
        if anim["glow"] > 0:
            glow_radius = radius + int(8 * anim["glow"])
            glow_alpha = int(40 * anim["glow"])
            glow_surf = pygame.Surface((glow_radius * 2 + 20, glow_radius * 2 + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*cog_color, glow_alpha), 
                             (glow_radius + 10, glow_radius + 10), glow_radius)
            self.screen.blit(glow_surf, (center[0] - glow_radius - 10, center[1] - glow_radius - 10))
        
        # Draw cog shape with better design
        self._draw_improved_cog(center, radius, cog_color, bg_color, anim["rotation"])
    
    def _draw_improved_cog(self, center, radius, cog_color, bg_color, rotation):
        """Draw an improved cog design"""
        # Create surface for the cog
        cog_surf = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
        cog_center = (radius * 3 // 2, radius * 3 // 2)
        
        # Draw outer gear teeth first
        num_teeth = 8
        tooth_angle = 360 / num_teeth
        outer_radius = radius
        inner_radius = radius - 6
        tooth_height = 8
        
        # Create points for the gear shape
        gear_points = []
        
        for i in range(num_teeth):
            # Base angles for this tooth
            base_angle = math.radians(i * tooth_angle + rotation)
            tooth_width = math.radians(tooth_angle * 0.4)  # Tooth takes up 40% of the space
            
            # Inner arc points (between teeth)
            for j in range(3):
                angle = base_angle - tooth_width/2 + (j * tooth_width/2)
                x = cog_center[0] + math.cos(angle) * inner_radius
                y = cog_center[1] + math.sin(angle) * inner_radius
                gear_points.append((x, y))
            
            # Outer tooth points
            tooth_start = base_angle - tooth_width/2
            tooth_end = base_angle + tooth_width/2
            
            # Tooth tip points
            for j in range(3):
                angle = tooth_start + (j * tooth_width/2)
                x = cog_center[0] + math.cos(angle) * (outer_radius + tooth_height)
                y = cog_center[1] + math.sin(angle) * (outer_radius + tooth_height)
                gear_points.append((x, y))
        
        # Simplify: draw using circles and rectangles for cleaner look
        # Draw base circle
        pygame.draw.circle(cog_surf, cog_color, cog_center, outer_radius)
        
        # Draw teeth as rectangles
        for i in range(num_teeth):
            angle = math.radians(i * tooth_angle + rotation)
            
            # Calculate tooth rectangle position
            tooth_center_x = cog_center[0] + math.cos(angle) * (outer_radius + tooth_height//2)
            tooth_center_y = cog_center[1] + math.sin(angle) * (outer_radius + tooth_height//2)
            
            # Create tooth rectangle
            tooth_width = 6
            tooth_rect = pygame.Rect(0, 0, tooth_width, tooth_height)
            tooth_rect.center = (tooth_center_x, tooth_center_y)
            
            # Rotate and draw tooth
            pygame.draw.rect(cog_surf, cog_color, tooth_rect)
        
        # Draw inner circle (hole)
        inner_hole_radius = radius // 2
        pygame.draw.circle(cog_surf, bg_color, cog_center, inner_hole_radius)
        pygame.draw.circle(cog_surf, cog_color, cog_center, inner_hole_radius, 2)
        
        # Add some detail lines
        for i in range(4):
            angle = math.radians(i * 90 + rotation * 0.5)  # Slower rotation for detail
            start_radius = inner_hole_radius + 3
            end_radius = outer_radius - 3
            
            start_x = cog_center[0] + math.cos(angle) * start_radius
            start_y = cog_center[1] + math.sin(angle) * start_radius
            end_x = cog_center[0] + math.cos(angle) * end_radius
            end_y = cog_center[1] + math.sin(angle) * end_radius
            
            pygame.draw.line(cog_surf, bg_color, (start_x, start_y), (end_x, end_y), 1)
        
        # Blit the cog surface to screen
        cog_rect = cog_surf.get_rect(center=center)
        self.screen.blit(cog_surf, cog_rect)
    
    def _draw_loading_progress(self, button_rect, bg_color):
        """Draw loading progress bar inside button"""
        current_time = pygame.time.get_ticks()
        progress = min(1.0, (current_time - self.loading_start_time) / self.loading_duration)
        
        # Progress bar dimensions
        bar_width = button_rect.width - 20
        bar_height = 4
        bar_x = button_rect.x + 10
        bar_y = button_rect.bottom - 15
        
        # Background bar
        pygame.draw.rect(self.screen, (100, 100, 100), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Progress bar
        progress_width = int(bar_width * progress)
        pygame.draw.rect(self.screen, (100, 255, 100), 
                        (bar_x, bar_y, progress_width, bar_height))
    
    def _draw_version_info(self):
        """Draw version information in corner"""
        version_text = "v0.8.2 Alpha - May/June 2025"
        version_surf = pygame.font.Font(None, 24).render(version_text, True, (150, 150, 150))
        version_rect = version_surf.get_rect(bottomleft=(10, app.HEIGHT - 10))
        self.screen.blit(version_surf, version_rect)