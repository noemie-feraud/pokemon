# =============================================================================
# POKEMON_CENTER.PY - POKEMON CENTER LOGIC
# =============================================================================
#
# Handles team/storage management at Pokemon Center.

class PokemonCenter:
    """
    Pokemon Center logic. Manages team/storage exchanges.
    Coordinates Team and Storage without them knowing each other.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, player):
        """
        Initialize Pokemon Center.
        
        Args:
            player: Player object (to access team and storage)
        """
        self.player = player
        self.team = player.team
        self.storage = player.storage
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS - GETTERS
    # -------------------------------------------------------------------------
    
    def get_team(self):
        """Return team list (for display)."""
        return self.team.get_all()
    
    
    def get_storage(self):
        """Return storage list (for display)."""
        return self.storage.get_all()
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS - VALIDATION
    # -------------------------------------------------------------------------
    
    def can_deposit(self, pokemon):
        """
        Check if a Pokemon can be deposited from team to storage.
        
        Conditions:
        1. Team has more than 1 Pokemon (can't empty team)
        2. After deposit, team still has at least 1 valid (non-KO) Pokemon
        
        Args:
            pokemon: Pokemon to deposit
        
        Returns:
            dict: {"possible": bool, "reason": str or None}
        """
        # Team size check
        if self.team.size <= 1:
            return {"possible": False, "reason": "last_pokemon"}
        
        # Count valid Pokemon after removal
        valid_after = 0
        for p in self.team.get_all():
            if p != pokemon and not p.is_ko:
                valid_after += 1
        
        if valid_after == 0:
            return {"possible": False, "reason": "last_valid"}
        
        return {"possible": True, "reason": None}
    
    
    def can_withdraw(self, pokemon):
        """
        Check if a Pokemon can be withdrawn from storage to team.
        
        Condition: team is not full (less than 6)
        
        Args:
            pokemon: Pokemon to withdraw
        
        Returns:
            dict: {"possible": bool, "reason": str or None}
        """
        if self.team.is_full:
            return {"possible": False, "reason": "team_full"}
        
        return {"possible": True, "reason": None}
    
    
    def can_exchange(self, team_pokemon, storage_pokemon):
        """
        Check if team and storage Pokemon can be exchanged.
        
        Exchange = deposit + withdraw simultaneously.
        Team size stays the same, but need to check valid Pokemon rule.
        
        Args:
            team_pokemon: Pokemon from team to deposit
            storage_pokemon: Pokemon from storage to withdraw
        
        Returns:
            dict: {"possible": bool, "reason": str or None}
        """
        # Count valid Pokemon after exchange
        valid_after = 0
        
        # Current team except the one being deposited
        for p in self.team.get_all():
            if p != team_pokemon and not p.is_ko:
                valid_after += 1
        
        # Add incoming Pokemon if valid
        if not storage_pokemon.is_ko:
            valid_after += 1
        
        if valid_after == 0:
            return {"possible": False, "reason": "no_valid_after_exchange"}
        
        return {"possible": True, "reason": None}
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS - ACTIONS
    # -------------------------------------------------------------------------
    
    def deposit(self, pokemon):
        """
        Transfer a Pokemon from team to storage.
        
        Args:
            pokemon: Pokemon to deposit
        
        Returns:
            dict: {
                "success": bool,
                "pokemon": Pokemon or None,
                "reason": str or None
            }
        """
        # Validate
        check = self.can_deposit(pokemon)
        if not check["possible"]:
            return {
                "success": False,
                "pokemon": None,
                "reason": check["reason"]
            }
        
        # Find index of this Pokemon in team
        index = -1
        for i, p in enumerate(self.team.get_all()):
            if p == pokemon:
                index = i
                break
        
        if index == -1:
            return {
                "success": False,
                "pokemon": None,
                "reason": "pokemon_not_in_team"
            }
        
        # Remove from team and add to storage
        removed = self.team.remove(index)
        if removed is None:
            return {
                "success": False,
                "pokemon": None,
                "reason": "remove_failed"
            }
        
        self.storage.add(removed)
        
        return {
            "success": True,
            "pokemon": removed,
            "reason": None
        }
    
    
    def withdraw(self, pokemon):
        """
        Transfer a Pokemon from storage to team.
        
        Args:
            pokemon: Pokemon to withdraw
        
        Returns:
            dict: {
                "success": bool,
                "pokemon": Pokemon or None,
                "reason": str or None
            }
        """
        # Validate
        check = self.can_withdraw(pokemon)
        if not check["possible"]:
            return {
                "success": False,
                "pokemon": None,
                "reason": check["reason"]
            }
        
        # Find index of this Pokemon in storage
        index = -1
        for i, p in enumerate(self.storage.get_all()):
            if p == pokemon:
                index = i
                break
        
        if index == -1:
            return {
                "success": False,
                "pokemon": None,
                "reason": "pokemon_not_in_storage"
            }
        
        # Remove from storage and add to team
        removed = self.storage.remove(index)
        if removed is None:
            return {
                "success": False,
                "pokemon": None,
                "reason": "remove_failed"
            }
        
        self.team.add(removed)
        
        return {
            "success": True,
            "pokemon": removed,
            "reason": None
        }
    
    
    def exchange(self, team_pokemon, storage_pokemon):
        """
        Exchange team Pokemon with storage Pokemon.
        
        Args:
            team_pokemon: Pokemon from team to deposit
            storage_pokemon: Pokemon from storage to withdraw
        
        Returns:
            dict: {
                "success": bool,
                "deposited": Pokemon or None,
                "withdrawn": Pokemon or None,
                "reason": str or None
            }
        """
        # Validate
        check = self.can_exchange(team_pokemon, storage_pokemon)
        if not check["possible"]:
            return {
                "success": False,
                "deposited": None,
                "withdrawn": None,
                "reason": check["reason"]
            }
        
        # Find indices
        team_index = -1
        for i, p in enumerate(self.team.get_all()):
            if p == team_pokemon:
                team_index = i
                break
        
        storage_index = -1
        for i, p in enumerate(self.storage.get_all()):
            if p == storage_pokemon:
                storage_index = i
                break
        
        if team_index == -1 or storage_index == -1:
            return {
                "success": False,
                "deposited": None,
                "withdrawn": None,
                "reason": "pokemon_not_found"
            }
        
        # Perform exchange
        # Remove from storage first (team still full)
        withdrawn = self.storage.remove(storage_index)
        if withdrawn is None:
            return {
                "success": False,
                "deposited": None,
                "withdrawn": None,
                "reason": "remove_storage_failed"
            }
        
        # Remove from team (now we have space)
        deposited = self.team.remove(team_index)
        if deposited is None:
            # Should not happen if validation passed, but just in case
            # Put withdrawn back in storage
            self.storage.add(withdrawn)
            return {
                "success": False,
                "deposited": None,
                "withdrawn": None,
                "reason": "remove_team_failed"
            }
        
        # Add withdrawn to team
        self.team.add(withdrawn)
        
        # Add deposited to storage
        self.storage.add(deposited)
        
        return {
            "success": True,
            "deposited": deposited,
            "withdrawn": withdrawn,
            "reason": None
        }
    
    
    def heal_team(self):
        """Heal all Pokemon in team."""
        self.team.heal_all()
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS - SUMMARY
    # -------------------------------------------------------------------------
    
    def get_summary(self):
        """
        Return summary of current state for display.
        
        Returns:
            dict with:
            - team_size
            - team_valid
            - team_ko
            - storage_size
            - team_full
            - storage_empty
        """
        return {
            "team_size": self.team.size,
            "team_valid": self.team.count_valid(),
            "team_ko": len(self.team.get_ko()),
            "storage_size": self.storage.size,
            "team_full": self.team.is_full,
            "storage_empty": self.storage.is_empty
        }
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """Debug representation."""
        return f"PokemonCenter — Team: {self.team.size}/6, Storage: {self.storage.size} Pokemon"