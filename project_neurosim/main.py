"""
Project Neurosim - Entry Point
A Neural Simulation Adventure Game
"""
import pygame
from game.game import Game


def main():
    """Main entry point for the game"""
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"An error occurred: {e}")
        pygame.quit()

if __name__ == "__main__":
    main()