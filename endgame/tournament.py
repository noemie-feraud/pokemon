# =============================================================================
# TOURNAMENT.PY - TOURNAMENT LOGIC
# =============================================================================
#
# Tournament logic. Manages bracket, opponents, access conditions.
# Used by state_tournament.py.

import random
import json
import os
from entities.pokemon import Pokemon
from entities.trainer import Trainer
from config.settings import TOURNAMENT_ENTRY_FEE, WILD_POKEMON_LEVELS


# =============================================================================
# CONSTANTS
# =============================================================================

TOURNAMENT_DATA_PATH = "data/tournament.json"

# Fallback if file doesn't exist
DEFAULT_ROUNDS = [
    {
        "name": "Quarter-final",
        "opponent_name": "Challenger Alex",
        "pokemon_count": 2,
        "min_level": 20,
        "max_level": 22,
        "max_stage": 2
    },
    {
        "name": "Semi-final",
        "opponent_name": "Veteran Marie",
        "pokemon_count": 3,
        "min_level": 22,
        "max_level": 24,
        "max_stage": 2
    },
    {
        "name": "Final",
        "opponent_name": "Champion Lucas",
        "pokemon_count": 3,
        "min_level": 24,
        "max_level": 25,
        "max_stage": 3
    }
]


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
    
    def __init__(self, pokemon_data):
        """
        Initialize tournament.
        
        Args:
            pokemon_data: catalog of all 54 Pokemon (for team generation)
        """
        self.pokemon_data = pokemon_data
        
        # Load configuration
        self.rounds_config = self._load_config()
        
        # Generate opponents
        self.opponents = []
        self._generate_opponents()
        
        # Bracket state
        self.current_round = 0
        self.results = []        # list of "victory" or "defeat"
        self.in_progress = False
        self.finished = False
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _load_config(self):
        """
        Load tournament configuration from JSON file.
        Fallback to defaults if file doesn't exist.
        """
        try:
            if os.path.exists(TOURNAMENT_DATA_PATH):
                with open(TOURNAMENT_DATA_PATH, "r") as f:
                    data = json.load(f)
                    return data.get("rounds", DEFAULT_ROUNDS)
        except Exception:
            pass
        
        return DEFAULT_ROUNDS
    
    
    def _generate_opponents(self):
        """Create Trainer objects for each round."""
        self.opponents = []
        
        for round_config in self.rounds_config:
            trainer = self._create_opponent(round_config)
            self.opponents.append(trainer)
    
    
    def _create_opponent(self, round_config):
        """
        Create a Trainer for a given round.
        
        Args:
            round_config: dict with name, pokemon_count, min/max level, max_stage
        
        Returns:
            Trainer instance
        """
        name = round_config.get("opponent_name", "Opponent")
        pokemon_count = round_config.get("pokemon_count", 2)
        min_level = round_config.get("min_level", 20)
        max_level = round_config.get("max_level", 25)
        max_stage = round_config.get("max_stage", 3)
        
        # Generate team
        team = self._generate_team(pokemon_count, min_level, max_level, max_stage)
        
        # Create trainer
        trainer_data = {
            "id": "tournament_" + name.lower().replace(" ", "_"),
            "name": name,
            "type": "trainer",
            "position": {"x": 0, "y": 0},  # no map position
            "direction": "down",
            "dialogues": {
                "challenge": ["Get ready to battle!"],
                "defeat": ["Well played..."],
                "already_beaten": ["You already beat me!"]
            },
            "reward_credits": 0  # no credits in tournament
        }
        
        trainer = Trainer(trainer_data)
        trainer.team = team
        
        return trainer
    
    
    def _generate_team(self, count, min_level, max_level, max_stage):
        """
        Generate a random team for an opponent.
        
        Constraints:
        - count distinct Pokemon
        - levels in [min_level, max_level]
        - stage ≤ max_stage
        - varied types (avoid 2 of same type)
        
        Args:
            count: number of Pokemon
            min_level, max_level: level range
            max_stage: maximum evolution stage
        
        Returns:
            list of Pokemon instances
        """
        team = []
        used_types = set()
        used_ids = set()
        
        # Get all stage 1 Pokemon IDs
        all_ids = self.pokemon_data.get_stage1_ids()
        
        # Shuffle for variety
        shuffled = list(all_ids)
        random.shuffle(shuffled)
        
        for pokemon_id in shuffled:
            if len(team) >= count:
                break
            
            # Get info to check type
            info = self.pokemon_data.get_info(pokemon_id)
            pokemon_types = info["types"]
            
            # Try to avoid duplicate types
            type_already_used = False
            for t in pokemon_types:
                if t in used_types:
                    type_already_used = True
            
            # If type already used and we still have options, skip
            if type_already_used and len(team) < count - 1:
                continue
            
            # Random level
            level = random.randint(min_level, max_level)
            
            # Create Pokemon
            pokemon = Pokemon.from_data(pokemon_id, level)
            
            # Check stage
            if pokemon.evolution_stage > max_stage:
                # Reduce to max stage by adjusting level? For now, skip
                continue
            
            # Add to team
            team.append(pokemon)
            used_ids.add(pokemon_id)
            for t in pokemon_types:
                used_types.add(t)
        
        # If we don't have enough Pokemon (type constraint too strict),
        # fill with random ones
        if len(team) < count:
            for pokemon_id in shuffled:
                if len(team) >= count:
                    break
                if pokemon_id in used_ids:
                    continue
                
                level = random.randint(min_level, max_level)
                pokemon = Pokemon.from_data(pokemon_id, level)
                
                if pokemon.evolution_stage <= max_stage:
                    team.append(pokemon)
                    used_ids.add(pokemon_id)
        
        return team
    
    
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
                "reason": f"Not enough credits (need {TOURNAMENT_ENTRY_FEE}, you have {player.credits})"
            }
        
        # Check team
        if not player.team.has_valid_pokemon:
            return {
                "can": False,
                "reason": "You have no Pokemon able to fight!"
            }
        
        # Check if tournament already in progress
        if self.in_progress:
            return {
                "can": False,
                "reason": "A tournament is already in progress"
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
        
        # Regenerate opponents (new teams each attempt)
        self._generate_opponents()
        
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
        return len(self.rounds_config)
    
    
    def get_round_name(self, index):
        """Return name of round at index."""
        if index < len(self.rounds_config):
            return self.rounds_config[index].get("name", f"Round {index+1}")
        return "Unknown round"
    
    
    def get_opponent(self, index):
        """Return Trainer for given round index."""
        if index < len(self.opponents):
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