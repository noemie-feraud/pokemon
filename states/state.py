# =============================================================================
# STATE.PY - ABSTRACT BASE CLASS FOR ALL GAME STATES
# =============================================================================
#
# This is the abstract class that all game screens will inherit from.
# Each game state (menu, exploration, combat, dialogue, shop, etc.)
# is a child class that implements these methods.
#
# Why an abstract class?
# - Forces all states to implement the 3 core methods
# - Provides a common interface for StateManager
# - Implements the State Pattern (design pattern)

from abc import ABC, abstractmethod


# =============================================================================
# ABSTRACT STATE CLASS
# =============================================================================

class State(ABC):
    """
    Abstract base class for all game states.
    
    Each state must implement:
    - handle_events(events)
    - update(dt)
    - render(screen)
    
    Optional methods:
    - on_enter() (called when state becomes active)
    - on_exit() (called when state is paused/removed)
    
    Attributes:
        game_manager: reference to the main Game object
        transparent: if True, the state below will also be rendered
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    #
    # game_manager: reference to the main Game object.
    #   Allows any state to access everything it needs:
    #   - change state (game_manager.state_manager.push/pop)
    #   - access player (game_manager.player)
    #   - access Pygame screen (game_manager.screen)
    #   - etc.
    #
    # transparent: should the state below be rendered too?
    #   False by default → state takes full screen (menu, combat, exploration)
    #   True → state overlays (inventory, pokedex, dialogue)
    #   StateManager uses this to know if it should render multiple states.
    
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.transparent = False
    
    
    # -------------------------------------------------------------------------
    # ABSTRACT METHODS (MUST BE IMPLEMENTED BY CHILDREN)
    # -------------------------------------------------------------------------
    
    @abstractmethod
    def handle_events(self, events):
        """
        Called every frame by the main loop.
        Receives the list of Pygame events.
        
        Each state handles inputs differently:
        - StateMenu: up/down navigation, Enter to validate
        - StateExploration: movement keys (ZQSD or arrows)
        - StateCombat: action selection, attack choice
        
        Args:
            events: list of pygame.event.Event objects
        """
        pass
    
    
    @abstractmethod
    def update(self, dt):
        """
        Called every frame after handle_events.
        Updates all logic for this state.
        
        dt = delta time in seconds (time since last frame).
        Example: at 60 FPS, dt ≈ 0.0167 seconds.
        
        We use dt so the game runs at the same speed regardless of actual FPS.
        If a frame takes longer, dt is larger and movement compensates.
        
        Examples:
        - StateExploration: move player by speed × dt pixels
        - StateCombat: animate HP bars decreasing
        - DayNightCycle: advance clock by dt × TIME_RATIO
        
        Args:
            dt: delta time in seconds (float)
        """
        pass
    
    
    @abstractmethod
    def render(self, screen):
        """
        Called every frame after update.
        Draws everything for this state on the screen surface.
        
        Important: render order matters.
        If a state is transparent (e.g., inventory over exploration),
        StateManager will call exploration.render() first,
        then inventory.render() on top.
        
        Each state only renders its own content.
        Combat doesn't draw the map, exploration doesn't draw menus.
        Separation of responsibilities.
        
        Args:
            screen: Pygame surface (the main display)
        """
        pass
    
    
    # -------------------------------------------------------------------------
    # OPTIONAL METHODS (CAN BE OVERRIDDEN IF NEEDED)
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """
        Called ONCE when entering this state.
        Not abstract → optional. States override only if needed.
        
        Used to initialize state-specific things:
        - StateCombat: start combat music, initialize Pokémon
        - StateExploration: resume zone music
        - StateShop: load shop catalog
        
        Different from __init__:
        - __init__ is called when object is CREATED
        - on_enter is called when state becomes ACTIVE
        A state can be created once and reactivated multiple times.
        """
        pass
    
    
    def on_exit(self):
        """
        Called ONCE when leaving this state.
        Same logic as on_enter, but on exit.
        
        Used to clean up:
        - StateCombat: stop combat music
        - StateExploration: auto-save player position
        
        Not abstract → optional.
        """
        pass