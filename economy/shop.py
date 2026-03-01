# =============================================================================
# SHOP.PY - SHOP LOGIC
# =============================================================================
#
# Handles shop purchases. Receives catalog and player, performs transactions.

class Shop:
    """
    Shop logic. Handles catalog display and purchases.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, item_catalog, player):
        """
        Initialize shop.
        
        Args:
            item_catalog: ItemCatalog object (all item data)
            player: Player object (for credits and inventory)
        """
        self.item_catalog = item_catalog
        self.player = player
        
        # Build shop catalog once at opening
        self.catalog = item_catalog.get_buyable_items()
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def get_catalog(self):
        """
        Return list of items available for purchase.
        Each entry is an Item object with all properties.
        
        Used by state_shop.py to build display.
        """
        return self.catalog
    
    
    def get_player_credits(self):
        """Return player's current credits."""
        return self.player.credits
    
    
    def get_owned_quantity(self, item_id):
        """
        Return quantity of an item already owned.
        Displayed next to price: "Potion — 25 credits (x3)"
        
        Args:
            item_id: item ID
        """
        return self.player.inventory.get_quantity(item_id)
    
    
    def can_afford(self, item_id):
        """
        Check if player can afford an item.
        
        Args:
            item_id: item ID to check
        
        Returns:
            True if affordable, False otherwise
        """
        item = self.item_catalog.get_item(item_id)
        
        if item is None:
            return False
        
        if not item.buyable:
            return False
        
        return self.player.credits >= item.price
    
    
    def buy(self, item_id):
        """
        Purchase an item.
        
        Steps:
        1. Check if purchase is possible
        2. Deduct credits
        3. Add item to inventory
        
        Args:
            item_id: item ID to buy
        
        Returns:
            dict with result:
            {
                "success": bool,
                "item": Item or None,
                "price_paid": int,
                "credits_left": int,
                "failure_reason": str or None
            }
        """
        item = self.item_catalog.get_item(item_id)
        
        # Check: item exists?
        if item is None:
            return {
                "success": False,
                "item": None,
                "price_paid": 0,
                "credits_left": self.player.credits,
                "failure_reason": "unknown_item"
            }
        
        # Check: item is buyable?
        if not item.buyable:
            return {
                "success": False,
                "item": item,
                "price_paid": 0,
                "credits_left": self.player.credits,
                "failure_reason": "not_buyable"
            }
        
        # Check: enough credits?
        if self.player.credits < item.price:
            return {
                "success": False,
                "item": item,
                "price_paid": 0,
                "credits_left": self.player.credits,
                "failure_reason": "insufficient_credits"
            }
        
        # All good → perform transaction
        self.player.credits -= item.price
        self.player.inventory.add(item.id)
        
        return {
            "success": True,
            "item": item,
            "price_paid": item.price,
            "credits_left": self.player.credits,
            "failure_reason": None
        }
    
    
    def get_item_info(self, item_id):
        """
        Return full info for an item (display details).
        
        When player hovers over an item, show:
        - description
        - effect
        - price
        - owned quantity
        
        Args:
            item_id: item ID
        
        Returns:
            dict with all info, or None if not found
        """
        item = self.item_catalog.get_item(item_id)
        
        if item is None:
            return None
        
        return {
            "item": item,
            "name": item.name,
            "description": item.get_formatted_description(),
            "price": item.price,
            "owned_quantity": self.get_owned_quantity(item.id),
            "can_afford": self.can_afford(item.id),
            "player_credits": self.player.credits
        }
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """Debug representation."""
        return f"Shop ({len(self.catalog)} items) — Player credits: {self.player.credits}"