# =============================================================================
# TOURNAMENT.PY - TOURNAMENT LOGIC
# =============================================================================
#
# Tournament logic. Manages bracket, opponents, access conditions.
# Used by state_tournament.py.
# Opponents are loaded from trainers.json (with is_tournament flag).

import json
import os
from entities.npc_trainer import NPCTrainer as Trainer
from config.settings import TOURNAMENT_ENTRY_FEE


# =============================================================================
# CONSTANTS
# =============================================================================

TRAINERS_DATA_PATH = "data/trainers.json"


# =============================================================================
# TOURNAMENT CLASS
# =============================================================================

class Tournament:
    """
    Tournament logic. Manages bracket, opponents, access conditions.
    Used by state_tournament.py.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self):
        """
        Initialize tournament.
        Loads tournament opponents from trainers.json.
        """
        
        # Load tournament opponents
        self.opponents = []
        self._load_opponents()
        
        # Round names (for display)
        self.round_names = ["Quart de finale", "Demi-finale", "Finale"]
        
        # Bracket state
        self.current_round = 0
        self.results = []        # list of "victory" or "defeat"
        self.in_progress = False
        self.finished = False
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _load_opponents(self):
        """
        Load tournament opponents from trainers.json.
        Filters trainers with is_tournament = true and sorts by tournament_round.
        """
        try:
            if os.path.exists(TRAINERS_DATA_PATH):
                with open(TRAINERS_DATA_PATH, "r", encoding="utf-8") as f:
                    trainers_data = json.load(f)
                
                # Filter tournament trainers
                tournament_trainers = [
                    t for t in trainers_data 
                    if t.get("is_tournament") and t.get("zone") == "arena"
                ]
                
                # Sort by round (1 = quarter, 2 = semi, 3 = final)
                tournament_trainers.sort(key=lambda t: t.get("tournament_round", 99))
                
                # Create Trainer instances
                self.opponents = [Trainer(t) for t in tournament_trainers]
                
                # Verify we have exactly 3 opponents
                if len(self.opponents) != 3:
                    print(f"Warning: Tournament has {len(self.opponents)} opponents (expected 3)")
            
            else:
                print(f"Warning: Trainers file not found: {TRAINERS_DATA_PATH}")
                self.opponents = []
        
        except Exception as e:
            print(f"Error loading tournament opponents: {e}")
            self.opponents = []
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS - ACCESS CONDITIONS
    # -------------------------------------------------------------------------
    
    def can_participate(self, player):
        """
        Check if player meets conditions to enter tournament.
        
        Args:
            player: Player instance
        
        Returns:
            dict: {"can": bool, "reason": str}
        """
        # Check credits
        if player.credits < TOURNAMENT_ENTRY_FEE:
            return {
                "can": False,
                "reason": f"Pas assez de crédits (besoin de {TOURNAMENT_ENTRY_FEE}, vous en avez {player.credits})"
            }
        
        # Check team
        if not player.team.has_valid_pokemon:
            return {
                "can": False,
                "reason": "Vous n'avez aucun Pokémon en état de combattre !"
            }
        
        # Check if tournament already in progress
        if self.in_progress:
            return {
                "can": False,
                "reason": "Un tournoi est déjà en cours"
            }
        
        # Check if we have opponents
        if len(self.opponents) == 0:
            return {
                "can": False,
                "reason": "Pas d'adversaires disponibles"
            }
        
        return {"can": True, "reason": None}
    
    
    def register(self, player):
        """
        Register player for tournament.
        Deducts entry fee and initializes bracket.
        
        Args:
            player: Player instance
        
        Returns:
            True if registration succeeded, False otherwise
        """
        check = self.can_participate(player)
        if not check["can"]:
            return False
        
        # Deduct credits
        player.credits -= TOURNAMENT_ENTRY_FEE
        
        # Reset bracket
        self.current_round = 0
        self.results = []
        self.in_progress = True
        self.finished = False
        
        return True
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS - BRACKET INFO
    # -------------------------------------------------------------------------
    
    def get_round_count(self):
        """Return number of rounds."""
        return len(self.opponents)
    
    
    def get_round_name(self, index):
        """Return name of round at index."""
        if 0 <= index < len(self.round_names):
            return self.round_names[index]
        return f"Round {index+1}"
    
    
    def get_opponent(self, index):
        """Return Trainer for given round index."""
        if 0 <= index < len(self.opponents):
            return self.opponents[index]
        return None
    
    
    def get_current_opponent(self):
        """Return Trainer for current round."""
        return self.get_opponent(self.current_round)
    
    
    def get_all_opponents(self):
        """Return list of all opponents."""
        return self.opponents
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS - BRACKET PROGRESSION
    # -------------------------------------------------------------------------
    
    def register_result(self, victory):
        """
        Register result of current round.
        
        Args:
            victory: True if player won, False otherwise
        
        Returns:
            dict with tournament state after this result
        """
        if victory:
            self.results.append("victory")
            self.current_round += 1
            
            if self.current_round >= self.get_round_count():
                # All rounds won → tournament victory
                self.finished = True
                self.in_progress = False
                return {
                    "tournament_finished": True,
                    "final_victory": True,
                    "next_round": None
                }
            else:
                return {
                    "tournament_finished": False,
                    "final_victory": False,
                    "next_round": self.current_round
                }
        
        else:
            self.results.append("defeat")
            self.finished = True
            self.in_progress = False
            return {
                "tournament_finished": True,
                "final_victory": False,
                "next_round": None
            }
    
    
    def get_results(self):
        """Return list of results."""
        return self.results
    
    
    def is_round_won(self, index):
        """Check if a specific round was won."""
        if index < len(self.results):
            return self.results[index] == "victory"
        return False
    
    
    def get_progress(self):
        """Return summary of progression for display."""
        return {
            "current_round": self.current_round,
            "round_count": self.get_round_count(),
            "results": self.results,
            "in_progress": self.in_progress,
            "finished": self.finished
        }