# =============================================================================
# DAMAGE_CALCULATOR.PY - DAMAGE CALCULATION
# =============================================================================
#
# Calculates damage inflicted by an attack.
# Pure logic, no display.

import random
from config.settings import MISS_CHANCE, MIN_DAMAGE, STAB_BONUS
from config.type_chart import get_multiplier


# =============================================================================
# DAMAGE CALCULATION
# =============================================================================

def calculate_damage(attacker, defender, attack, day_night_cycle,
                     attacker_boosts=None, defender_boosts=None):
    """
    Calculate damage for an attack.
    
    Args:
        attacker: attacking Pokemon
        defender: defending Pokemon
        attack: attack dict with "name", "type", "power"
        day_night_cycle: DayNightCycle object (for penalty)
        attacker_boosts: dict {"attack": 0, "defense": 0} (temporary boosts)
        defender_boosts: same for defender
    
    Returns:
        dict with all result info:
        {
            "damage": int,
            "hit": bool,
            "miss": bool,
            "type_multiplier": float,
            "super_effective": bool,
            "not_very_effective": bool,
            "immune": bool,
            "stab": bool
        }
    """
    # Default boosts
    if attacker_boosts is None:
        attacker_boosts = {"attack": 0, "defense": 0}
    if defender_boosts is None:
        defender_boosts = {"attack": 0, "defense": 0}
    
    # -------------------------------------------------------------------------
    # STEP 1: CHECK MISS
    # -------------------------------------------------------------------------
    if random.random() < MISS_CHANCE:
        return {
            "damage": 0,
            "hit": False,
            "miss": True,
            "type_multiplier": 1.0,
            "super_effective": False,
            "not_very_effective": False,
            "immune": False,
            "stab": False
        }
    
    # -------------------------------------------------------------------------
    # STEP 2: GET STATS WITH BOOSTS
    # -------------------------------------------------------------------------
    # Boost of 25 = +25% → multiply by 1.25
    attack_stat = attacker.attack * (1 + attacker_boosts["attack"] / 100)
    defense_stat = defender.defense * (1 + defender_boosts["defense"] / 100)
    
    # Safety: defense can't be 0
    if defense_stat < 1:
        defense_stat = 1
    
    # -------------------------------------------------------------------------
    # STEP 3: BASE DAMAGE
    # -------------------------------------------------------------------------
    # Formula: (power × attack) / (defense × 0.5)
    # The 0.5 factor on defense makes combat more dynamic
    power = attack.get("power") or 0

    # Status moves (power=None or 0) deal no damage
    if power == 0:
        return {
            "damage": 0,
            "hit": True,
            "miss": False,
            "type_multiplier": 1.0,
            "super_effective": False,
            "not_very_effective": False,
            "immune": False,
            "stab": False
        }

    base_damage = (power * attack_stat) / (defense_stat * 0.5)
    
    # -------------------------------------------------------------------------
    # STEP 4: TYPE MULTIPLIER
    # -------------------------------------------------------------------------
    attack_type = attack["type"]
    type_multiplier = 1.0
    
    for def_type in defender.types:
        mult = get_multiplier(attack_type, def_type)
        type_multiplier *= mult
    
    # -------------------------------------------------------------------------
    # STEP 5: CHECK IMMUNITY
    # -------------------------------------------------------------------------
    if type_multiplier == 0:
        return {
            "damage": 0,
            "hit": True,
            "miss": False,
            "type_multiplier": 0,
            "super_effective": False,
            "not_very_effective": False,
            "immune": True,
            "stab": False
        }
    
    # -------------------------------------------------------------------------
    # STEP 6: STAB BONUS (Same Type Attack Bonus)
    # -------------------------------------------------------------------------
    stab = False
    if attack_type in attacker.types:
        stab = True
    
    stab_mult = STAB_BONUS if stab else 1.0
    
    # -------------------------------------------------------------------------
    # STEP 7: DAY/NIGHT PENALTY
    # -------------------------------------------------------------------------
    day_night_mult = 1.0
    if day_night_cycle is not None:
        day_night_mult = day_night_cycle.get_penalty(attacker.day_night)
    
    # -------------------------------------------------------------------------
    # STEP 8: RANDOM VARIATION
    # -------------------------------------------------------------------------
    # Factor between 0.85 and 1.0 (like real Pokemon)
    variation = random.uniform(0.85, 1.0)
    
    # -------------------------------------------------------------------------
    # STEP 9: FINAL DAMAGE
    # -------------------------------------------------------------------------
    final_damage = base_damage * type_multiplier * stab_mult * day_night_mult * variation
    final_damage = int(final_damage)
    
    # Apply minimum damage (unless immune, already handled)
    if final_damage < MIN_DAMAGE:
        final_damage = MIN_DAMAGE
    
    # -------------------------------------------------------------------------
    # STEP 10: BUILD RESULT
    # -------------------------------------------------------------------------
    return {
        "damage": final_damage,
        "hit": True,
        "miss": False,
        "type_multiplier": type_multiplier,
        "super_effective": type_multiplier > 1.0,
        "not_very_effective": type_multiplier < 1.0,
        "immune": False,
        "stab": stab
    }


# =============================================================================
# XP CALCULATION
# =============================================================================

def calculate_xp_gained(defeated_pokemon):
    """
    Calculate XP gained after defeating a Pokemon.
    
    Formula: defeated_level × 10
    
    Level 5 gives 50 XP, level 20 gives 200 XP.
    Beating stronger Pokemon gives more XP.
    
    Args:
        defeated_pokemon: the Pokemon that was KO'd
    
    Returns:
        int: XP gained
    """
    return defeated_pokemon.level * 10