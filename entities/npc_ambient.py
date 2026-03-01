# =============================================================================
# NPC_AMBIENT.PY - AMBIENT NPC CLASS
# =============================================================================
#
# Ambient NPCs that give life to the world.
# They have random dialogues and no special actions.

import random
from entities.npc import NPC


# =============================================================================
# AMBIENT NPC CLASS
# =============================================================================

class NPCAmbient(NPC):
    """
    Ambient NPC. Gives life to the world with humorous dialogues.
    Inherits from NPC. Only overrides get_dialogue().
    Everything else (position, sprite, interaction, draw, on_dialogue_end)
    is inherited from NPC.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, data):
        """
        Initialize ambient NPC.
        
        Args:
            data: dict from npcs.json
        """
        super().__init__(data)
        # No additional attributes needed
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def get_dialogue(self):
        """
        Return dialogue to display when player interacts.
        
        Two modes:
        
        RANDOM MODE (key "random" in dialogues):
            self.dialogues["random"] is a list of dialogues.
            Each dialogue is itself a list of lines.
            Pick one random dialogue.
        
        CLASSIC MODE (key "default" in dialogues):
            Behavior inherited from NPC: always same dialogue.
            Fallback if "random" doesn't exist.
        
        Returns:
            list of strings (dialogue lines)
        """
        # Random mode: if JSON contains "random" key
        if "random" in self.dialogues:
            dialogue_list = self.dialogues["random"]
            
            if dialogue_list:
                # Pick one random dialogue
                return random.choice(dialogue_list)
        
        # Classic mode: fixed dialogue (inherited from NPC)
        return self.dialogues.get("default", ["..."])