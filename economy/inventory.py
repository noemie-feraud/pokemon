# =============================================================================
# INVENTORY.PY - PLAYER'S INVENTORY
# =============================================================================
#
# Manages player's items with quantities.
# Stores {item_id: quantity} internally.
# Accesses ItemCatalog for item details.

from entities.item import ItemCatalog


# =============================================================================
# INVENTORY CLASS
# =============================================================================

class Inventory:
    """
    Manages player's owned items with quantities.
    Stores {item_id: quantity} internally.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, item_catalog):
        """
        Initialize inventory.
        
        Args:
            item_catalog: reference to game's ItemCatalog
        """
        self.item_catalog = item_catalog
        self.items = {}  # {item_id: quantity}
    
    
    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------
    
    @property
    def is_empty(self):
        """True if player has no items."""
        return len(self.items) == 0
    
    
    @property
    def total_count(self):
        """Total number of items (all quantities summed)."""
        total = 0
        for qty in self.items.values():
            total += qty
        return total
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def add(self, item_id, quantity=1):
        """
        Add quantity of an item to inventory.
        
        Args:
            item_id: item ID (must exist in catalog)
            quantity: amount to add (default 1)
        """
        # Verify item exists in catalog
        if self.item_catalog.get_item(item_id) is None:
            print(f"Warning: Unknown item ID: {item_id}")
            return
        
        if item_id in self.items:
            self.items[item_id] += quantity
        else:
            self.items[item_id] = quantity
    
    
    def remove(self, item_id, quantity=1):
        """
        Remove quantity of an item from inventory.
        
        Args:
            item_id: item ID
            quantity: amount to remove (default 1)
        
        Returns:
            True if removal succeeded, False if not enough
        """
        if item_id not in self.items:
            return False
        
        if self.items[item_id] < quantity:
            return False
        
        self.items[item_id] -= quantity
        
        # Remove entry if quantity reaches 0
        if self.items[item_id] <= 0:
            del self.items[item_id]
        
        return True
    
    
    def get_quantity(self, item_id):
        """
        Return owned quantity of an item.
        
        Args:
            item_id: item ID
        
        Returns:
            int (0 if not owned)
        """
        return self.items.get(item_id, 0)
    
    
    def has(self, item_id):
        """True if player owns at least 1 of this item."""
        return self.get_quantity(item_id) > 0
    
    
    def get_all(self):
        """
        Return complete inventory content.
        Each entry is (Item object, quantity).
        
        Returns:
            list of (Item, int) tuples
        """
        content = []
        
        for item_id, qty in self.items.items():
            item = self.item_catalog.get_item(item_id)
            if item is not None:
                content.append((item, qty))
        
        return content
    
    
    def get_by_category(self, category):
        """
        Return items of a given category that player owns.
        
        Args:
            category: "heal", "pokeball", "boost", "revive", "status"
        
        Returns:
            list of (Item, quantity) tuples
        """
        result = []
        
        for item_id, qty in self.items.items():
            item = self.item_catalog.get_item(item_id)
            if item is not None and item.category == category:
                result.append((item, qty))
        
        return result
    
    
    def get_usable_in_combat(self):
        """
        Return all items usable in combat that player owns.
        
        Returns:
            list of (Item, quantity) tuples
        """
        result = []
        
        for item_id, qty in self.items.items():
            item = self.item_catalog.get_item(item_id)
            if item is not None and item.usable_in_combat:
                result.append((item, qty))
        
        return result
    
    
    def get_usable_outside_combat(self):
        """
        Return all items usable outside combat.
        
        Returns:
            list of (Item, quantity) tuples
        """
        result = []
        
        for item_id, qty in self.items.items():
            item = self.item_catalog.get_item(item_id)
            if item is not None and item.usable_outside_combat:
                result.append((item, qty))
        
        return result
    
    
    def has_pokeballs(self):
        """True if player owns at least one Poke Ball."""
        for item_id, qty in self.items.items():
            item = self.item_catalog.get_item(item_id)
            if item is not None and item.is_pokeball and qty > 0:
                return True
        return False
    
    
    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------
    
    def to_dict(self):
        """
        Convert inventory to dict for save.
        
        Format: {"items": {"1": 3, "4": 5, ...}}
        """
        items_str = {}
        for item_id, qty in self.items.items():
            items_str[str(item_id)] = qty
        
        return {"items": items_str}
    
    
    @classmethod
    def from_dict(cls, data, item_catalog):
        """
        Recreate inventory from save dict.
        
        Args:
            data: dict {"items": {"1": 3, "4": 5}}
            item_catalog: ItemCatalog for validation
        
        Returns:
            Inventory instance
        """
        inv = cls(item_catalog)
        
        items_data = data.get("items", {})
        for item_id_str, qty in items_data.items():
            try:
                item_id = int(item_id_str)
                # Verify item still exists in catalog
                if item_catalog.get_item(item_id) is not None:
                    inv.items[item_id] = qty
                else:
                    print(f"Warning: Item {item_id} from save no longer exists")
            except Exception:
                print(f"Warning: Invalid item ID in save: {item_id_str}")
        
        return inv
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __len__(self):
        """Number of different item types in inventory."""
        return len(self.items)
    
    
    def __str__(self):
        """Debug representation."""
        if self.is_empty:
            return "Inventory (empty)"
        
        descriptions = []
        for item_id, qty in self.items.items():
            item = self.item_catalog.get_item(item_id)
            if item is not None:
                descriptions.append(f"{item.name} ×{qty}")
        
        return f"Inventory ({len(self.items)} types, {self.total_count} items): {', '.join(descriptions)}"