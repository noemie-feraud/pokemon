# =============================================================================
# MAIN.PY - GAME ENTRY POINT
# =============================================================================
#
# This file is the unique entry point of the game.
# It initializes Pygame, creates the Game object, and starts the main loop.
#
# Usage: python main.py

# =============================================================================
# DEPENDENCY CHECK
# =============================================================================
#
# Verify that required libraries are installed before anything else.
# If an import fails, display a clear message and exit.

import sys
import os

try:
    import pygame
except ImportError:
    print("ERROR: Pygame is not installed.")
    print("Install it with: pip install pygame")
    sys.exit(1)

try:
    import pytmx
except ImportError:
    print("ERROR: Pytmx is not installed.")
    print("Install it with: pip install pytmx")
    sys.exit(1)

# =============================================================================
# PROJECT IMPORTS
# =============================================================================

from core.game import Game
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WINDOW_TITLE


# =============================================================================
# FOLDER VERIFICATION
# =============================================================================
#
# Ensure required folders exist.
# Critical folders must exist (data/, assets/).
# Auto-created folders are created if missing (saves/).

def check_folders():
    """Verify that all necessary directories exist."""
    
    # Critical folders (must exist for the game to work)
    critical_folders = ["data", "assets"]
    for folder in critical_folders:
        if not os.path.exists(folder):
            print(f"ERROR: Folder '{folder}' is missing.")
            print("Please make sure the project is complete.")
            sys.exit(1)
    
    # Auto-created folders (created if missing)
    auto_folders = ["saves"]
    for folder in auto_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created missing folder: {folder}")


# =============================================================================
# PYGAME INITIALIZATION
# =============================================================================
#
# Initialize all Pygame modules (video, audio, events).
# Create the game window with dimensions from settings.

def init_pygame():
    """Initialize Pygame and create the game window."""
    
    pygame.init()
    
    # Create the game window
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    # Set window title
    pygame.display.set_caption(WINDOW_TITLE)
    
    # Optional: set window icon
    try:
        icon = pygame.image.load("assets/sprites/ui/icon.png")
        pygame.display.set_icon(icon)
    except:
        pass  # No icon, not critical
    
    # Clock for framerate control
    clock = pygame.time.Clock()
    
    return screen, clock


# =============================================================================
# MAIN FUNCTION
# =============================================================================
#
# 1. Check folders
# 2. Initialize Pygame
# 3. Create and run Game
# 4. Cleanup on exit

def main():
    """Main game function."""
    
    # Check folders
    check_folders()
    
    # Initialize Pygame
    screen, clock = init_pygame()
    
    # Create the Game object
    try:
        game = Game(screen, clock)
    except Exception as e:
        print(f"ERROR during game initialization: {e}")
        pygame.quit()
        sys.exit(1)
    
    # Run the main game loop
    try:
        game.run()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        # Optional: print full traceback for debugging
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup - always executed, even after an error
        pygame.quit()
    
    print("Game terminated.")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()