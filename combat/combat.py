# =============================================================================
# COMBAT.PY - COMBAT ENGINE
# =============================================================================
#
# Turn-based combat engine with tactical AI.
# Manages complete combat logic from start to end.
# No display here — pure logic.

import random
from combat.damage_calculator import calculate_damage, calculate_xp_gained
from combat.capture_system import attempt_capture
from config.type_chart import get_multiplier
from config.settings import MISS_CHANCE


# =============================================================================
# CONSTANTS
# =============================================================================

HP_SWITCH_THRESHOLD = 0.3      # 30% HP left → trigger switch
MULTI_SWITCH_THRESHOLD = 0.5    # Multiplier < 0.5 → critical disadvantage


# =============================================================================
# COMBAT CLASS
# =============================================================================

class Combat:
    """
    Turn-based combat engine with tactical AI.
    Manages complete combat logic.
    No display — pure logic.
    
    Conforms to subject requirements:
    - get_winner() / get_loser()
    - register_opponent_in_pokedex()
    - damage calculation with type multipliers
    - defense-based HP reduction
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager, player_team, opponent_team,
                 combat_type="wild", trainer=None):
        """
        Initialize combat.
        
        Args:
            game_manager: reference to Game (for day/night cycle)
            player_team: player's Team object
            opponent_team: opponent's Team object (trainer or wild)
            combat_type: "wild" or "trainer"
            trainer: Trainer instance (None if wild)
        """
        self.game_manager = game_manager
        self.player_team = player_team
        self.opponent_team = opponent_team
        self.combat_type = combat_type
        self.trainer = trainer
        
        # Current Pokemon on field
        self.player_pokemon = player_team.get_first_valid()
        self.opponent_pokemon = opponent_team.get_first_valid()
        
        # Turn counter
        self.current_turn = 0
        
        # Temporary boosts (reset on switch)
        self.player_boosts = {"attack": 0, "defense": 0}
        self.opponent_boosts = {"attack": 0, "defense": 0}
        
        # Combat state
        self.combat_finished = False
        self.combat_result = None
        self.winner = None
        self.loser = None
        
        # Event queue for this turn
        self.events = []
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS - IA (TACTICAL)
    # -------------------------------------------------------------------------
    
    def _choose_ia_action(self):
        """
        Tactical IA: decides opponent's action.
        - Wild combat: always attack
        - Trainer combat: can switch if advantageous
        - Chooses best attack based on type effectiveness
        """
        # Special case: wild combat → always attack
        if self.combat_type == "wild":
            best_attack = self._find_best_attack(self.opponent_pokemon, self.player_pokemon)
            return {"type": "attack", "attack": best_attack}
        
        # Trainer combat: tactical logic
        # 1. Check if should switch
        if self._should_switch():
            best_switch = self._find_best_switch()
            if best_switch is not None:
                index = self.opponent_team.get_index(best_switch)
                return {"type": "switch", "index": index}
        
        # 2. Otherwise, attack with best attack
        best_attack = self._find_best_attack(self.opponent_pokemon, self.player_pokemon)
        return {"type": "attack", "attack": best_attack}
    
    
    def _find_best_attack(self, attacker, target):
        """
        Find most effective attack of a Pokemon against a target.
        
        Args:
            attacker: attacking Pokemon
            target: target Pokemon
        
        Returns:
            attack dict with best type multiplier
        """
        attacks = attacker.attacks
        
        if not attacks:
            return {"name": "Struggle", "type": "normal", "power": 30}
        
        best_attack = attacks[0]
        best_multiplier = 0
        
        for attack in attacks:
            multiplier = 1.0
            
            # Calculate effectiveness against each target type
            for target_type in target.types:
                mult = get_multiplier(attack["type"], target_type)
                multiplier *= mult
            
            # If better than current best
            if multiplier > best_multiplier:
                best_multiplier = multiplier
                best_attack = attack
        
        return best_attack
    
    
    def _should_switch(self):
        """
        Determine if trainer should switch Pokemon.
        
        Criteria:
        1. Current Pokemon in danger (HP < HP_SWITCH_THRESHOLD)
        2. Current Pokemon at disadvantage (multiplier < MULTI_SWITCH_THRESHOLD)
        3. Remaining valid Pokemon in team
        
        Returns:
            True if switch recommended
        """
        # Wild combat: no switch
        if self.combat_type == "wild":
            return False
        
        # Trainer has only one valid Pokemon
        if self.opponent_team.count_valid() <= 1:
            return False
        
        # Criterion 1: low HP
        if self.opponent_pokemon.get_hp_percentage() < HP_SWITCH_THRESHOLD:
            return True
        
        # Criterion 2: type disadvantage
        defense_multiplier = self._calculate_defense_multiplier()
        if defense_multiplier < MULTI_SWITCH_THRESHOLD:
            return True
        
        return False
    
    
    def _calculate_defense_multiplier(self):
        """
        Calculate average multiplier opponent would receive
        if player attacked with their most effective type.
        
        Useful to know if Pokemon is in danger.
        """
        # Worst case scenario: player's best attack
        best_player_attack = self._find_best_attack(
            self.player_pokemon, self.opponent_pokemon
        )
        
        multiplier = 1.0
        for def_type in self.opponent_pokemon.types:
            mult = get_multiplier(best_player_attack["type"], def_type)
            multiplier *= mult
        
        return multiplier
    
    
    def _find_best_switch(self):
        """
        Find best replacement Pokemon in opponent's team.
        
        "Best" is the one with highest type advantage against player's Pokemon.
        """
        best_pokemon = None
        best_score = -1
        
        for pokemon in self.opponent_team.get_valid():
            # Don't switch to same Pokemon
            if pokemon == self.opponent_pokemon:
                continue
            
            # Calculate advantage against player
            score = self._calculate_type_advantage(pokemon, self.player_pokemon)
            
            if score > best_score:
                best_score = score
                best_pokemon = pokemon
        
        return best_pokemon
    
    
    def _calculate_type_advantage(self, attacker, defender):
        """
        Calculate average type advantage of attacker against defender.
        Higher score = more effective.
        """
        best_attack = self._find_best_attack(attacker, defender)
        
        multiplier = 1.0
        for def_type in defender.types:
            mult = get_multiplier(best_attack["type"], def_type)
            multiplier *= mult
        
        return multiplier
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS - TURN ORDER
    # -------------------------------------------------------------------------
    
    def _determine_order(self, player_action, opponent_action):
        """
        Determine who acts first.
        
        Priority rules:
        1. Items and switches ALWAYS go first
        2. If both are attacks → random order (50/50)
        3. If both are items/switches → player first
        
        Returns:
            list of (action, side) tuples in order
        """
        player_priority = player_action["type"] in ["item", "switch"]
        opponent_priority = opponent_action["type"] in ["item", "switch"]
        
        # Both are priority → player first
        if player_priority and opponent_priority:
            return [(player_action, "player"), (opponent_action, "opponent")]
        
        # Only player is priority
        if player_priority:
            return [(player_action, "player"), (opponent_action, "opponent")]
        
        # Only opponent is priority
        if opponent_priority:
            return [(opponent_action, "opponent"), (player_action, "player")]
        
        # Both attack → random
        if random.random() < 0.5:
            return [(player_action, "player"), (opponent_action, "opponent")]
        else:
            return [(opponent_action, "opponent"), (player_action, "player")]
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS - ACTIONS
    # -------------------------------------------------------------------------
    
    def _execute_action(self, action, side):
        """Execute a single action (attack, item, or switch)."""
        if action["type"] == "attack":
            self._execute_attack(action, side)
        
        elif action["type"] == "item":
            self._execute_item(action, side)
        
        elif action["type"] == "switch":
            self._execute_switch(action, side)
    
    
    def _execute_attack(self, action, side):
        """Resolve an attack."""
        if side == "player":
            attacker = self.player_pokemon
            defender = self.opponent_pokemon
            attacker_boosts = self.player_boosts
            defender_boosts = self.opponent_boosts
        else:
            attacker = self.opponent_pokemon
            defender = self.player_pokemon
            attacker_boosts = self.opponent_boosts
            defender_boosts = self.player_boosts
        
        attack = action["attack"]
        
        # Get day/night cycle (may be None)
        day_night = self.game_manager.day_night_cycle
        
        # Calculate damage
        result = calculate_damage(
            attacker, defender, attack, day_night,
            attacker_boosts, defender_boosts
        )
        
        # Apply damage
        if result["hit"] and not result["immune"]:
            defender.take_damage(result["damage"])
        
        # Add event
        self.events.append({
            "type": "attack",
            "side": side,
            "attacker": attacker,
            "defender": defender,
            "attack_name": attack["name"],
            "result": result
        })
    
    
    def _execute_item(self, action, side):
        """Resolve item usage by player (IA doesn't use items)."""
        item = action["item"]
        target = action.get("target", self.player_pokemon)
        
        if item.is_heal:
            target.heal(item.effect_value)
            self.events.append({
                "type": "item_used",
                "side": side,
                "item": item,
                "target": target,
                "effect": "heal",
                "value": item.effect_value
            })
        
        elif item.is_boost:
            stat = item.target_stat    # "attack" or "defense"
            self.player_boosts[stat] += item.effect_value
            self.events.append({
                "type": "item_used",
                "side": side,
                "item": item,
                "target": self.player_pokemon,
                "effect": "boost",
                "stat": stat,
                "value": item.effect_value
            })
        
        elif item.is_revive:
            target.revive(item.effect_value / 100)
            self.events.append({
                "type": "item_used",
                "side": side,
                "item": item,
                "target": target,
                "effect": "revive",
                "value": item.effect_value
            })
        
        elif item.is_status_heal:
            target.cure_status()
            self.events.append({
                "type": "item_used",
                "side": side,
                "item": item,
                "target": target,
                "effect": "status_heal"
            })
    
    
    def _execute_switch(self, action, side):
        """Switch active Pokemon (player only)."""
        if side == "player":
            old = self.player_pokemon
            index = action["index"]
            new = self.player_team.get_pokemon(index)
            
            if new is not None and not new.is_ko:
                self.player_pokemon = new
                
                # Reset boosts
                self.player_boosts = {"attack": 0, "defense": 0}
                
                self.events.append({
                    "type": "switch",
                    "side": side,
                    "old": old,
                    "new": new
                })
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS - FLEE / CAPTURE
    # -------------------------------------------------------------------------
    
    def _handle_flee(self):
        """Handle player fleeing."""
        if self.combat_type != "wild":
            self.events.append({
                "type": "flee_impossible",
                "message": "Can't flee from a trainer battle!"
            })
            return self.events
        
        self.combat_finished = True
        self.combat_result = "flee"
        
        self.events.append({
            "type": "flee",
            "message": "You fled successfully!"
        })
        
        return self.events
    
    
    def _handle_capture(self, ball):
        """Handle capture attempt."""
        result = attempt_capture(
            self.opponent_pokemon, ball,
            self.player_team, self.game_manager.player.storage,
            self.combat_type
        )
        
        self.events.append({
            "type": "capture",
            "result": result,
            "ball": ball
        })
        
        if result["capture_success"]:
            self.combat_finished = True
            self.combat_result = "capture"
        else:
            if result["failure_reason"] == "miss":
                # Opponent attacks after failed capture
                opponent_action = self._choose_ia_action()
                self._execute_action(opponent_action, "opponent")
                self._check_ko()
        
        return self.events
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS - KO CHECK
    # -------------------------------------------------------------------------
    
    def _check_ko(self):
        """
        Check if a Pokemon is KO after an action.
        Handle consequences: replacement or combat end.
        
        Returns:
            True if combat ended or replacement needed, False otherwise
        """
        # --- Opponent KO ---
        if self.opponent_pokemon.is_ko:
            self.events.append({
                "type": "ko",
                "side": "opponent",
                "pokemon": self.opponent_pokemon
            })
            
            # Give XP
            self._give_xp()
            
            # Check if opponent has remaining Pokemon
            if self.opponent_team.has_valid_pokemon:
                # Send next
                next_pokemon = self.opponent_team.get_first_valid()
                old = self.opponent_pokemon
                self.opponent_pokemon = next_pokemon
                self.opponent_boosts = {"attack": 0, "defense": 0}
                
                self.events.append({
                    "type": "switch",
                    "side": "opponent",
                    "old": old,
                    "new": next_pokemon
                })
            else:
                # No more opponents → victory!
                self._end_combat("victory")
                return True
        
        # --- Player KO ---
        if self.player_pokemon.is_ko:
            self.events.append({
                "type": "ko",
                "side": "player",
                "pokemon": self.player_pokemon
            })
            
            if self.player_team.has_valid_pokemon:
                # Player must choose replacement
                self.events.append({
                    "type": "replacement_choice",
                    "side": "player"
                })
                return True
            else:
                # No more Pokemon → defeat
                self._end_combat("defeat")
                return True
        
        return False
    
    
    def _give_xp(self):
        """Give XP to player's active Pokemon."""
        if self.player_pokemon.is_ko:
            return   # KO Pokemon don't gain XP
        
        xp = calculate_xp_gained(self.opponent_pokemon)
        result = self.player_pokemon.gain_xp(xp)
        
        self.events.append({
            "type": "xp",
            "pokemon": self.player_pokemon,
            "xp_gained": xp,
            "result": result
        })
        
        # Level up event
        if result["level_ups"] > 0:
            self.events.append({
                "type": "level_up",
                "pokemon": self.player_pokemon,
                "old_level": result["old_level"],
                "new_level": result["new_level"]
            })
        
        # Evolution possible
        if result["evolution"]:
            self.events.append({
                "type": "evolution_possible",
                "pokemon": self.player_pokemon
            })
    
    
    def _end_combat(self, result):
        """Mark combat as finished and add end event."""
        self.combat_finished = True
        self.combat_result = result
        
        if result == "victory":
            self.winner = self.player_pokemon
            self.loser = self.opponent_pokemon
        else:
            self.winner = self.opponent_pokemon
            self.loser = self.player_pokemon
        
        self.events.append({
            "type": "combat_end",
            "result": result
        })
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def execute_turn(self, player_action):
        """
        Execute a complete turn.
        
        Args:
            player_action: dict describing player's action
        
        Returns:
            list of events
        """
        self.events = []
        self.current_turn += 1
        
        # --- FLEE ---
        if player_action["type"] == "flee":
            return self._handle_flee()
        
        # --- CAPTURE ---
        if player_action["type"] == "capture":
            return self._handle_capture(player_action["ball"])
        
        # --- DETERMINE IA ACTION ---
        opponent_action = self._choose_ia_action()
        
        # --- DETERMINE ORDER ---
        ordered_actions = self._determine_order(player_action, opponent_action)
        
        # --- EXECUTE ACTIONS IN ORDER ---
        for action, side in ordered_actions:
            # Check if combatant is still alive
            if side == "player" and self.player_pokemon.is_ko:
                continue
            if side == "opponent" and self.opponent_pokemon.is_ko:
                continue
            
            self._execute_action(action, side)
            
            # Check KO after each action
            if self._check_ko():
                # Combat ended or replacement needed
                break
        
        return self.events
    
    
    def replace_player_pokemon(self, index):
        """
        Called by state_combat.py when player chooses replacement after KO.
        
        Args:
            index: index in team
        
        Returns:
            switch event for display
        """
        old = self.player_pokemon
        new = self.player_team.get_pokemon(index)
        
        if new is None or new.is_ko:
            return None
        
        self.player_pokemon = new
        self.player_boosts = {"attack": 0, "defense": 0}
        
        event = {
            "type": "switch",
            "side": "player",
            "old": old,
            "new": new
        }
        
        return event
    
    
    def get_state(self):
        """Return snapshot of current combat state."""
        return {
            "player_pokemon": self.player_pokemon,
            "opponent_pokemon": self.opponent_pokemon,
            "player_boosts": self.player_boosts.copy(),
            "opponent_boosts": self.opponent_boosts.copy(),
            "turn": self.current_turn,
            "combat_type": self.combat_type,
            "trainer_name": self.trainer.name if self.trainer else None,
            "combat_finished": self.combat_finished,
            "result": self.combat_result
        }
    
    
    # -------------------------------------------------------------------------
    # SUBJECT-REQUIRED METHODS
    # -------------------------------------------------------------------------
    
    def get_winner(self):
        """Return winner name (subject requirement)."""
        if not self.combat_finished:
            return None
        return self.winner.name if self.winner else None
    
    
    def get_loser(self):
        """Return loser name (subject requirement)."""
        if not self.combat_finished:
            return None
        return self.loser.name if self.loser else None
    
    
    def register_opponent_in_pokedex(self, pokedex):
        """Register opponent Pokemon in Pokedex (subject requirement)."""
        if self.opponent_pokemon is not None:
            pokedex.register_seen(self.opponent_pokemon.id)
            return True
        return False
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """Debug representation."""
        return f"Combat turn {self.current_turn}: {self.player_pokemon.name} (HP:{self.player_pokemon.current_hp}/{self.player_pokemon.max_hp}) vs {self.opponent_pokemon.name} (HP:{self.opponent_pokemon.current_hp}/{self.opponent_pokemon.max_hp})"