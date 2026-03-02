# =============================================================================
# NPC_SHOPKEEPER.PY - SHOPKEEPER NPC CLASS
# =============================================================================
#
# Shopkeeper at the Pokemon Mart. Opens shop interface.

from entities.npc import NPC


# =============================================================================
# SHOPKEEPER NPC CLASS
# =============================================================================

class NPCShopkeeper(NPC):
    """
    Shopkeeper at the Pokemon Mart.
    Opens shop interface after dialogue.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, data):
        """
        Initialize shopkeeper.
        
        Args:
            data: dict from npcs.json
        """
        super().__init__(data)

        # If no "talk" dialogue in data, load from SHOPKEEPER_DIALOGUES
        if "talk" not in self.dialogues:
            try:
                from data.trainer_dialogues import SHOPKEEPER_DIALOGUES
                shop_dlg = SHOPKEEPER_DIALOGUES.get(self.name)
                if shop_dlg:
                    self.dialogues.update(shop_dlg)
            except Exception:
                pass
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def on_dialogue_end(self, game_manager):
        """
        Called when welcome dialogue ends.
        Opens the shop by pushing StateShop.
        
        StateShop receives:
        - game_manager: to access player (credits, inventory)
        - self: reference to shopkeeper, to get contextual dialogues
               ("no_money", "purchase") and display them at right time
        
        When player closes shop, StateShop pops itself
        and we return to exploration.
        """
        # Import here to avoid circular imports
        from states.state_shop import StateShop
        
        shop_state = StateShop(game_manager, self)
        game_manager.state_manager.push(shop_state)
    
    
    def get_purchase_dialogue(self):
        """Return dialogue after successful purchase."""
        return self.dialogues.get("purchase", ["Thank you for your purchase!"])
    
    
    def get_no_money_dialogue(self):
        """Return dialogue when player doesn't have enough credits."""
        return self.dialogues.get("no_money", ["You don't have enough credits..."])