# =============================================================================
# POKEMON.PY - POKEMON ENTITY CLASS
# =============================================================================
#
# This is THE central file of the project.
# The Pokemon class represents a Pokemon in the game:
# - stats, types, attacks
# - XP, level, evolution
# - status conditions

import math
from config.settings import ATTACKS_PER_STAGE


# =============================================================================
# POKEMON CLASS
# =============================================================================

class Pokemon:
    """
    Represents a Pokemon with all its characteristics.
    Data model with progression logic (XP, level up, evolution).
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, data):
        """
        Initialize Pokemon from data dictionary.
        
        Args:
            data: dict from pokemon.json or save file
        """
        
        # --- IDENTITY ---
        self.id = data["id"]
        self.original_name = data["name_original"]
        self.name = data["name_custom"]          # humorous name displayed in game
        self.types = data["types"]                # list of 1 or 2 types
        
        # --- EVOLUTION STAGE ---
        # 1, 2 or 3. Determines max attacks and appearance.
        self.evolution_stage = data.get("evolution_stage", 1)
        
        # --- BASE STATS ---
        # Raw species stats at level 1.
        # Change only when evolving (replaced by evolved form's base stats).
        self.base_hp = data["base_stats"]["hp"]
        self.base_attack = data["base_stats"]["attack"]
        self.base_defense = data["base_stats"]["defense"]
        
        # --- LEVEL & XP ---
        self.level = data.get("level", 1)
        self.current_xp = data.get("xp", 0)
        self.xp_for_next_level = self._compute_xp_for_next_level()
        
        # --- CURRENT STATS ---
        # Calculated from base stats and level.
        # If loading from save, recalc to ensure consistency.
        self.max_hp = self._compute_stat(self.base_hp)
        self.attack = self._compute_stat(self.base_attack)
        self.defense = self._compute_stat(self.base_defense)
        self.speed = self._compute_stat(50)  # placeholder, not used yet
        
        # Current HP: from save if provided, else full HP
        self.current_hp = data.get("current_hp", self.max_hp)
        
        # --- ATTACKS ---
        # List of dicts {"name": ..., "type": ..., "power": ...}
        # Number limited by evolution stage.
        self.attacks = data.get("attacks", [])
        max_attacks = ATTACKS_PER_STAGE[self.evolution_stage]
        # Auto-populate from all_attacks if no explicit attacks provided
        if not self.attacks:
            all_atk = data.get("all_attacks", [])
            self.attacks = all_atk[:max_attacks]
        else:
            self.attacks = self.attacks[:max_attacks]
        
        # --- EVOLUTION ---
        # dict {"to": evolution_id, "level": required_level}
        # None if final stage (stage 3).
        self.evolution_data = data.get("evolution", None)
        
        # --- ALL POSSIBLE ATTACKS ---
        # Full list of attacks this Pokemon can learn.
        # Stored to pick one when evolving.
        self.all_attacks = data.get("all_attacks", [])
        
        # --- DAY/NIGHT ---
        # "diurne" or "nocturne", determined by type in JSON.
        self.day_night = data.get("day_night", "diurne")
        
        # --- STATUS ---
        # None = no status. Otherwise: "poison", "burn", "paralysis", etc.
        self.status = data.get("status", None)
        
        # --- SPRITES ---
        # Paths to images. UI classes load them, we just store paths.
        self.sprite_front = data.get("sprite_front", "")
        self.sprite_back = data.get("sprite_back", "")
    
    
    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------
    
    @property
    def is_ko(self):
        """Return True if Pokemon is KO (0 HP)."""
        return self.current_hp <= 0
    
    
    @property
    def is_full_hp(self):
        """Return True if Pokemon is at max HP."""
        return self.current_hp >= self.max_hp
    
    
    @property
    def can_evolve(self):
        """
        Return True if Pokemon can evolve now.
        Conditions:
        1. Has evolution data (not final stage)
        2. Level >= required level
        """
        if self.evolution_data is None:
            return False
        return self.level >= self.evolution_data["level"]
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _compute_stat(self, base_stat):
        """
        Calculate current stat from base stat and level.
        
        Formula:
            bonus_per_level = base_stat / 10 (rounded up, min 1)
            current_stat = base_stat + (level × bonus_per_level)
        
        Example: base_attack = 49, level = 10
            bonus = ceil(49 / 10) = 5
            stat = 49 + (10 × 5) = 99
        
        Simple but effective. High base stats progress faster,
        rewarding players who evolve their Pokemon.
        """
        bonus = max(1, math.ceil(base_stat / 10))
        return base_stat + (self.level * bonus)
    
    
    def _compute_xp_for_next_level(self):
        """
        Calculate XP threshold for next level up.
        
        Formula: current_level × 20
        
        Level 1 → 20 XP, level 5 → 100 XP, level 15 → 300 XP.
        Linear, simple, gives natural progression.
        """
        return self.level * 20
    
    
    def _learn_new_attack(self):
        """
        When evolving, gain a new attack slot and learn one automatically.
        Pick from all_attacks the first one not already known.
        
        Returns:
            name of learned attack, or None if none learned
        """
        max_attacks = ATTACKS_PER_STAGE[self.evolution_stage]
        
        # Check if we have room
        if len(self.attacks) >= max_attacks:
            return None
        
        # Find an attack we don't know yet
        current_names = [a["name"] for a in self.attacks]
        
        for attack in self.all_attacks:
            if attack["name"] not in current_names:
                self.attacks.append(attack)
                return attack["name"]
        
        return None
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def recalc_stats(self):
        """
        Recalculate all current stats from base stats and level.
        Called after level up or evolution.
        
        For HP, calculate difference between old max and new max.
        Add difference to current HP.
        This way, level up doesn't fully heal, but Pokemon gains bonus HP.
        
        Example:
            Before: max_hp = 80, current_hp = 50
            After level up: max_hp = 85
            Difference = 85 - 80 = 5
            current_hp = 50 + 5 = 55
        """
        old_max_hp = self.max_hp
        
        self.max_hp = self._compute_stat(self.base_hp)
        self.attack = self._compute_stat(self.base_attack)
        self.defense = self._compute_stat(self.base_defense)
        self.speed = self._compute_stat(50)
        
        # Add HP bonus
        hp_diff = self.max_hp - old_max_hp
        self.current_hp += hp_diff
        
        # Safety: current HP never exceeds max
        if self.current_hp > self.max_hp:
            self.current_hp = self.max_hp
    
    
    def gain_xp(self, xp_gained):
        """
        Add XP to Pokemon. If threshold reached, trigger level up(s).
        
        Args:
            xp_gained: amount of XP to add (from combat.py)
        
        Returns:
            dict with info about what happened:
            {
                "level_ups": number of levels gained,
                "old_level": level before,
                "new_level": level after,
                "evolution": True/False (if can evolve now)
            }
        """
        old_level = self.level
        level_ups = 0
        
        self.current_xp += xp_gained
        
        # Loop: can gain multiple levels at once if XP is high
        while self.current_xp >= self.xp_for_next_level:
            self.current_xp -= self.xp_for_next_level
            self.level += 1
            level_ups += 1
            self.xp_for_next_level = self._compute_xp_for_next_level()
            self.recalc_stats()
        
        return {
            "level_ups": level_ups,
            "old_level": old_level,
            "new_level": self.level,
            "evolution": self.can_evolve
        }
    
    
    def evolve(self, evolution_data):
        """
        Evolve Pokemon to next form.
        
        Args:
            evolution_data: complete dict of evolved Pokemon from pokemon.json
        
        Returns:
            name of new attack learned (for display)
        """
        # Keep HP ratio to avoid free heal
        hp_ratio = self.current_hp / self.max_hp if self.max_hp > 0 else 1.0
        
        # Update identity
        self.id = evolution_data["id"]
        self.original_name = evolution_data["name_original"]
        self.name = evolution_data["name_custom"]
        self.sprite_front = evolution_data["sprite_front"]
        self.sprite_back = evolution_data["sprite_back"]
        
        # Update base stats
        self.base_hp = evolution_data["base_stats"]["hp"]
        self.base_attack = evolution_data["base_stats"]["attack"]
        self.base_defense = evolution_data["base_stats"]["defense"]
        
        # Increase stage
        self.evolution_stage += 1
        
        # New evolution data (None if stage 3)
        self.evolution_data = evolution_data.get("evolution", None)
        
        # Update available attacks
        self.all_attacks = evolution_data.get("all_attacks", [])
        
        # Recalc stats with new bases
        self.recalc_stats()
        
        # Restore HP ratio
        self.current_hp = max(1, int(self.max_hp * hp_ratio))
        
        # Learn a new attack
        new_attack_name = self._learn_new_attack()
        
        return new_attack_name
    
    
    def take_damage(self, damage):
        """
        Reduce HP.
        
        Args:
            damage: amount of HP to remove
        
        Returns:
            True if Pokemon is KO after damage, False otherwise
        """
        self.current_hp -= damage
        
        if self.current_hp < 0:
            self.current_hp = 0
        
        return self.is_ko
    
    
    def heal(self, amount=None):
        """
        Restore HP.
        
        Args:
            amount: amount to restore (None = full heal)
        """
        if amount is None:
            self.current_hp = self.max_hp
        else:
            self.current_hp += amount
            if self.current_hp > self.max_hp:
                self.current_hp = self.max_hp
    
    
    def revive(self, percentage=0.5):
        """
        Revive a KO Pokemon with percentage of max HP.
        
        Args:
            percentage: between 0.0 and 1.0 (default 0.5 = 50%)
        """
        if not self.is_ko:
            return
        
        self.current_hp = max(1, int(self.max_hp * percentage))
        self.status = None
    
    
    def cure_status(self):
        """Remove status condition."""
        self.status = None
    
    
    def full_heal(self):
        """Fully restore Pokemon (HP + status)."""
        self.current_hp = self.max_hp
        self.status = None
    
    
    def get_hp_percentage(self):
        """
        Return HP percentage between 0.0 and 1.0.
        Used by combat_ui.py for HP bar color.
        """
        if self.max_hp == 0:
            return 0.0
        return self.current_hp / self.max_hp
    
    
    def has_status(self):
        """Return True if Pokemon has a status condition."""
        return self.status is not None
    
    
    def get_front_sprite(self):
        """Load and return front sprite surface, or None if unavailable."""
        import os, pygame
        if self.sprite_front and os.path.exists(self.sprite_front):
            try:
                return pygame.image.load(self.sprite_front).convert_alpha()
            except Exception:
                pass
        return None

    def get_back_sprite(self):
        """Load and return back sprite surface, or None if unavailable."""
        import os, pygame
        if self.sprite_back and os.path.exists(self.sprite_back):
            try:
                return pygame.image.load(self.sprite_back).convert_alpha()
            except Exception:
                pass
        return None
    
    
    def get_evolution_name(self):
        """Return name of evolution, or None if can't evolve."""
        if not self.can_evolve:
            return None
        # This would need pokemon_data to resolve ID to name
        return "???"
    
    
    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------
    
    def to_dict(self):
        """
        Convert Pokemon to dict for save file.
        
        Returns:
            dict with all data needed to reconstruct
        """
        return {
            "id": self.id,
            "name_original": self.original_name,
            "name_custom": self.name,
            "types": self.types,
            "base_stats": {
                "hp": self.base_hp,
                "attack": self.base_attack,
                "defense": self.base_defense
            },
            "level": self.level,
            "current_hp": self.current_hp,
            "xp": self.current_xp,
            "xp_for_next_level": self.xp_for_next_level,
            "evolution_stage": self.evolution_stage,
            "attacks": self.attacks,
            "all_attacks": self.all_attacks,
            "evolution": self.evolution_data,
            "day_night": self.day_night,
            "status": self.status,
            "sprite_front": self.sprite_front,
            "sprite_back": self.sprite_back
        }
    
    
    @classmethod
    def from_data(cls, pokemon_id, level):
        """
        Create a Pokemon from pokemon.json by ID at a given level.

        Args:
            pokemon_id: integer ID
            level: starting level
        Returns:
            Pokemon instance ready to use
        """
        import json
        from config.settings import POKEMON_DATA_FILE

        with open(POKEMON_DATA_FILE, "r", encoding="utf-8") as f:
            all_pokemon = json.load(f)

        data = None
        for poke in all_pokemon:
            if poke["id"] == pokemon_id:
                data = poke.copy()
                break

        if data is None:
            raise ValueError(f"Pokemon ID {pokemon_id} not found in pokemon.json")

        data["level"] = level
        pokemon = cls(data)
        pokemon.recalc_stats()
        pokemon.current_hp = pokemon.max_hp
        return pokemon


    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------

    def __str__(self):
        """Debug representation."""
        types_str = " / ".join(self.types)
        return f"{self.name} ({types_str}) Niv.{self.level} - PV: {self.current_hp}/{self.max_hp}"