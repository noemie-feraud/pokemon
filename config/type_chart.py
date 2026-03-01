# =============================================================================
# TYPE_CHART.PY - POKEMON TYPE CHART
# =============================================================================
#
# Defines type effectiveness multipliers for all 18 Pokemon types.
# Used by damage_calculator.py to compute damage.
# No dependencies — pure data.

# Type multipliers:
# 2.0  = Super effective
# 1.0  = Neutral
# 0.5  = Not very effective
# 0.0  = Immune

TYPE_CHART = {
    "normal": {
        "normal": 1.0, "fire": 1.0, "water": 1.0, "electric": 1.0, "grass": 1.0,
        "ice": 1.0, "fighting": 1.0, "poison": 1.0, "ground": 1.0, "flying": 1.0,
        "psychic": 1.0, "bug": 1.0, "rock": 0.5, "ghost": 0.0, "dragon": 1.0,
        "dark": 1.0, "steel": 0.5, "fairy": 1.0
    },
    "fire": {
        "normal": 1.0, "fire": 0.5, "water": 0.5, "electric": 1.0, "grass": 2.0,
        "ice": 2.0, "fighting": 1.0, "poison": 1.0, "ground": 1.0, "flying": 1.0,
        "psychic": 1.0, "bug": 2.0, "rock": 0.5, "ghost": 1.0, "dragon": 0.5,
        "dark": 1.0, "steel": 2.0, "fairy": 1.0
    },
    "water": {
        "normal": 1.0, "fire": 2.0, "water": 0.5, "electric": 1.0, "grass": 0.5,
        "ice": 1.0, "fighting": 1.0, "poison": 1.0, "ground": 2.0, "flying": 1.0,
        "psychic": 1.0, "bug": 1.0, "rock": 2.0, "ghost": 1.0, "dragon": 0.5,
        "dark": 1.0, "steel": 1.0, "fairy": 1.0
    },
    "electric": {
        "normal": 1.0, "fire": 1.0, "water": 2.0, "electric": 0.5, "grass": 0.5,
        "ice": 1.0, "fighting": 1.0, "poison": 1.0, "ground": 0.0, "flying": 2.0,
        "psychic": 1.0, "bug": 1.0, "rock": 1.0, "ghost": 1.0, "dragon": 0.5,
        "dark": 1.0, "steel": 1.0, "fairy": 1.0
    },
    "grass": {
        "normal": 1.0, "fire": 0.5, "water": 2.0, "electric": 1.0, "grass": 0.5,
        "ice": 1.0, "fighting": 1.0, "poison": 0.5, "ground": 2.0, "flying": 0.5,
        "psychic": 1.0, "bug": 0.5, "rock": 2.0, "ghost": 1.0, "dragon": 0.5,
        "dark": 1.0, "steel": 0.5, "fairy": 1.0
    },
    "ice": {
        "normal": 1.0, "fire": 0.5, "water": 0.5, "electric": 1.0, "grass": 2.0,
        "ice": 0.5, "fighting": 1.0, "poison": 1.0, "ground": 2.0, "flying": 2.0,
        "psychic": 1.0, "bug": 1.0, "rock": 1.0, "ghost": 1.0, "dragon": 2.0,
        "dark": 1.0, "steel": 0.5, "fairy": 1.0
    },
    "fighting": {
        "normal": 2.0, "fire": 1.0, "water": 1.0, "electric": 1.0, "grass": 1.0,
        "ice": 2.0, "fighting": 1.0, "poison": 0.5, "ground": 1.0, "flying": 0.5,
        "psychic": 0.5, "bug": 0.5, "rock": 2.0, "ghost": 0.0, "dragon": 1.0,
        "dark": 2.0, "steel": 2.0, "fairy": 0.5
    },
    "poison": {
        "normal": 1.0, "fire": 1.0, "water": 1.0, "electric": 1.0, "grass": 2.0,
        "ice": 1.0, "fighting": 1.0, "poison": 0.5, "ground": 0.5, "flying": 1.0,
        "psychic": 1.0, "bug": 1.0, "rock": 0.5, "ghost": 0.5, "dragon": 1.0,
        "dark": 1.0, "steel": 0.0, "fairy": 2.0
    },
    "ground": {
        "normal": 1.0, "fire": 2.0, "water": 1.0, "electric": 2.0, "grass": 0.5,
        "ice": 1.0, "fighting": 1.0, "poison": 2.0, "ground": 1.0, "flying": 0.0,
        "psychic": 1.0, "bug": 0.5, "rock": 2.0, "ghost": 1.0, "dragon": 1.0,
        "dark": 1.0, "steel": 2.0, "fairy": 1.0
    },
    "flying": {
        "normal": 1.0, "fire": 1.0, "water": 1.0, "electric": 0.5, "grass": 2.0,
        "ice": 1.0, "fighting": 2.0, "poison": 1.0, "ground": 1.0, "flying": 1.0,
        "psychic": 1.0, "bug": 2.0, "rock": 0.5, "ghost": 1.0, "dragon": 1.0,
        "dark": 1.0, "steel": 0.5, "fairy": 1.0
    },
    "psychic": {
        "normal": 1.0, "fire": 1.0, "water": 1.0, "electric": 1.0, "grass": 1.0,
        "ice": 1.0, "fighting": 2.0, "poison": 2.0, "ground": 1.0, "flying": 1.0,
        "psychic": 0.5, "bug": 1.0, "rock": 1.0, "ghost": 1.0, "dragon": 1.0,
        "dark": 0.0, "steel": 0.5, "fairy": 1.0
    },
    "bug": {
        "normal": 1.0, "fire": 0.5, "water": 1.0, "electric": 1.0, "grass": 2.0,
        "ice": 1.0, "fighting": 0.5, "poison": 0.5, "ground": 1.0, "flying": 0.5,
        "psychic": 2.0, "bug": 1.0, "rock": 1.0, "ghost": 0.5, "dragon": 1.0,
        "dark": 2.0, "steel": 0.5, "fairy": 0.5
    },
    "rock": {
        "normal": 1.0, "fire": 2.0, "water": 1.0, "electric": 1.0, "grass": 1.0,
        "ice": 2.0, "fighting": 0.5, "poison": 1.0, "ground": 0.5, "flying": 2.0,
        "psychic": 1.0, "bug": 2.0, "rock": 1.0, "ghost": 1.0, "dragon": 1.0,
        "dark": 1.0, "steel": 0.5, "fairy": 1.0
    },
    "ghost": {
        "normal": 0.0, "fire": 1.0, "water": 1.0, "electric": 1.0, "grass": 1.0,
        "ice": 1.0, "fighting": 1.0, "poison": 1.0, "ground": 1.0, "flying": 1.0,
        "psychic": 2.0, "bug": 1.0, "rock": 1.0, "ghost": 2.0, "dragon": 1.0,
        "dark": 0.5, "steel": 0.5, "fairy": 1.0
    },
    "dragon": {
        "normal": 1.0, "fire": 1.0, "water": 1.0, "electric": 1.0, "grass": 1.0,
        "ice": 1.0, "fighting": 1.0, "poison": 1.0, "ground": 1.0, "flying": 1.0,
        "psychic": 1.0, "bug": 1.0, "rock": 1.0, "ghost": 1.0, "dragon": 2.0,
        "dark": 1.0, "steel": 0.5, "fairy": 0.0
    },
    "dark": {
        "normal": 1.0, "fire": 1.0, "water": 1.0, "electric": 1.0, "grass": 1.0,
        "ice": 1.0, "fighting": 0.5, "poison": 1.0, "ground": 1.0, "flying": 1.0,
        "psychic": 2.0, "bug": 1.0, "rock": 1.0, "ghost": 2.0, "dragon": 1.0,
        "dark": 0.5, "steel": 0.5, "fairy": 0.5
    },
    "steel": {
        "normal": 1.0, "fire": 0.5, "water": 0.5, "electric": 0.5, "grass": 1.0,
        "ice": 2.0, "fighting": 1.0, "poison": 1.0, "ground": 1.0, "flying": 1.0,
        "psychic": 1.0, "bug": 1.0, "rock": 2.0, "ghost": 1.0, "dragon": 1.0,
        "dark": 1.0, "steel": 0.5, "fairy": 2.0
    },
    "fairy": {
        "normal": 1.0, "fire": 0.5, "water": 1.0, "electric": 1.0, "grass": 1.0,
        "ice": 1.0, "fighting": 2.0, "poison": 0.5, "ground": 1.0, "flying": 1.0,
        "psychic": 1.0, "bug": 1.0, "rock": 1.0, "ghost": 1.0, "dragon": 2.0,
        "dark": 2.0, "steel": 0.5, "fairy": 1.0
    }
}


# =============================================================================
# HELPER FUNCTION
# =============================================================================

def get_multiplier(attack_type, defense_type):
    """
    Return type effectiveness multiplier.
    
    Args:
        attack_type: type of the attack (string)
        defense_type: type of the defending Pokemon (string)
    
    Returns:
        float: 2.0, 1.0, 0.5, or 0.0
    
    Example:
        get_multiplier("fire", "grass") → 2.0
        get_multiplier("fire", "water") → 0.5
    """
    # Normalize to lowercase
    attack_type = attack_type.lower()
    defense_type = defense_type.lower()
    
    # Safety: if type not in chart, return neutral
    if attack_type not in TYPE_CHART:
        return 1.0
    
    if defense_type not in TYPE_CHART[attack_type]:
        return 1.0
    
    return TYPE_CHART[attack_type][defense_type]