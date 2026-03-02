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

        # Only professors with gives_starter=true (i.e. Akram) trigger starter selection.
        self.gives_starter = data.get("gives_starter", False)

        # Load talk dialogue from PROFESSOR_DIALOGUES if not already in data
        if "talk" not in self.dialogues:
            try:
                from data.trainer_dialogues import PROFESSOR_DIALOGUES
                prof_dlg = PROFESSOR_DIALOGUES.get(self.name)
                if prof_dlg:
                    self.dialogues.update(prof_dlg)
            except Exception:
                pass
    
    
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
            return self.dialogues.get("first", [
                "OUE LES GARS Bienvenue à La Plateforme !",
                "Je suis le Prof. Akram les gars.",
                "Ici on apprend en codant les gars... et en entraînant des Pokémon les gars.",
                "Il est temps de choisir ton premier partenaire !"
            ])

        return self.dialogues.get("already_have_starter", [
            "Alors, comment avance ton aventure ?",
            "Continue comme ça, tu deviendras le meilleur dresseur de La Plateforme !"
        ])
    
    
    def on_dialogue_end(self, game_manager):
        """
        Called when dialogue ends.

        If player has no Pokemon in team → launch starter selection.
        Otherwise → nothing, dialogue just closes.
        """
        if not self.gives_starter:
            return

        if not game_manager.player.team.is_empty:
            return

        if self.starter_given:
            return

        from states.state_starter_select import StateStarterSelect
        starter_state = StateStarterSelect(game_manager, npc_professor=self)
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
            "{} a rejoint ton équipe !".format(starter.name),
            "Prends-en soin.",
            "Ton aventure commence maintenant !"
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