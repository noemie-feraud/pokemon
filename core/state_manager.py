# =============================================================================
# STATE_MANAGER.PY - GAME STATE STACK MANAGER
# =============================================================================
#
# Manages the stack of game states.
# Knows which screen is active and delegates calls to the top state.

class StateManager:
    """
    Manages a stack of game states (menu, exploration, combat, etc.).
    Handles pushing, popping, and changing states.
    Also manages transparent rendering for overlapping states.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    #
    # Initializes an empty stack.
    # The stack is just a Python list - we use append() for push
    # and pop() for pop. Simplest way in Python.
    
    def __init__(self):
        """Initialize an empty state stack."""
        self.stack = []
    
    
    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------
    
    @property
    def current_state(self):
        """
        Return the state at the top of the stack.
        Returns None if stack is empty.
        """
        if not self.stack:
            return None
        return self.stack[-1]
    
    
    def is_empty(self):
        """Return True if stack is empty, False otherwise."""
        return len(self.stack) == 0
    
    
    # -------------------------------------------------------------------------
    # STACK OPERATIONS
    # -------------------------------------------------------------------------
    
    def push(self, state):
        """
        Push a new state on top of the current one.
        Previous state is paused, new state becomes active.
        
        Usage examples:
        - Opening inventory over exploration
        - Starting a combat from exploration
        - Showing dialogue over exploration
        
        Sequence:
        1. If there's a current state → call its on_exit()
        2. Add new state to stack
        3. Call on_enter() on new state
        """
        if not self.is_empty():
            self.current_state.on_exit()
        
        self.stack.append(state)
        state.on_enter()
    
    
    def pop(self):
        """
        Remove the top state and return to the previous one.
        
        Usage examples:
        - Closing inventory → back to exploration
        - Combat ends → back to exploration
        - Dialogue ends → back to exploration
        
        Sequence:
        1. Remove top state → call its on_exit()
        2. If there's a state below → call its on_enter()
        
        Safety: if stack is empty, do nothing.
        """
        if self.is_empty():
            return
        
        # Remove top state and call its on_exit
        old_state = self.stack.pop()
        old_state.on_exit()
        
        # If there's a state below, wake it up
        if not self.is_empty():
            self.current_state.on_enter()
    
    
    def change(self, state):
        """
        Replace current state with another one.
        This is pop + push combined, but we don't wake the state below.
        
        Usage examples:
        - Main menu → Exploration (replace, never come back)
        - Game Over → Main menu (same)
        
        Sequence:
        1. Remove current state → call its on_exit()
        2. Add new state at same position → call its on_enter()
        """
        if not self.is_empty():
            old_state = self.stack.pop()
            old_state.on_exit()
        
        self.stack.append(state)
        state.on_enter()
    
    
    def clear(self):
        """
        Completely empty the stack.
        Used when returning to main menu from in-game.
        Calls on_exit() for all states.
        """
        while not self.is_empty():
            state = self.stack.pop()
            state.on_exit()
    
    
    # -------------------------------------------------------------------------
    # DELEGATION METHODS
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """
        Delegate events to the top state ONLY.
        We don't want the player moving on the map while in inventory.
        
        If stack is empty, do nothing.
        """
        if self.is_empty():
            return
        
        self.current_state.handle_events(events)
    
    
    def update(self, dt):
        """
        Delegate update to the top state only.
        Exploration freezes when combat is active - intended behavior.
        """
        if self.is_empty():
            return
        
        self.current_state.update(dt)
    
    
    def render(self, screen):
        """
        Render all visible states, handling transparency.
        
        If top state is transparent (e.g., inventory), we must also render
        what's below it (e.g., exploration).
        
        Algorithm:
        1. Start from top of stack
        2. Go down while states are transparent
        3. Note the index to start drawing from
        4. Render from bottom to top
        
        Example:
        stack = [Exploration, Dialogue, Inventory]
        Inventory is transparent → go down
        Dialogue is transparent → go down
        Exploration is NOT transparent → stop
        Draw: Exploration, then Dialogue, then Inventory
        """
        if self.is_empty():
            return
        
        # Find the lowest state to draw
        start_index = len(self.stack) - 1
        
        while start_index > 0 and self.stack[start_index].transparent:
            start_index -= 1
        
        # Draw from bottom to top
        for i in range(start_index, len(self.stack)):
            self.stack[i].render(screen)