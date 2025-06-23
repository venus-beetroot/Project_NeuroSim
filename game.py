import pygame
import random
import os
import math
from player import Player
import app


pygame.init()
pygame.mixer.init()



class Game:
    def __init__(self):
        pygame.init()  # Initialise Pygame

        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN) #Creating a window for game
        pygame.display.set_caption("Shooter Game") # Setting the title of window to shooter game

        self.clock = pygame.time.Clock() # Create a clock object to control the frame rate
        self.assets = app.load_assets() # Loading the game assets by setting a path to the assets folder
        font_path = os.path.join("assets" ,"PressStart2P.ttf")
        self.font_small = pygame.font.Font(font_path, 18)
        self.font_large = pygame.font.Font(font_path, 32)
        self.player = Player(100, 100, self.assets)


        self.background = self.create_random_background(
            app.WIDTH, app.HEIGHT, self.assets["floor_tiles"] # Use floor tiles to create a background
        )

        self.running = True  # set the game state to running
        self.game_over = False # set the game state of not over

        self.in_level_up_menu = False
        self.reset_game() # Reset game method

    def reset_game(self):
        self.player = Player(app.WIDTH // 2, app.HEIGHT // 2, self.assets)
        self.game_over = False


    def create_random_background(self, width, height, floor_tiles):
        bg = pygame.Surface((width, height)) # Setting bg object as a surface
        tile_w = floor_tiles[0].get_width() # Set start position of tile (width)
        tile_h = floor_tiles[0].get_height() # Set start position of tile (length)

        for y in range(0, height, tile_h):
            for x in range(0, width, tile_w):
                tile = random.choice(floor_tiles)
                bg.blit(tile, (x, y)) # Use blit to place object on screen

        return bg

    def run(self):
        while self.running:
            self.clock.tick(60) # Set FPS to 60

            self.handle_events() # Process user input form keyboard and mouse
            if not self.game_over and not self.in_level_up_menu:
                self.update() # Looks for update for position after each frame
            #### Only update player input, not visual output!###

            self.draw() # Render updated visuals to the screen
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

    def update(self):
        self.player.handle_input()
        self.player.update()


        if self.player.health <= 0:
            self.game_over = True
            return
        



    def draw(self):
        ##Render all game elements to the screen.
        self.screen.blit(self.background, (0, 0))  # update the screen to position 0,0

        if not self.game_over:
            self.player.draw(self.screen)
        
        pygame.display.flip()


   

      