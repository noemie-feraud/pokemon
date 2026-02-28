# =============================================================================
# GAME.PY - MAIN GAME CLASS
# =============================================================================
#
# This is the heart of the game. The Game class:
# - Initializes Pygame and creates the window
# - Runs the main game loop
# - Delegates everything to StateManager and other managers
#
# If the game is a body, game.py is the heart that pumps blood.

import pygame
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WINDOW_TITLE
from core.state_manager import StateManager
from core.audio_manager import AudioManager
from core.day_night_cycle import DayNightCycle
from states.state_menu import StateMenu


# =============================================================================
# GAME CLASS
# =============================================================================

class Game:
    """
    Main game class. Creates all managers and runs the main loop.
    All states access the game via self.game_manager to get what they need
    (screen, player, audio, etc.).
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    #
    # Initializes Pygame and creates all game components.
    #
    # Order is important:
    #   1. Pygame first (otherwise nothing works)
    #   2. Window (states need it to draw)
    #   3. Clock (loop needs it for FPS)
    #   4. Managers (state, audio, day_night)
    #   5. First state (main menu)
    #
    # player is None at start. It will be created when the player chooses
    # their character and starter (in StateMenu / CharacterSelect).
    
    def __init__(self, screen, clock):
        """
        Initialize the game with a Pygame screen and clock.
        
        Args:
            screen: Pygame surface (the game window)
            clock: Pygame clock for FPS control
        """
        
        # Store screen and clock
        self.screen = screen
        self.clock = clock
        
        # Game runs while this is True
        self.running = True
        
        # Player (created later, after character selection)
        self.player = None
        
        # Managers
        self.state_manager = StateManager()
        self.audio_manager = AudioManager()
        self.day_night_cycle = DayNightCycle()
        
        # Push main menu as first state
        # Pass self (the Game) so states can access everything
        self.state_manager.push(StateMenu(self))
    
    
    # -------------------------------------------------------------------------
    # MAIN GAME LOOP
    # -------------------------------------------------------------------------
    #
    # THE main loop. Runs while self.running is True.
    #
    # Each frame:
    #   1. Calculate dt (delta time)
    #   2. Get Pygame events
    #   3. Check if player closed window
    #   4. Delegate events → update → render to StateManager
    #   5. Update display
    #   6. Check if state stack is empty (= game finished)
    #
    # When loop stops, call cleanup() to close everything.
    
    def run(self):
        """Main game loop."""
        
        while self.running:
            
            # -----------------------------------------------------------------
            # DELTA TIME
            # -----------------------------------------------------------------
            # clock.tick(FPS) does two things:
            #   1. Waits to maintain 60 FPS
            #   2. Returns time since last tick in milliseconds
            # Divide by 1000 to get seconds
            dt = self.clock.tick(FPS) / 1000.0
            
            # -----------------------------------------------------------------
            # EVENTS
            # -----------------------------------------------------------------
            # pygame.event.get() returns ALL events since last frame
            # (key presses, releases, clicks, window close, etc.)
            events = pygame.event.get()
            
            # -----------------------------------------------------------------
            # QUIT
            # -----------------------------------------------------------------
            # Check if player closed the window.
            # This is handled here, not in states, because it's global:
            # no matter where we are, the X button must work.
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
            
            # -----------------------------------------------------------------
            # DELEGATE TO STATE MANAGER
            # -----------------------------------------------------------------
            # StateManager handles everything and passes to the active state.
            # We don't need to know which state is active - that's the power
            # of the State Pattern.
            self.state_manager.handle_events(events)
            self.state_manager.update(dt)
            self.state_manager.render(self.screen)
            
            # -----------------------------------------------------------------
            # UPDATE DISPLAY
            # -----------------------------------------------------------------
            # pygame.display.flip() takes everything drawn on self.screen
            # and actually displays it.
            # Without this, we draw "in the void" and nothing shows.
            pygame.display.flip()
            
            # -----------------------------------------------------------------
            # CHECK GAME END
            # -----------------------------------------------------------------
            # If the state stack is empty, there's nothing left to display.
            # This happens when player quits from main menu for example.
            if self.state_manager.is_empty():
                self.running = False
        
        # Loop finished, clean up
        self.cleanup()
    
    
    # -------------------------------------------------------------------------
    # CLEANUP
    # -------------------------------------------------------------------------
    #
    # Called when game closes.
    # Properly releases all Pygame resources.
    #
    # Why this is important:
    #   - pygame.quit() closes window and frees audio/video memory
    #   - Without it, on some OS the window stays open or audio keeps playing
    #
    # We could also auto-save here (emergency save), but that's SaveManager's job.
    
    def cleanup(self):
        """Clean up Pygame resources."""
        pygame.quit()