# =============================================================================
# NPC_PROFESSOR.PY - PROFESSOR NPC CLASS
# =============================================================================
#
# Professor who gives the starter Pokemon at the beginning of the game.

import json
from entities.npc import NPC
from entities.pokemon import Pokemon
from config.settings import POKEMON_DATA_FILE


# =============================================================================
# CONSTANTS
# =============================================================================

STARTER_LEVEL = 5


# =============================================================================
# PROFESSOR NPC CLASS
# =============================================================================

class NPCProfessor(NPC):
    """
    Professor who gives the starter Pokemon.
    Player only talks to him once (for starter choice).
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, data):
        """
        Initialize professor.
        
        Args:
            data: dict from npcs.json
        """
        super().__init__(data)
        
        # IDs of the 3 starters in pokemon.json
        self.starter_ids = data.get("starter_ids", [1, 4, 7])
        
        # Flag: has starter been given?
        self.starter_given = False
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _load_starters(self):
        """
        Load starter data from pokemon.json.
        
        Returns:
            list of 3 dicts (starter data), or empty list if error
        """
        try:
            with open(POKEMON_DATA_FILE, "r") as f:
                all_pokemon = json.load(f)
            
            starters = []
            for pokemon_data in all_pokemon:
                if pokemon_data["id"] in self.starter_ids:
                    starters.append(pokemon_data)
            
            return starters
        
        except Exception:
            print("Warning: Could not load starter data")
            return []
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def get_dialogue(self):
        """
        Return appropriate dialogue based on context.
        
        If player has no Pokemon yet → "first_meeting" dialogue
            (welcome speech, intro)
        
        If starter just given → "after_starter" dialogue
            (encouragement right after choice)
        
        If player comes back later → "default" dialogue
            (short friendly line)
        """
        if not self.starter_given:
            return self.dialogues.get("first_meeting", [
                "Welcome to La Plateforme!",
                "I'm the Professor of this school.",
                "Here, we learn by coding... and training Pokemon!",
                "It's time to choose your first partner!"
            ])
        
        return self.dialogues.get("default", [
            "How is your adventure going?",
            "Keep it up, you'll become the best trainer at La Plateforme!"
        ])
    
    
    def on_dialogue_end(self, game_manager):
        """
        Called when dialogue ends.
        
        If player has no Pokemon in team → launch starter selection.
        Otherwise → nothing, dialogue just closes.
        """
        # If player already has Pokemon, nothing to do
        if not game_manager.player.team.is_empty:
            return
        
        # If starter already given (safety)
        if self.starter_given:
            return
        
        # Load starter data
        starters_data = self._load_starters()
        
        if not starters_data:
            # Can't load data, do nothing
            return
        
        # Push starter selection screen
        from states.state_starter_select import StateStarterSelect
        
        starter_state = StateStarterSelect(
            game_manager,
            starters_data,
            callback=self._on_starter_chosen
        )
        game_manager.state_manager.push(starter_state)
    
    
    def _on_starter_chosen(self, starter_data, game_manager):
        """
        Callback when player has chosen a starter.
        
        Args:
            starter_data: dict of chosen Pokemon
            game_manager: Game object
        """
        # Prepare starter data at correct level
        starter_data["level"] = STARTER_LEVEL
        
        # Create Pokemon instance
        starter = Pokemon(starter_data)
        
        # Recalc stats for level 5 (constructor already did it, but ensure)
        starter.recalc_stats()
        
        # Full HP for a good start
        starter.current_hp = starter.max_hp
        
        # Add to player's team
        game_manager.player.team.add(starter)
        
        # Mark that starter has been given
        self.starter_given = True
        
        # Play sound
        game_manager.audio_manager.play_sfx("levelup")
        
        # Confirmation dialogue
        lines = self.dialogues.get("after_starter", [
            "{} has joined your team!".format(starter.name),
            "Take good care of it!",
            "Your adventure begins now!"
        ])
        
        # Replace placeholder if needed
        final_lines = []
        for line in lines:
            final_lines.append(line.replace("{pokemon_name}", starter.name))
        
        from states.state_dialogue import StateDialogue
        
        dialogue_state = StateDialogue(
            game_manager,
            final_lines,
            callback=None   # no action after this dialogue
        )
        game_manager.state_manager.push(dialogue_state)