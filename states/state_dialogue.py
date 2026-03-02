# =============================================================================
# STATE_DIALOGUE.PY - DIALOGUE STATE
# =============================================================================
#
# This state manages conversations with NPCs.
# When the player presses Space in front of an NPC, StateExploration pushes
# a StateDialogue onto the stack.

import pygame
from states.state import State
from ui.dialogue_box import DialogueBox


# =============================================================================
# STATE DIALOGUE CLASS
# =============================================================================

class StateDialogue(State):
    """
    Transparent state that displays dialogue over exploration.
    Pops when dialogue ends and executes the NPC's callback.
    """
    
    # Class attribute: transparent = True tells state_manager to render
    # the state below before this one
    transparent = True
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager, lines, npc=None, callback=None):
        """
        Initialize dialogue state.
        
        Args:
            game_manager: reference to Game
            lines: list of strings, dialogue lines to display
            npc: NPC instance (for reference, optional)
            callback: function to execute when dialogue ends
                     signature: callback(player, game_manager)
                     can be None
        """
        super().__init__(game_manager)
        
        self.npc = npc
        self.callback = callback
        
        # Create dialogue box with lines
        self.dialogue_box = DialogueBox(
            lines=lines,
            audio_manager=game_manager.audio_manager
        )
        
        # Flag to avoid double callback execution
        self.finished = False
    
    
    # -------------------------------------------------------------------------
    # LIFECYCLE METHODS
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """Nothing special on entry. Exploration music continues."""
        pass
    
    
    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """
        Handle player input during dialogue.
        Only Space/Enter is accepted.
        """
        if self.finished:
            return
        
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                self._advance_dialogue()
    
    
    def _advance_dialogue(self):
        """
        Advance dialogue by one step.
        Either skip typewriter, go to next page, or end dialogue.
        """
        result = self.dialogue_box.advance()

        if result:
            self._end_dialogue()
    
    
    def _end_dialogue(self):
        """
        Dialogue is finished. Execute callback and pop.
        
        ORDER IS IMPORTANT:
        1. Pop first (return to exploration)
        2. Execute callback afterwards
        
        Why this order? Because the callback might push a new state
        (shop, Pokemon center, starter select...). If we executed the
        callback before popping, we would have:
        stack = [exploration, dialogue, new_state]
        And when dialogue pops afterwards, it would remove new_state
        instead of itself.
        
        By popping first:
        stack = [exploration] (after pop)
        stack = [exploration, new_state] (after callback push)
        This is the correct behavior.
        """
        if self.finished:
            return  # Safety against double execution
        
        self.finished = True
        
        # 1. Pop from stack
        self.game_manager.state_manager.pop()
        
        # 2. Execute callback if present
        if self.callback is not None:
            try:
                self.callback(self.game_manager)
            except Exception as e:
                print(f"Error in dialogue callback: {e}")
    
    
    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    
    def update(self, dt):
        """Update dialogue box typewriter."""
        if not self.finished:
            self.dialogue_box.update(dt)
    
    
    # -------------------------------------------------------------------------
    # RENDERING
    # -------------------------------------------------------------------------
    
    def render(self, screen):
        """
        Draw dialogue box over the screen.
        
        NOTE: the state below (exploration) is rendered by state_manager
        BEFORE this state, thanks to transparent = True.
        So here we only draw the dialogue box, not the background.
        """
        # Exploration has already been rendered by state_manager
        # Just draw the dialogue box on top
        self.dialogue_box.draw(screen)