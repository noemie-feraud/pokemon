# =============================================================================
# NPC_NURSE.PY - NURSE NPC CLASS
# =============================================================================
#
# Nurse at the Pokemon Center. Heals player's team.

from entities.npc import NPC


# =============================================================================
# NURSE NPC CLASS
# =============================================================================

class NPCNurse(NPC):
    """
    Nurse at the Pokemon Center.
    Heals player's team after dialogue.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, data):
        """
        Initialize nurse.
        
        Args:
            data: dict from npcs.json
        """
        super().__init__(data)
        
        # Flag to know if we just healed
        # Used to choose between "default" and "after" dialogue
        self.has_healed = False
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def get_dialogue(self):
        """
        Return appropriate dialogue based on context.
        
        If just healed → "after" dialogue
            ("Your Pokemon are fully healed!")
        Otherwise → "default" dialogue
            ("Welcome to the Pokemon Center!")
        
        After returning "after" dialogue, reset flag so next interaction
        starts normally.
        """
        if self.has_healed:
            self.has_healed = False
            return self.dialogues.get("after", ["Your Pokemon are fully healed!"])
        
        return self.dialogues.get("default", ["Welcome to the Pokemon Center!"])
    
    
    def on_interact(self, game_manager):
        """Reset healed flag at the start of each fresh interaction."""
        self.has_healed = False
        super().on_interact(game_manager)

    def on_dialogue_end(self, game_manager):
        """
        Called when default dialogue ends.
        Heals the team then shows a confirmation dialogue (no further callback).
        """
        if self.has_healed:
            return

        game_manager.player.team.heal_all()
        game_manager.audio_manager.play_sfx("heal")
        self.has_healed = True

        after_lines = self.dialogues.get(
            "after", ["Vos Pokémon sont complètement rétablis !"]
        )

        from states.state_dialogue import StateDialogue

        dialogue_state = StateDialogue(
            game_manager,
            after_lines,
            npc=self,
            callback=None   # stops the loop
        )
        game_manager.state_manager.push(dialogue_state)