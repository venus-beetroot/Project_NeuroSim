"""
Start screen UI and functionality
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
        self.button_width = 300
        self.button_height = 60
        self.button_spacing = 20
        
        # Calculate button positions (centered)
        center_x = app.WIDTH // 2
        start_y = app.HEIGHT // 2 + 50
        
        self.buttons = {
            "start": pygame.Rect(center_x - self.button_width//2, start_y, 
                               self.button_width, self.button_height),
            "settings": pygame.Rect(center_x - self.button_width//2, 
                                  start_y + self.button_height + self.button_spacing,
                                  self.button_width, self.button_height),
            "quit": pygame.Rect(center_x - self.button_width//2, 
                              start_y + 2*(self.button_height + self.button_spacing),
                              self.button_width, self.button_height)
        }
        
        # Button hover states
        self.hovered_button = None
        
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
            for button_name, button_rect in self.buttons.items():
                if button_rect.collidepoint(mouse_pos):
                    self.hovered_button = button_name
                    break
        
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
    
    def handle_click(self, mouse_pos):
        """Handle mouse clicks on buttons"""
        # Don't handle clicks if already loading
        if self.loading:
            return None
            
        for button_name, button_rect in self.buttons.items():
            if button_rect.collidepoint(mouse_pos):
                # Start loading animation
                self.start_loading(button_name)
                return None  # Don't return the action immediately
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
        """Draw menu buttons with hover effects and loading animation"""
        button_texts = {
            "start": "Start Game",
            "settings": "Settings", 
            "quit": "Quit"
        }
        
        for button_name, button_rect in self.buttons.items():
            # Determine if this button is loading
            is_loading = self.loading and self.loading_button == button_name
            
            # Determine button colors
            if is_loading:
                bg_color = (80, 120, 80)    # Green tint when loading
                border_color = (100, 255, 100)
                text_color = (200, 255, 200)
                border_width = 3
            elif self.hovered_button == button_name and not self.loading:
                bg_color = (100, 100, 150)  # Lighter when hovered
                border_color = (255, 255, 255)
                text_color = (255, 255, 255)
                border_width = 3
            else:
                bg_color = (50, 50, 80)     # Darker normally
                border_color = (150, 150, 150)
                text_color = (200, 200, 200)
                border_width = 2
            
            # Disable other buttons during loading
            if self.loading and not is_loading:
                bg_color = (30, 30, 30)     # Very dark when disabled
                border_color = (80, 80, 80)
                text_color = (100, 100, 100)
                border_width = 1
            
            # Draw button background
            pygame.draw.rect(self.screen, bg_color, button_rect)
            pygame.draw.rect(self.screen, border_color, button_rect, border_width)
            
            # Draw button text with loading animation
            if is_loading:
                # Create loading text with animated dots
                dots = "." * self.loading_dots
                loading_text = f"Loading{dots}"
                text_surf = self.font_small.render(loading_text, True, text_color)
                
                # Add loading progress bar
                self._draw_loading_progress(button_rect, bg_color)
            else:
                text_surf = self.font_small.render(button_texts[button_name], True, text_color)
            
            text_rect = text_surf.get_rect(center=button_rect.center)
            self.screen.blit(text_surf, text_rect)
    
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
        version_rect = version_surf.get_rect(bottomright=(app.WIDTH - 10, app.HEIGHT - 10))
        self.screen.blit(version_surf, version_rect)