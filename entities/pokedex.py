# =============================================================================
# POKEDEX.PY - POKEDEX CLASS
# =============================================================================
#
# Manages the player's Pokedex: seen and captured Pokemon.
# Stores two sets of IDs:
# - seen: encountered in combat (even if fled)
# - captured: owned (currently or in the past)

class Pokedex:
    """
    Manages seen and captured Pokemon.
    Stored in Player, saved in save slot.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, seen_ids=None, captured_ids=None):
        """
        Initialize Pokedex.
        
        Args:
            seen_ids: list of encountered Pokemon IDs
            captured_ids: list of captured Pokemon IDs
        """
        if seen_ids is None:
            self.seen = set()
        else:
            self.seen = set(seen_ids)
        
        if captured_ids is None:
            self.captured = set()
        else:
            self.captured = set(captured_ids)
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def register_seen(self, pokemon_id):
        """
        Register a Pokemon as seen.
        Called by combat.py at start of each combat.
        
        Args:
            pokemon_id: Pokemon ID (1 to 54)
        
        Returns:
            True if new entry, False if already seen
        """
        old_size = len(self.seen)
        self.seen.add(pokemon_id)
        return len(self.seen) > old_size
    
    
    def register_captured(self, pokemon_id):
        """
        Register a Pokemon as captured.
        Called by capture_system.py when capture succeeds.
        
        Note: A captured Pokemon is automatically seen.
        If ID not in seen, it is added.
        
        Args:
            pokemon_id: captured Pokemon ID
        
        Returns:
            True if new capture, False if already captured
        """
        # Captured Pokemon is automatically seen
        self.register_seen(pokemon_id)
        
        old_size = len(self.captured)
        self.captured.add(pokemon_id)
        return len(self.captured) > old_size
    
    
    def is_seen(self, pokemon_id):
        """Check if a Pokemon has been encountered."""
        return pokemon_id in self.seen
    
    
    def is_captured(self, pokemon_id):
        """Check if a Pokemon has been captured."""
        return pokemon_id in self.captured
    
    
    def get_total_seen(self):
        """Return number of seen Pokemon."""
        return len(self.seen)
    
    
    def get_total_captured(self):
        """Return number of captured Pokemon."""
        return len(self.captured)
    
    
    def get_seen_list(self):
        """Return list of seen Pokemon IDs (sorted)."""
        return sorted(list(self.seen))
    
    
    def get_captured_list(self):
        """Return list of captured Pokemon IDs (sorted)."""
        return sorted(list(self.captured))
    
    
    def get_new_entries(self):
        """
        Return list of newly seen Pokemon (for "NEW!" animation).
        Not implemented yet.
        """
        return []  # TODO: implement if needed
    
    
    def get_completion_percentage(self, total_pokemon):
        """
        Return completion percentage based on seen Pokemon.
        
        Args:
            total_pokemon: total number of Pokemon in game (54)
        
        Returns:
            float between 0.0 and 1.0
        """
        if total_pokemon == 0:
            return 0.0
        return len(self.seen) / total_pokemon
    
    
    def get_capture_percentage(self, total_pokemon):
        """
        Return capture percentage.
        
        Args:
            total_pokemon: total number of Pokemon in game (54)
        
        Returns:
            float between 0.0 and 1.0
        """
        if total_pokemon == 0:
            return 0.0
        return len(self.captured) / total_pokemon
    
    
    def reset(self):
        """Clear Pokedex (new game)."""
        self.seen = set()
        self.captured = set()
    
    
    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------
    
    def to_dict(self):
        """
        Convert Pokedex to dict for save.
        Convert sets to lists (JSON doesn't support sets).
        
        Returns:
            {"seen": [1,4,7], "captured": [1,4]}
        """
        return {
            "seen": sorted(list(self.seen)),
            "captured": sorted(list(self.captured))
        }
    
    
    @classmethod
    def from_dict(cls, data):
        """
        Recreate Pokedex from save dict.
        
        Args:
            data: dict with "seen" and "captured" keys
        
        Returns:
            Pokedex instance
        """
        seen_ids = data.get("seen", [])
        captured_ids = data.get("captured", [])
        return cls(seen_ids, captured_ids)
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __len__(self):
        """Return number of seen Pokemon."""
        return len(self.seen)
    
    
    def __str__(self):
        """Debug representation."""
        return f"Pokedex ({len(self.seen)} seen, {len(self.captured)} captured)"