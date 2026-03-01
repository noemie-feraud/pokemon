# =============================================================================
# CAPTURE_SYSTEM.PY - POKEMON CAPTURE SYSTEM
# =============================================================================
#
# Handles wild Pokemon capture attempts.

import random


# =============================================================================
# CAPTURE FUNCTIONS
# =============================================================================

def attempt_capture(target_pokemon, ball, player_team, player_storage, combat_type):
    """
    Attempt to capture a wild Pokemon.
    
    Args:
        target_pokemon: Pokemon object (the wild Pokemon)
        ball: Item object (the Poke Ball used)
        player_team: player's Team object
        player_storage: player's Storage object
        combat_type: "wild" or "trainer"
    
    Returns:
        dict with result info:
        {
            "capture_success": bool,
            "captured_pokemon": Pokemon or None,
            "destination": "team" or "storage" or None,
            "capture_rate": float (ball's rate),
            "random_roll": float (for debug),
            "failure_reason": str or None ("trainer_combat", "miss", None)
        }
    """
    # -------------------------------------------------------------------------
    # STEP 1: CHECK COMBAT TYPE
    # -------------------------------------------------------------------------
    # Can only capture in wild combat
    if combat_type != "wild":
        return {
            "capture_success": False,
            "captured_pokemon": None,
            "destination": None,
            "capture_rate": 0,
            "random_roll": 0,
            "failure_reason": "trainer_combat"
        }
    
    # -------------------------------------------------------------------------
    # STEP 2: GET CAPTURE RATE
    # -------------------------------------------------------------------------
    # Rate comes from Item object (Poke Ball)
    # effect_value contains percentage: 30, 60, 80, 100
    # Convert to float between 0 and 1
    capture_rate = ball.effect_value / 100
    
    # -------------------------------------------------------------------------
    # STEP 3: ROLL THE DICE
    # -------------------------------------------------------------------------
    random_roll = random.random()
    
    if random_roll > capture_rate:
        # Capture failed
        return {
            "capture_success": False,
            "captured_pokemon": None,
            "destination": None,
            "capture_rate": capture_rate,
            "random_roll": random_roll,
            "failure_reason": "miss"
        }
    
    # -------------------------------------------------------------------------
    # STEP 4: CAPTURE SUCCESS — ADD POKEMON
    # -------------------------------------------------------------------------
    # Pokemon is captured. Add to team or storage.
    
    destination = None
    
    if not player_team.is_full:
        player_team.add(target_pokemon)
        destination = "team"
    else:
        player_storage.add(target_pokemon)
        destination = "storage"
    
    # -------------------------------------------------------------------------
    # STEP 5: RETURN RESULT
    # -------------------------------------------------------------------------
    return {
        "capture_success": True,
        "captured_pokemon": target_pokemon,
        "destination": destination,
        "capture_rate": capture_rate,
        "random_roll": random_roll,
        "failure_reason": None
    }


def can_attempt_capture(combat_type, inventory):
    """
    Check if player can attempt capture in current context.
    
    Conditions:
    1. Combat is wild (not trainer)
    2. Player has at least one Poke Ball
    
    Args:
        combat_type: "wild" or "trainer"
        inventory: player's Inventory object
    
    Returns:
        True if capture possible, False otherwise
    """
    if combat_type != "wild":
        return False
    
    return inventory.has_pokeballs()


def get_available_balls(inventory):
    """
    Return list of Poke Balls the player owns.
    Used by state_combat.py to show capture menu.
    
    Returns:
        list of (Item, quantity) tuples sorted by capture rate
    """
    balls = inventory.get_by_category("pokeball")
    
    # Sort by capture rate ascending (Poke Ball first, Master Ball last)
    balls.sort(key=lambda item_qty: item_qty[0].effect_value)
    
    return balls


def calculate_shake_count(capture_success, capture_rate, random_roll):
    """
    Calculate number of shakes before result.
    Cosmetic only — doesn't affect capture outcome.
    
    In real Pokemon, ball shakes 0, 1, 2, or 3 times.
    More shakes = more suspense.
    
    For us:
    - Success → always 3 shakes + lock
    - Failure → 0 to 2 shakes depending on how close the roll was
    
    Args:
        capture_success: bool
        capture_rate: float (0.0 to 1.0)
        random_roll: float (0.0 to 1.0)
    
    Returns:
        int between 0 and 3
    """
    if capture_success:
        return 3
    
    if capture_rate == 0:
        return 0
    
    # How close was the roll to the rate?
    # Closer = more shakes for suspense
    ratio = random_roll / capture_rate    # > 1 since random_roll > capture_rate
    
    if ratio < 1.3:
        # Very close → 2 shakes ("almost!")
        return 2
    
    if ratio < 2.0:
        # Moderately close → 1 shake
        return 1
    
    # Far from rate → 0 shakes ("it broke out immediately")
    return 0