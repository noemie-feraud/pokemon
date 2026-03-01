# =============================================================================
# ITEM.PY - BASE ITEM CLASS
# =============================================================================
#
# Represents an item in the game (potion, pokeball, etc.).
# Data class with no logic — just properties.

import json
from config.settings import ITEMS_DATA_FILE


# =============================================================================
# ITEM CLASS
# =============================================================================

class Item:
    """
    Represents an item with all its properties.
    Lightweight data class.
    Usage logic is in systems that consume items.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, data):
        """
        Initialize item from JSON data.
        
        Args:
            data: dict from items.json
        """
        
        # --- IDENTITY ---
        self.id = data["id"]
        self.name = data["name"]
        self.description = data.get("description", "")
        
        # --- CATEGORY ---
        # Determines how item is used:
        # "heal" → restores HP
        # "pokeball" → capture attempt
        # "boost" → temporary stat increase
        # "revive" → revives KO Pokemon
        # "status" → removes status condition
        self.category = data["category"]
        
        # --- EFFECT ---
        # Numeric effect value. Meaning depends on category:
        #   heal → HP restored (20, 50, 120)
        #   pokeball → capture rate percentage (30, 60, 80, 100)
        #   boost → boost percentage (25 → +25%)
        #   revive → percentage of max HP restored (50 → 50%)
        #   status → no numeric value (0)
        self.effect_value = data.get("effect_value", 0)
        
        # --- TARGET STAT (for boosts) ---
        # Which stat is boosted: "attack" or "defense"
        # None for non-boost items
        self.target_stat = data.get("target_stat", None)
        
        # --- PRICE ---
        # In credits. 0 = not buyable (quest item, Master Ball)
        self.price = data.get("price", 0)
        
        # --- USAGE CONTEXT ---
        # Where can the item be used?
        # Pokeballs and boosts are combat only.
        # Potions and revives are both.
        self.usable_in_combat = data.get("usable_in_combat", True)
        self.usable_outside_combat = data.get("usable_outside_combat", True)
        
        # --- BUYABLE ---
        # Does the item appear in shops?
        # Master Ball is not buyable (quest reward)
        self.buyable = data.get("buyable", True)
    
    
    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------
    
    @property
    def is_heal(self):
        """True if item is a healing item (potion)."""
        return self.category == "heal"
    
    
    @property
    def is_pokeball(self):
        """True if item is a Poke Ball."""
        return self.category == "pokeball"
    
    
    @property
    def is_boost(self):
        """True if item is a stat boost."""
        return self.category == "boost"
    
    
    @property
    def is_revive(self):
        """True if item is a revive (revives KO)."""
        return self.category == "revive"
    
    
    @property
    def is_status_heal(self):
        """True if item removes status conditions."""
        return self.category == "status"
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def get_formatted_description(self):
        """
        Return readable description for in-game display.
        Adds effect details to base description.
        
        Examples:
            "Potion — Restores 20 HP (25 credits)"
            "Super Ball — 60% capture chance (50 credits)"
            "Attack Boost — +25% attack in combat (40 credits)"
        """
        if self.is_heal:
            effect_str = f"Restores {self.effect_value} HP"
        
        elif self.is_pokeball:
            effect_str = f"{self.effect_value}% capture chance"
        
        elif self.is_boost:
            effect_str = f"+{self.effect_value}% {self.target_stat}"
        
        elif self.is_revive:
            effect_str = f"Revives with {self.effect_value}% HP"
        
        elif self.is_status_heal:
            effect_str = "Removes status conditions"
        
        else:
            effect_str = self.description
        
        if self.price > 0:
            return f"{self.name} — {effect_str} ({self.price} credits)"
        else:
            return f"{self.name} — {effect_str}"
    
    
    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------
    
    def to_dict(self):
        """Serialize for debug."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "effect_value": self.effect_value,
            "target_stat": self.target_stat,
            "price": self.price,
            "usable_in_combat": self.usable_in_combat,
            "usable_outside_combat": self.usable_outside_combat,
            "buyable": self.buyable
        }
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """Debug representation."""
        return f"{self.name} ({self.category}) — effect: {self.effect_value} — {self.price} credits"


# =============================================================================
# ITEM CATALOG CLASS
# =============================================================================

class ItemCatalog:
    """
    Loads and stores all items from items.json.
    Singleton in practice: created once at startup.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self):
        """Load items.json and create Item instances."""
        self.items = {}
        
        try:
            with open(ITEMS_DATA_FILE, "r") as f:
                items_data = json.load(f)
            
            for item_data in items_data:
                item = Item(item_data)
                self.items[item.id] = item
        
        except Exception:
            print("Warning: Could not load item catalog")
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def get_item(self, item_id):
        """Return Item by ID, or None if not found."""
        return self.items.get(item_id, None)
    
    
    def get_buyable_items(self):
        """Return list of items buyable in shops."""
        buyable = []
        for item in self.items.values():
            if item.buyable and item.price > 0:
                buyable.append(item)
        return buyable
    
    
    def get_items_by_category(self, category):
        """Return all items of a given category."""
        result = []
        for item in self.items.values():
            if item.category == category:
                result.append(item)
        return result
    
    
    def get_all(self):
        """Return list of all items."""
        return list(self.items.values())
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __len__(self):
        return len(self.items)
    
    
    def __str__(self):
        return f"ItemCatalog ({len(self.items)} items)"