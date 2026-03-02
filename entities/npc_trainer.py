# =============================================================================
# NPC_TRAINER.PY - TRAINER NPC CLASS
# =============================================================================
#
# Trainer NPC that battles the player.

import json
import pygame
from entities.npc import NPC
from entities.pokemon import Pokemon
from entities.team import Team
from config.settings import TILE_SIZE, POKEMON_DATA_FILE


# =============================================================================
# TRAINER NPC CLASS
# =============================================================================

class NPCTrainer(NPC):
    """
    Trainer NPC. Inherits from NPC.
    Has a Pokemon team, vision range, and triggers combat.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, data):
        """
        Initialize trainer.
        
        Args:
            data: dict from trainers.json
        """
        # Call NPC constructor
        super().__init__(data)
        
        # --- COMBAT ---
        self.battle_level = data.get("battle_level", 1)
        self.reward_credits = data.get("reward_credits", 20)
        self.level_label = data.get("level", "B1")

        # --- POKEMON TEAM ---
        # Each entry in "team" has pokemon_id and level.
        # Load full data from pokemon.json.
        self.team_data = data.get("team", [])
        self.team = self._create_team()
        
        # --- VISION RANGE ---
        # Number of tiles in front of trainer where they spot the player.
        # 3 by default: enough to surprise, not too much to be unavoidable.
        self.vision_range = data.get("vision_range", 3)
        
        # Vision rectangle calculated based on direction
        self.vision_rect = self._calculate_vision_rect()
        
        # If no dialogues were provided in data, load from central trainer_dialogues.py
        if "challenge" not in self.dialogues:
            try:
                from data.trainer_dialogues import TRAINER_DIALOGUES
                trainer_dlg = TRAINER_DIALOGUES.get(self.name)
                if trainer_dlg:
                    self.dialogues = trainer_dlg
            except Exception:
                pass

        # --- GAME MANAGER REFERENCE ---
        # Stored temporarily during on_interact() so on_dialogue_end() can access it
        self._game_manager_ref = None
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _create_team(self):
        """
        Create trainer's Pokemon team from JSON data.
        If no team_data defined (e.g. spawned from map), generate a default team.
        """
        if not self.team_data:
            return self._generate_default_team()

        pokemon_list = []

        try:
            with open(POKEMON_DATA_FILE, "r") as f:
                all_pokemon = json.load(f)

            index = {}
            for poke in all_pokemon:
                index[poke["id"]] = poke

            for entry in self.team_data:
                pokemon_id = entry["pokemon_id"]
                level = entry["level"]

                if pokemon_id in index:
                    poke_data = index[pokemon_id].copy()
                    poke_data["level"] = level

                    pokemon = Pokemon(poke_data)
                    pokemon.recalc_stats()
                    pokemon.current_hp = pokemon.max_hp

                    pokemon_list.append(pokemon)

        except Exception:
            print(f"Warning: Could not load team for trainer {self.name}")

        return Team(pokemon_list)


    def _generate_default_team(self):
        """
        Generate a random default team when no explicit team data is given.
        Team size and level range depend on the trainer's level_label.
        """
        import random

        # level_label → (team_size, min_level, max_level)
        level_map = {
            "B1": (1, 5,  10),
            "B2": (2, 10, 15),
            "B3": (2, 15, 20),
            "M1": (3, 20, 25),
            "M2": (3, 25, 30),
        }
        count, min_lvl, max_lvl = level_map.get(self.level_label, (1, 5, 10))

        pokemon_list = []
        try:
            with open(POKEMON_DATA_FILE, "r") as f:
                all_pokemon = json.load(f)

            candidates = [p for p in all_pokemon if p.get("id", 0) > 0]
            if not candidates:
                return Team([])

            chosen = random.sample(candidates, min(count, len(candidates)))
            for poke_data in chosen:
                data = poke_data.copy()
                data["level"] = random.randint(min_lvl, max_lvl)
                pokemon = Pokemon(data)
                pokemon.recalc_stats()
                pokemon.current_hp = pokemon.max_hp
                pokemon_list.append(pokemon)

        except Exception:
            print(f"Warning: Could not generate default team for trainer {self.name}")

        return Team(pokemon_list)
    
    
    def _calculate_vision_rect(self):
        """
        Calculate trainer's vision rectangle.
        Rectangle of width 1 tile and length vision_range tiles,
        placed in front of trainer according to direction.
        
        Example for trainer at (160,96) facing down with vision_range=3:
            rect = pygame.Rect(160, 128, 32, 96)
            → x=160 (same column)
            → y=128 (1 tile below trainer)
            → width=32 (1 tile)
            → height=96 (3 tiles × 32)
        """
        range_px = self.vision_range * TILE_SIZE
        
        if self.direction == "down":
            return pygame.Rect(
                self.x,
                self.y + TILE_SIZE,      # starts 1 tile below
                TILE_SIZE,                # width: 1 tile
                range_px                   # length: vision_range tiles
            )
        
        if self.direction == "up":
            return pygame.Rect(
                self.x,
                self.y - range_px,        # starts vision_range tiles above
                TILE_SIZE,
                range_px
            )
        
        if self.direction == "left":
            return pygame.Rect(
                self.x - range_px,        # starts vision_range tiles left
                self.y,
                range_px,
                TILE_SIZE
            )
        
        if self.direction == "right":
            return pygame.Rect(
                self.x + TILE_SIZE,       # starts 1 tile right
                self.y,
                range_px,
                TILE_SIZE
            )
        
        # Fallback (shouldn't happen)
        return pygame.Rect(0, 0, 0, 0)
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def is_player_in_vision(self, player, game_manager):
        """
        Check if player is in trainer's vision range (all 4 directions).

        Args:
            player: Player object (uses collision rect)
            game_manager: to check if trainer already defeated

        Returns:
            True if combat should trigger, False otherwise
        """
        if game_manager.player.is_trainer_defeated(self.id):
            return False

        range_px = self.vision_range * TILE_SIZE
        vision_rects = [
            pygame.Rect(self.x, self.y - range_px, TILE_SIZE, range_px),       # up
            pygame.Rect(self.x, self.y + TILE_SIZE, TILE_SIZE, range_px),       # down
            pygame.Rect(self.x - range_px, self.y, range_px, TILE_SIZE),        # left
            pygame.Rect(self.x + TILE_SIZE, self.y, range_px, TILE_SIZE),       # right
        ]
        return any(r.colliderect(player.rect) for r in vision_rects)
    
    
    def get_dialogue(self):
        """
        Return dialogue based on context.
        
        If trainer not defeated yet → "challenge" dialogue
            (provocation before battle)
        
        If trainer already defeated → "already_beaten" dialogue
            (post-combat line)
        
        Needs game_manager, but get_dialogue() is called by on_interact()
        which has access to it. We store temporary reference in _game_manager_ref.
        """
        if self._game_manager_ref is not None:
            if self._game_manager_ref.player.is_trainer_defeated(self.id):
                return self.dialogues.get("already_beaten",
                    ["T'as déjà gagné contre moi...", "Pas la peine de te vanter."])

        return self.dialogues.get("challenge",
            ["Hé ! Prépare-toi à combattre !"])
    
    
    def on_interact(self, game_manager):
        """
        Override on_interact() to store game_manager reference
        before get_dialogue() is called.
        Then call base behavior (NPC.on_interact).
        """
        self._game_manager_ref = game_manager
        super().on_interact(game_manager)
    
    
    def on_dialogue_end(self, game_manager):
        """
        Called when dialogue ends.
        
        If trainer not defeated → start combat.
        If trainer already defeated → nothing, dialogue just closes.
        
        Combat is started by pushing StateCombat.
        We pass:
        - trainer's team
        - callback for when combat ends
        - combat type ("trainer")
        
        The callback _on_combat_end is called by StateCombat when combat finishes.
        It gives credits and marks trainer as defeated.
        """
        # If already defeated, nothing to do
        if game_manager.player.is_trainer_defeated(self.id):
            return
        
        # Restore trainer's team HP
        # In case player lost a previous battle against this trainer
        self.team.heal_all()
        
        # Start combat
        from states.state_combat import StateCombat
        
        combat_state = StateCombat(
            game_manager,
            opponent_pokemon=self.team.get_first_valid(),
            combat_type="trainer",
            trainer=self
        )
        game_manager.state_manager.push(combat_state)
    
    
    def on_victory(self, game_manager):
        """
        Callback called by StateCombat when player wins.
        
        Steps:
        1. Mark trainer as defeated
        2. Give credits to player
        3. Play victory sound
        4. Start defeat dialogue
        """
        player = game_manager.player
        
        # Mark as defeated
        player.add_defeated_trainer(self.id)
        
        # Give credits
        player.credits += self.reward_credits
        
        # Play victory music
        game_manager.audio_manager.play_music("victory", loop=False)
        
        # Defeat dialogue
        lines = self.dialogues.get("defeat", ["Bien joué..."])

        # Add credits message
        final_lines = lines.copy()
        final_lines.append(f"Tu gagnes {self.reward_credits} crédits !")
        
        from states.state_dialogue import StateDialogue
        
        dialogue_state = StateDialogue(
            game_manager,
            final_lines,
            callback=None    # nothing after this dialogue
        )
        game_manager.state_manager.push(dialogue_state)
    
    
    def on_defeat(self, game_manager):
        """
        Callback called by StateCombat when player loses.
        
        Player is sent back to Pokemon Center.
        Team is healed automatically (Pokemon convention).
        Trainer is NOT marked as defeated.
        """
        player = game_manager.player
        
        # Heal team (Pokemon convention: heal after blackout)
        player.team.heal_all()
        
        # Play defeat music
        game_manager.audio_manager.play_music("defeat", loop=False)
        
        # Defeat dialogue
        lines = ["Tous tes Pokémon sont KO...",
                 "Tu es renvoyé au Centre Pokémon."]
        
        from states.state_dialogue import StateDialogue
        
        dialogue_state = StateDialogue(
            game_manager,
            lines,
            callback=self._return_to_pokemon_center
        )
        game_manager.state_manager.push(dialogue_state)
    
    
    def _return_to_pokemon_center(self, game_manager):
        """
        Teleport player to Pokemon Center of current zone.
        Called after defeat dialogue.
        
        Loads Pokemon Center spawn from map_manager
        and teleports player there.
        """
        # Get Pokemon Center spawn
        # map_manager has a special spawn point for defeat return
        spawn = game_manager.map_manager.get_spawn_position("pokemon_center")
        
        if spawn is not None:
            game_manager.player.set_position(spawn[0], spawn[1])
        
        # Resume exploration music
        zone = game_manager.player.current_zone
        game_manager.audio_manager.play_music("exploration_" + zone)
    
    
    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------
    
    @property
    def is_trainer(self):
        """Flag to identify as trainer in state_exploration.py."""
        return True
    
    
    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------
    
    def to_dict(self):
        """Serialize for debug (adds trainer-specific info)."""
        base = super().to_dict()
        base["battle_level"] = self.battle_level
        base["reward_credits"] = self.reward_credits
        base["vision_range"] = self.vision_range
        base["team_size"] = self.team.size
        return base
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """Debug representation."""
        return f"Trainer '{self.name}' (B{self.battle_level}) @ {self.zone} - Team: {self.team.size} Pokemon - {self.reward_credits} credits"