# =============================================================================
# TEAM.PY - PLAYER'S ACTIVE TEAM
# =============================================================================
#
# Manages the player's active team (max 6 Pokemon).
# Enforces rules: max 6, always at least 1 valid Pokemon.

from config.settings import MAX_TEAM_SIZE


# =============================================================================
# TEAM CLASS
# =============================================================================

class Team:
    """
    Manages active Pokemon team (max 6).
    Enforces rules: no more than 6, always at least 1 valid.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, pokemon_list=None):
        """
        Initialize team.
        
        Args:
            pokemon_list: list of Pokemon objects (from save)
        """
        if pokemon_list is None:
            self.pokemon = []
        else:
            self.pokemon = pokemon_list.copy()
    
    
    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------
    
    @property
    def size(self):
        """Number of Pokemon in team."""
        return len(self.pokemon)
    
    
    @property
    def is_full(self):
        """True if team has reached max size (6)."""
        return self.size >= MAX_TEAM_SIZE
    
    
    @property
    def is_empty(self):
        """True if team is empty."""
        return self.size == 0
    
    
    @property
    def has_valid_pokemon(self):
        """True if at least 1 non-KO Pokemon in team."""
        for pokemon in self.pokemon:
            if not pokemon.is_ko:
                return True
        return False
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def get_first_valid(self):
        """
        Return first non-KO Pokemon in team.
        This is the one sent out at start of combat.
        
        Returns:
            Pokemon object or None if all KO
        """
        for pokemon in self.pokemon:
            if not pokemon.is_ko:
                return pokemon
        return None
    
    
    def get_pokemon(self, index):
        """
        Return Pokemon at given index.
        
        Args:
            index: 0 to 5
        
        Returns:
            Pokemon object or None if invalid index
        """
        if index < 0 or index >= self.size:
            return None
        return self.pokemon[index]
    
    
    def get_all(self):
        """Return copy of team list."""
        return self.pokemon.copy()
    
    
    def add(self, pokemon):
        """
        Add a Pokemon to team.
        
        Args:
            pokemon: Pokemon object
        
        Returns:
            True if added, False if team full
        """
        if self.is_full:
            return False
        
        self.pokemon.append(pokemon)
        return True
    
    
    def remove(self, index):
        """
        Remove a Pokemon from team by index.
        
        Before removing, check:
        1. Index is valid
        2. After removal, at least 1 non-KO Pokemon remains (CA-87)
        
        Args:
            index: position to remove
        
        Returns:
            Removed Pokemon if successful, None otherwise
        """
        if index < 0 or index >= self.size:
            return None
        
        pokemon_to_remove = self.pokemon[index]
        
        # Simulate removal to check rule
        team_after = [p for i, p in enumerate(self.pokemon) if i != index]
        has_valid = False
        for p in team_after:
            if not p.is_ko:
                has_valid = True
                break
        
        # If team would be empty or have no valid Pokemon → refuse
        if not team_after or not has_valid:
            return None
        
        # All good, remove
        return self.pokemon.pop(index)
    
    
    def swap(self, index_a, index_b):
        """
        Swap two Pokemon positions in team.
        
        Args:
            index_a, index_b: positions to swap
        
        Returns:
            True if successful, False if invalid indices
        """
        if index_a < 0 or index_a >= self.size:
            return False
        if index_b < 0 or index_b >= self.size:
            return False
        if index_a == index_b:
            return False
        
        self.pokemon[index_a], self.pokemon[index_b] = self.pokemon[index_b], self.pokemon[index_a]
        return True
    
    
    def heal_all(self):
        """Fully heal all Pokemon in team."""
        for pokemon in self.pokemon:
            pokemon.full_heal()
    
    
    def get_valid(self):
        """Return list of non-KO Pokemon."""
        return [p for p in self.pokemon if not p.is_ko]
    
    
    def get_ko(self):
        """Return list of KO Pokemon."""
        return [p for p in self.pokemon if p.is_ko]
    
    
    def count_valid(self):
        """Return number of non-KO Pokemon."""
        return len(self.get_valid())
    
    
    def contains(self, pokemon_id):
        """Check if a Pokemon (by ID) is in team."""
        for pokemon in self.pokemon:
            if pokemon.id == pokemon_id:
                return True
        return False
    
    
    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------
    
    def to_list(self):
        """
        Convert team to list of dicts for save.
        Calls to_dict() on each Pokemon.
        """
        return [p.to_dict() for p in self.pokemon]
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __len__(self):
        """Allow len(team)."""
        return self.size
    
    
    def __iter__(self):
        """Allow 'for pokemon in team:'."""
        return iter(self.pokemon)
    
    
    def __str__(self):
        """Debug representation."""
        names = [f"{p.name} Nv.{p.level}" for p in self.pokemon]
        return f"Team ({self.size}/{MAX_TEAM_SIZE}): {', '.join(names)}"