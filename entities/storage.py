# =============================================================================
# STORAGE.PY - POKEMON STORAGE (PC)
# =============================================================================
#
# Storage for Pokemon beyond the active team (max 6).
# No size limit.
# Accessible only at Pokemon Center for team management.

class Storage:
    """
    Storage for captured Pokemon beyond the active team.
    No size limit.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, pokemon_list=None):
        """
        Initialize storage.
        
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
        """Number of Pokemon in storage."""
        return len(self.pokemon)
    
    
    @property
    def is_empty(self):
        """True if storage is empty."""
        return self.size == 0
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def add(self, pokemon):
        """
        Add a Pokemon to storage.
        No duplicate check (player can have multiple of same species).
        No size limit.
        
        Args:
            pokemon: Pokemon object
        """
        self.pokemon.append(pokemon)
    
    
    def remove(self, index):
        """
        Remove a Pokemon from storage by index.
        
        Args:
            index: position to remove
        
        Returns:
            Removed Pokemon or None if invalid index
        """
        if index < 0 or index >= self.size:
            return None
        
        return self.pokemon.pop(index)
    
    
    def get_pokemon(self, index):
        """
        Return Pokemon at given index without removing.
        
        Args:
            index: position
        
        Returns:
            Pokemon object or None if invalid index
        """
        if index < 0 or index >= self.size:
            return None
        return self.pokemon[index]
    
    
    def get_all(self):
        """Return copy of storage list."""
        return self.pokemon.copy()
    
    
    def get_by_type(self, pokemon_type):
        """
        Return all Pokemon of a given type.
        Useful for capture quests.
        
        Args:
            pokemon_type: "fire", "water", "grass", etc.
        
        Returns:
            list of Pokemon
        """
        result = []
        for pokemon in self.pokemon:
            if pokemon_type in pokemon.types:
                result.append(pokemon)
        return result
    
    
    def contains(self, pokemon_id):
        """Check if a Pokemon (by ID) is in storage."""
        for pokemon in self.pokemon:
            if pokemon.id == pokemon_id:
                return True
        return False
    
    
    def count_species(self, pokemon_id):
        """
        Count how many of a given species are in storage.
        Used for quests: "capture 3 Water type Pokemon"
        → count in team + storage.
        """
        count = 0
        for pokemon in self.pokemon:
            if pokemon.id == pokemon_id:
                count += 1
        return count
    
    
    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------
    
    def to_list(self):
        """
        Convert storage to list of dicts for save.
        Calls to_dict() on each Pokemon.
        """
        return [p.to_dict() for p in self.pokemon]
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __len__(self):
        """Allow len(storage)."""
        return self.size
    
    
    def __iter__(self):
        """Allow 'for pokemon in storage:'."""
        return iter(self.pokemon)
    
    
    def __str__(self):
        """Debug representation."""
        if self.is_empty:
            return "Storage (empty)"
        names = [p.name for p in self.pokemon]
        return f"Storage ({self.size} Pokemon): {', '.join(names)}"