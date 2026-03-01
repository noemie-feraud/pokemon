# =============================================================================
# CREDITS_MANAGER.PY - CREDITS MANAGER
# =============================================================================
#
# Manages player's credits. Centralizes all credit operations:
# - Add credits (victory, quests)
# - Remove credits (purchase, tournament entry)
# - Check if player can afford
# - Format for display

class CreditsManager:
    """
    Manages player's credits. Centralizes all operations.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, initial_balance=0):
        """
        Initialize credits manager.
        
        Args:
            initial_balance: starting credits (0 for new game, loaded from save)
        """
        self.balance = initial_balance
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def get_balance(self):
        """Return current balance."""
        return self.balance
    
    
    def add(self, amount, source=None):
        """
        Add credits to balance.
        
        Args:
            amount: credits to add (must be positive)
            source: optional debug source ("trainer_victory", "quest_reward", etc.)
        
        Returns:
            new balance
        """
        if amount < 0:
            print(f"Warning: Attempted to add negative credits: {amount}")
            amount = abs(amount)  # convert to positive as safety
        
        self.balance += amount
        
        # Optional logging
        if source is not None:
            self._log_transaction("add", amount, source)
        
        return self.balance
    
    
    def remove(self, amount, source=None):
        """
        Remove credits from balance.
        
        Args:
            amount: credits to remove
            source: optional debug source
        
        Returns:
            True if removal succeeded, False if insufficient funds
        """
        if amount < 0:
            print(f"Warning: Attempted to remove negative credits: {amount}")
            amount = abs(amount)
        
        if not self.can_afford(amount):
            return False
        
        self.balance -= amount
        
        if source is not None:
            self._log_transaction("remove", amount, source)
        
        return True
    
    
    def can_afford(self, amount):
        """Check if player has enough credits."""
        return self.balance >= amount
    
    
    def transfer_to(self, target, amount):
        """
        Transfer credits to another CreditsManager.
        (Not used for now, but could be for player-to-player trades)
        
        Args:
            target: another CreditsManager
            amount: amount to transfer
        
        Returns:
            True if transfer succeeded, False otherwise
        """
        if not self.can_afford(amount):
            return False
        
        self.remove(amount, source="transfer_out")
        target.add(amount, source="transfer_in")
        return True
    
    
    def format_balance(self):
        """
        Format balance for display.
        
        Examples:
            150 → "150"
            1250 → "1 250"
            1000000 → "1 000 000"
        
        Returns:
            formatted string with spaces every 3 digits
        """
        balance_str = str(self.balance)
        result = ""
        length = len(balance_str)
        
        for i, digit in enumerate(balance_str):
            result += digit
            # Add space every 3 digits from the right
            pos_from_end = length - i - 1
            if pos_from_end > 0 and pos_from_end % 3 == 0:
                result += " "
        
        return result
    
    
    def reset(self):
        """Reset credits to zero (new game)."""
        self.balance = 0
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _log_transaction(self, transaction_type, amount, source):
        """
        Log transaction for debugging.
        """
        # Debug mode only
        if True:  # Replace with DEBUG flag from settings
            print(f"[Credits] {transaction_type} {amount} credits - Source: {source} - New balance: {self.balance}")
    
    
    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------
    
    def to_dict(self):
        """Convert to dict for save."""
        return {
            "balance": self.balance
        }
    
    
    @classmethod
    def from_dict(cls, data):
        """Recreate from save dict."""
        balance = data.get("balance", 0)
        return cls(balance)
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        return f"CreditsManager: {self.balance} credits"
    
    
    def __repr__(self):
        return self.__str__()