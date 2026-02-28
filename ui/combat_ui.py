# =============================================================================
# COMBAT_UI.PY - COMBAT INTERFACE
# =============================================================================
#
# This file draws the entire combat screen:
# - Pokemon sprites (front and back)
# - HP bars
# - Names and levels
# - Action menu (Fight / Bag / Pokemon / Run)
# - Attack list
# - Messages ("It's super effective!")
# - Animations (damage flash, HP decrease, KO, capture)

import pygame
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    HP_GREEN, HP_YELLOW, HP_RED,
    DIALOG_BG, DIALOG_BORDER, DIALOG_TEXT
)


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

# Display modes for bottom zone
MODE_MENU = "menu"
MODE_ATTACKS = "attacks"
MODE_BAG = "bag"
MODE_POKEMON = "pokemon"
MODE_MESSAGE = "message"
MODE_REPLACEMENT = "replacement"

# Sprite positions
OPPONENT_SPRITE_X = SCREEN_WIDTH - 200
OPPONENT_SPRITE_Y = 80
PLAYER_SPRITE_X = 100
PLAYER_SPRITE_Y = 250

# HP bar dimensions
HP_BAR_WIDTH = 150
HP_BAR_HEIGHT = 12

# Bottom zone
BOTTOM_ZONE_Y = SCREEN_HEIGHT - 150
BOTTOM_ZONE_HEIGHT = 150

# Animation durations
DAMAGE_FLASH_DURATION = 0.4      # seconds of flashing
HP_BAR_ANIMATION_DURATION = 0.5   # seconds for bar transition
KO_ANIMATION_DURATION = 0.5       # seconds for KO animation


# =============================================================================
# COMBAT UI CLASS
# =============================================================================

class CombatUI:
    """
    Combat interface. Handles all drawing and animations during combat.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager):
        """
        Initialize combat UI.
        
        Args:
            game_manager: to access audio and resources
        """
        self.game_manager = game_manager
        
        # --- FONTS ---
        self.font_name = pygame.font.Font(None, 28)
        self.font_hp = pygame.font.Font(None, 22)
        self.font_menu = pygame.font.Font(None, 26)
        self.font_message = pygame.font.Font(None, 24)
        
        # --- DISPLAY MODE ---
        self.mode = MODE_MENU
        self.selection_index = 0
        
        # --- POKEMON SPRITES ---
        # Loaded dynamically when state is updated
        self.player_sprite = None
        self.opponent_sprite = None
        
        # --- HP BARS (animation) ---
        # Displayed HP = target HP (from Pokemon).
        # When HP changes, displayed_hp_* smoothly glides to new value.
        self.displayed_hp_player = 0
        self.displayed_hp_opponent = 0
        self.target_hp_player = 0
        self.target_hp_opponent = 0
        
        # --- ANIMATIONS ---
        self.animation_active = False
        self.animation_type = None      # "damage_flash", "ko", "capture"
        self.animation_timer = 0
        self.animation_target = None     # "player" or "opponent"
        
        # --- EVENT QUEUE ---
        self.pending_events = []
        self.current_event = None
        self.current_message = ""
        
        # --- COMBAT DATA ---
        # Updated every frame by state_combat.py
        self.combat_state = None
        
        # --- MENU OPTIONS ---
        self.menu_options = ["Attaquer", "Sac", "Pokémon", "Fuir"]
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def set_state(self, player_pokemon, opponent_pokemon, combat_type):
        """
        Update combat data from engine.
        Called every frame by state_combat.py.
        
        Args:
            player_pokemon: player's current Pokemon
            opponent_pokemon: opponent's current Pokemon
            combat_type: "wild" or "trainer"
        """
        self.combat_state = {
            "player_pokemon": player_pokemon,
            "opponent_pokemon": opponent_pokemon,
            "combat_type": combat_type
        }
        
        # Update target HP
        if player_pokemon is not None:
            self.target_hp_player = player_pokemon.current_hp
        
        if opponent_pokemon is not None:
            self.target_hp_opponent = opponent_pokemon.current_hp
    
    
    def load_sprites(self, player_pokemon, opponent_pokemon):
        """
        Load sprites for both Pokemon on the field.
        Called at combat start and after each switch.
        
        Player's Pokemon is seen from behind (back sprite).
        Opponent's Pokemon is seen from front (front sprite).
        
        If sprite file doesn't exist, create a placeholder.
        """
        # Player sprite (back)
        try:
            if player_pokemon.sprite_back and self._file_exists(player_pokemon.sprite_back):
                self.player_sprite = pygame.image.load(player_pokemon.sprite_back).convert_alpha()
            else:
                self.player_sprite = self._create_placeholder((100, 100, 255))
        except Exception:
            self.player_sprite = self._create_placeholder((100, 100, 255))
        
        # Opponent sprite (front)
        try:
            if opponent_pokemon.sprite_front and self._file_exists(opponent_pokemon.sprite_front):
                self.opponent_sprite = pygame.image.load(opponent_pokemon.sprite_front).convert_alpha()
            else:
                self.opponent_sprite = self._create_placeholder((255, 100, 100))
        except Exception:
            self.opponent_sprite = self._create_placeholder((255, 100, 100))
        
        # Initialize displayed HP
        self.displayed_hp_player = player_pokemon.current_hp
        self.displayed_hp_opponent = opponent_pokemon.current_hp
        self.target_hp_player = player_pokemon.current_hp
        self.target_hp_opponent = opponent_pokemon.current_hp
    
    
    def set_events(self, events):
        """
        Receive event list from a combat turn.
        Store in queue to display sequentially.
        
        Args:
            events: list from combat.execute_turn()
        """
        self.pending_events = events.copy()
        self._consume_next_event()
    
    
    def set_mode(self, mode):
        """Set bottom display mode."""
        self.mode = mode
        self.selection_index = 0
    
    
    def next_event(self):
        """
        Move to next event in queue.
        
        Returns:
            True if more events remain, False otherwise
        """
        if len(self.pending_events) > 0:
            self._consume_next_event()
            return True
        return False
    
    
    def is_animation_finished(self):
        """Return True if current animation is finished."""
        return not self.animation_active
    
    
    def skip_animation(self):
        """Skip current animation and show result immediately."""
        if self.animation_active:
            self.animation_active = False
            # Immediately set HP to target
            self.displayed_hp_player = self.target_hp_player
            self.displayed_hp_opponent = self.target_hp_opponent
    
    
    def handle_input(self, event):
        """
        Handle player input based on current mode.
        Called by state_combat.py when a key event occurs.
        
        Args:
            event: pygame event
            
        Returns:
            dict describing player action, or None if nothing chosen
        """
        if event.type != pygame.KEYDOWN:
            return None
        
        # --- MESSAGE MODE ---
        if self.mode == MODE_MESSAGE:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                # Move to next event
                self.next_event()
                return {"type": "advance_message"}
        
        # --- MENU MODE ---
        if self.mode == MODE_MENU:
            if event.key == pygame.K_UP:
                self.selection_index = max(0, self.selection_index - 2)
            elif event.key == pygame.K_DOWN:
                self.selection_index = min(3, self.selection_index + 2)
            elif event.key == pygame.K_LEFT:
                self.selection_index = max(0, self.selection_index - 1)
            elif event.key == pygame.K_RIGHT:
                self.selection_index = min(3, self.selection_index + 1)
            
            elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.selection_index == 0:
                    self.mode = MODE_ATTACKS
                    self.selection_index = 0
                elif self.selection_index == 1:
                    self.mode = MODE_BAG
                    self.selection_index = 0
                elif self.selection_index == 2:
                    self.mode = MODE_POKEMON
                    self.selection_index = 0
                elif self.selection_index == 3:
                    return {"type": "flee"}
        
        # --- ATTACKS MODE ---
        if self.mode == MODE_ATTACKS:
            attacks = self.combat_state["player_pokemon"].attacks
            
            if event.key == pygame.K_UP:
                self.selection_index = max(0, self.selection_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selection_index = min(len(attacks) - 1, self.selection_index + 1)
            elif event.key == pygame.K_ESCAPE:
                self.mode = MODE_MENU
                self.selection_index = 0
            
            elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.selection_index < len(attacks):
                    chosen_attack = attacks[self.selection_index]
                    self.mode = MODE_MESSAGE
                    return {"type": "attack", "attack": chosen_attack}
        
        # --- BAG MODE ---
        if self.mode == MODE_BAG:
            items = self.combat_state.get("combat_items", [])
            
            if event.key == pygame.K_UP:
                self.selection_index = max(0, self.selection_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selection_index = min(len(items) - 1, self.selection_index + 1)
            elif event.key == pygame.K_ESCAPE:
                self.mode = MODE_MENU
                self.selection_index = 0
            
            elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.selection_index < len(items):
                    chosen_item, quantity = items[self.selection_index]
                    return {"type": "item_chosen", "item": chosen_item}
        
        # --- POKEMON MODE ---
        if self.mode == MODE_POKEMON:
            team = self.combat_state.get("player_team", [])
            
            if event.key == pygame.K_UP:
                self.selection_index = max(0, self.selection_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selection_index = min(len(team) - 1, self.selection_index + 1)
            elif event.key == pygame.K_ESCAPE:
                self.mode = MODE_MENU
                self.selection_index = 0
            
            elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.selection_index < len(team):
                    chosen_pokemon = team[self.selection_index]
                    if not chosen_pokemon.is_ko():
                        return {"type": "switch", "index": self.selection_index}
        
        # --- REPLACEMENT MODE (forced) ---
        if self.mode == MODE_REPLACEMENT:
            team = self.combat_state.get("player_team", [])
            
            if event.key == pygame.K_UP:
                self.selection_index = max(0, self.selection_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selection_index = min(len(team) - 1, self.selection_index + 1)
            # NO ESCAPE → choice is mandatory
            
            elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.selection_index < len(team):
                    chosen_pokemon = team[self.selection_index]
                    if not chosen_pokemon.is_ko():
                        return {"type": "replacement", "index": self.selection_index}
        
        return None
    
    
    def update(self, dt):
        """
        Update animations and HP bars.
        Called every frame.
        
        Args:
            dt: delta time in seconds
        """
        # --- HP BAR ANIMATION ---
        # Displayed HP glide toward target HP
        hp_speed = 100    # HP per second
        
        if self.displayed_hp_player != self.target_hp_player:
            if self.displayed_hp_player > self.target_hp_player:
                self.displayed_hp_player = max(
                    self.target_hp_player,
                    self.displayed_hp_player - hp_speed * dt
                )
            else:
                self.displayed_hp_player = min(
                    self.target_hp_player,
                    self.displayed_hp_player + hp_speed * dt
                )
        
        if self.displayed_hp_opponent != self.target_hp_opponent:
            if self.displayed_hp_opponent > self.target_hp_opponent:
                self.displayed_hp_opponent = max(
                    self.target_hp_opponent,
                    self.displayed_hp_opponent - hp_speed * dt
                )
            else:
                self.displayed_hp_opponent = min(
                    self.target_hp_opponent,
                    self.displayed_hp_opponent + hp_speed * dt
                )
        
        # --- ACTIVE ANIMATION ---
        if self.animation_active:
            self.animation_timer += dt
            
            if self.animation_type == "damage_flash":
                if self.animation_timer >= DAMAGE_FLASH_DURATION:
                    self.animation_active = False
            
            if self.animation_type == "ko":
                if self.animation_timer >= KO_ANIMATION_DURATION:
                    self.animation_active = False
    
    
    def draw(self, screen):
        """
        Draw entire combat screen.
        Called every frame by state_combat.py.
        
        Args:
            screen: Pygame surface
        """
        if self.combat_state is None:
            return
        
        # --- BACKGROUND ---
        screen.fill((240, 240, 240))    # light gray
        
        # --- SPRITES ---
        self._draw_sprites(screen)
        
        # --- POKEMON INFO (names, levels, HP bars) ---
        self._draw_opponent_info(screen)
        self._draw_player_info(screen)
        
        # --- BOTTOM ZONE ---
        self._draw_bottom_zone(screen)
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS - DRAWING
    # -------------------------------------------------------------------------
    
    def _draw_sprites(self, screen):
        """Draw both Pokemon sprites with animations."""
        # Opponent sprite
        draw_opponent = True
        
        if self.animation_active and self.animation_target == "opponent":
            if self.animation_type == "damage_flash":
                # Flash: visible every other frame
                if int(self.animation_timer * 15) % 2 == 0:
                    draw_opponent = False
            elif self.animation_type == "ko":
                # Sprite falls down
                offset_y = int(self.animation_timer / KO_ANIMATION_DURATION * 100)
                if self.opponent_sprite is not None:
                    screen.blit(self.opponent_sprite, (OPPONENT_SPRITE_X, OPPONENT_SPRITE_Y + offset_y))
                draw_opponent = False
        
        if draw_opponent and self.opponent_sprite is not None:
            screen.blit(self.opponent_sprite, (OPPONENT_SPRITE_X, OPPONENT_SPRITE_Y))
        
        # Player sprite (same logic)
        draw_player = True
        
        if self.animation_active and self.animation_target == "player":
            if self.animation_type == "damage_flash":
                if int(self.animation_timer * 15) % 2 == 0:
                    draw_player = False
            elif self.animation_type == "ko":
                offset_y = int(self.animation_timer / KO_ANIMATION_DURATION * 100)
                if self.player_sprite is not None:
                    screen.blit(self.player_sprite, (PLAYER_SPRITE_X, PLAYER_SPRITE_Y + offset_y))
                draw_player = False
        
        if draw_player and self.player_sprite is not None:
            screen.blit(self.player_sprite, (PLAYER_SPRITE_X, PLAYER_SPRITE_Y))
    
    
    def _draw_opponent_info(self, screen):
        """Draw opponent's info panel: name, level, HP bar."""
        pokemon = self.combat_state["opponent_pokemon"]
        if pokemon is None:
            return
        
        # Name and level
        text = f"{pokemon.name} Nv.{pokemon.level}"
        surface = self.font_name.render(text, True, (0, 0, 0))
        screen.blit(surface, (20, 20))
        
        # HP bar
        self._draw_hp_bar(screen, 20, 50,
                          self.displayed_hp_opponent, pokemon.max_hp)
        
        # HP numbers
        hp_text = f"{int(self.displayed_hp_opponent)}/{pokemon.max_hp}"
        hp_surface = self.font_hp.render(hp_text, True, (60, 60, 60))
        screen.blit(hp_surface, (20 + HP_BAR_WIDTH + 10, 48))
    
    
    def _draw_player_info(self, screen):
        """Draw player's info panel."""
        pokemon = self.combat_state["player_pokemon"]
        if pokemon is None:
            return
        
        base_x = SCREEN_WIDTH - 300
        base_y = 200
        
        # Name and level
        text = f"{pokemon.name} Nv.{pokemon.level}"
        surface = self.font_name.render(text, True, (0, 0, 0))
        screen.blit(surface, (base_x, base_y))
        
        # HP bar
        self._draw_hp_bar(screen, base_x, base_y + 30,
                          self.displayed_hp_player, pokemon.max_hp)
        
        # HP numbers
        hp_text = f"{int(self.displayed_hp_player)}/{pokemon.max_hp}"
        hp_surface = self.font_hp.render(hp_text, True, (60, 60, 60))
        screen.blit(hp_surface, (base_x + HP_BAR_WIDTH + 10, base_y + 28))
        
        # XP bar (smaller, blue)
        if pokemon.xp_for_next_level > 0:
            xp_ratio = pokemon.current_xp / pokemon.xp_for_next_level
            self._draw_bar(screen, base_x, base_y + 50,
                          HP_BAR_WIDTH, 6, xp_ratio, (80, 120, 255))
    
    
    def _draw_hp_bar(self, screen, x, y, current_hp, max_hp):
        """Draw HP bar with appropriate color."""
        if max_hp == 0:
            return
        
        ratio = current_hp / max_hp
        ratio = max(0, min(1, ratio))
        
        # Color based on ratio
        if ratio > 0.5:
            color = HP_GREEN
        elif ratio > 0.2:
            color = HP_YELLOW
        else:
            color = HP_RED
        
        self._draw_bar(screen, x, y, HP_BAR_WIDTH, HP_BAR_HEIGHT, ratio, color)
    
    
    def _draw_bar(self, screen, x, y, width, height, ratio, color):
        """Draw a generic bar (HP, XP). Gray background + colored fill."""
        # Gray background
        pygame.draw.rect(screen, (200, 200, 200), (x, y, width, height))
        # Fill
        fill_width = int(width * ratio)
        if fill_width > 0:
            pygame.draw.rect(screen, color, (x, y, fill_width, height))
        # Border
        pygame.draw.rect(screen, (100, 100, 100), (x, y, width, height), 1)
    
    
    def _draw_bottom_zone(self, screen):
        """Draw bottom zone according to current mode."""
        # Bottom zone background
        bg = pygame.Surface((SCREEN_WIDTH, BOTTOM_ZONE_HEIGHT))
        bg.fill(DIALOG_BG)
        bg.set_alpha(240)
        screen.blit(bg, (0, BOTTOM_ZONE_Y))
        
        # Border
        pygame.draw.rect(screen, DIALOG_BORDER,
                        (0, BOTTOM_ZONE_Y, SCREEN_WIDTH, BOTTOM_ZONE_HEIGHT), 3)
        
        if self.mode == MODE_MENU:
            self._draw_menu(screen)
        elif self.mode == MODE_ATTACKS:
            self._draw_attacks(screen)
        elif self.mode == MODE_BAG:
            self._draw_bag(screen)
        elif self.mode == MODE_POKEMON or self.mode == MODE_REPLACEMENT:
            self._draw_team(screen)
        elif self.mode == MODE_MESSAGE:
            self._draw_message(screen)
    
    
    def _draw_menu(self, screen):
        """Draw main menu (Fight / Bag / Pokemon / Run). 2x2 grid."""
        positions = [
            (50, BOTTOM_ZONE_Y + 30),                           # Fight
            (SCREEN_WIDTH // 2 + 50, BOTTOM_ZONE_Y + 30),       # Bag
            (50, BOTTOM_ZONE_Y + 70),                           # Pokemon
            (SCREEN_WIDTH // 2 + 50, BOTTOM_ZONE_Y + 70)        # Run
        ]
        
        for i, option in enumerate(self.menu_options):
            color = DIALOG_TEXT
            prefix = "  "
            
            if i == self.selection_index:
                prefix = "> "
            
            text = prefix + option
            surface = self.font_menu.render(text, True, color)
            screen.blit(surface, positions[i])
    
    
    def _draw_attacks(self, screen):
        """Draw list of player's Pokemon attacks."""
        attacks = self.combat_state["player_pokemon"].attacks
        
        for i, attack in enumerate(attacks):
            prefix = "> " if i == self.selection_index else "  "
            text = f"{prefix}{attack.name} ({attack.type} — Puiss.{attack.power})"
            surface = self.font_menu.render(text, True, DIALOG_TEXT)
            screen.blit(surface, (50, BOTTOM_ZONE_Y + 20 + i * 30))
        
        # Back hint
        back_surface = self.font_hp.render("[Échap] Retour", True, (150, 150, 150))
        screen.blit(back_surface, (SCREEN_WIDTH - 180, BOTTOM_ZONE_Y + BOTTOM_ZONE_HEIGHT - 25))
    
    
    def _draw_bag(self, screen):
        """Draw list of usable items in combat."""
        items = self.combat_state.get("combat_items", [])
        
        if not items:
            surface = self.font_menu.render("  Aucun objet disponible", True, DIALOG_TEXT)
            screen.blit(surface, (50, BOTTOM_ZONE_Y + 30))
            return
        
        for i, (item, quantity) in enumerate(items):
            prefix = "> " if i == self.selection_index else "  "
            text = f"{prefix}{item.name} ×{quantity}"
            surface = self.font_menu.render(text, True, DIALOG_TEXT)
            screen.blit(surface, (50, BOTTOM_ZONE_Y + 20 + i * 28))
        
        back_surface = self.font_hp.render("[Échap] Retour", True, (150, 150, 150))
        screen.blit(back_surface, (SCREEN_WIDTH - 180, BOTTOM_ZONE_Y + BOTTOM_ZONE_HEIGHT - 25))
    
    
    def _draw_team(self, screen):
        """Draw player's team (Pokemon mode or Replacement mode)."""
        team = self.combat_state.get("player_team", [])
        
        for i, pokemon in enumerate(team):
            prefix = "> " if i == self.selection_index else "  "
            
            if pokemon.is_ko():
                status = " [KO]"
            else:
                status = ""
            
            text = f"{prefix}{pokemon.name} Nv.{pokemon.level} — PV: {pokemon.current_hp}/{pokemon.max_hp}{status}"
            surface = self.font_menu.render(text, True, DIALOG_TEXT)
            screen.blit(surface, (50, BOTTOM_ZONE_Y + 10 + i * 22))
        
        if self.mode != MODE_REPLACEMENT:
            back_surface = self.font_hp.render("[Échap] Retour", True, (150, 150, 150))
            screen.blit(back_surface, (SCREEN_WIDTH - 180, BOTTOM_ZONE_Y + BOTTOM_ZONE_HEIGHT - 25))
    
    
    def _draw_message(self, screen):
        """Draw a message in bottom zone."""
        if self.current_message:
            surface = self.font_message.render(self.current_message, True, DIALOG_TEXT)
            screen.blit(surface, (50, BOTTOM_ZONE_Y + 40))
        
        # "Press Space" hint
        hint_surface = self.font_hp.render("[Espace] Continuer", True, (150, 150, 150))
        screen.blit(hint_surface, (SCREEN_WIDTH - 220, BOTTOM_ZONE_Y + BOTTOM_ZONE_HEIGHT - 25))
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS - UTILITY
    # -------------------------------------------------------------------------
    
    def _create_placeholder(self, color):
        """Create a placeholder sprite (colored rectangle)."""
        surface = pygame.Surface((64, 64))
        surface.fill(color)
        return surface
    
    
    def _file_exists(self, path):
        """Check if a file exists."""
        import os
        return os.path.exists(path)
    
    
    def _consume_next_event(self):
        """Take next event from queue and prepare for display."""
        if not self.pending_events:
            self.current_event = None
            self.mode = MODE_MENU
            self.selection_index = 0
            return
        
        self.current_event = self.pending_events.pop(0)
        evt = self.current_event
        
        if evt["type"] == "attack":
            attacker_name = evt["attacker"].name
            attack_name = evt["attack_name"]
            self.current_message = f"{attacker_name} utilise {attack_name} !"
            self.mode = MODE_MESSAGE
            
            # Start damage animation if attack hit
            if evt["result"]["hit"] and not evt["result"]["immune"]:
                self._start_animation("damage_flash", evt["result"], evt["side"])
        
        elif evt["type"] == "ko":
            self.current_message = f"{evt['pokemon'].name} est KO !"
            self.mode = MODE_MESSAGE
            self._start_animation("ko", None, evt["side"])
        
        elif evt["type"] == "item_used":
            item_name = evt["item"].name
            if evt["effect"] == "heal":
                self.current_message = f"Vous utilisez {item_name} !"
            elif evt["effect"] == "boost":
                self.current_message = f"{evt['stat']} augmente !"
            elif evt["effect"] == "revive":
                self.current_message = f"{evt['target'].name} est réanimé !"
            else:
                self.current_message = f"Vous utilisez {item_name} !"
            self.mode = MODE_MESSAGE
        
        elif evt["type"] == "capture":
            if evt["result"]["capture_success"]:
                self.current_message = f"Gotcha ! {evt['result']['captured_pokemon'].name} a été capturé !"
            else:
                if evt["result"]["failure_reason"] == "trainer_combat":
                    self.current_message = "On ne peut pas capturer le Pokémon d'un dresseur !"
                else:
                    self.current_message = "Oh non ! Il s'est libéré !"
            self.mode = MODE_MESSAGE
        
        elif evt["type"] == "switch":
            if evt["side"] == "player":
                self.current_message = f"Go {evt['new_pokemon'].name} !"
            else:
                self.current_message = f"L'adversaire envoie {evt['new_pokemon'].name} !"
            self.mode = MODE_MESSAGE
            # Reload sprites for new Pokemon
            self.load_sprites(
                self.combat_state["player_pokemon"],
                self.combat_state["opponent_pokemon"]
            )
        
        elif evt["type"] == "xp":
            self.current_message = f"{evt['pokemon'].name} gagne {evt['xp_gained']} XP !"
            self.mode = MODE_MESSAGE
        
        elif evt["type"] == "level_up":
            self.current_message = f"{evt['pokemon'].name} monte au niveau {evt['new_level']} !"
            self.mode = MODE_MESSAGE
        
        elif evt["type"] == "evolution_possible":
            self.current_message = f"{evt['pokemon'].name} peut évoluer !"
            self.mode = MODE_MESSAGE
        
        elif evt["type"] == "flee":
            self.current_message = evt["message"]
            self.mode = MODE_MESSAGE
        
        elif evt["type"] == "flee_impossible":
            self.current_message = evt["message"]
            self.mode = MODE_MESSAGE
        
        elif evt["type"] == "replacement_choice":
            self.current_message = "Choisissez un Pokémon !"
            self.mode = MODE_REPLACEMENT
            self.selection_index = 0
        
        elif evt["type"] == "combat_end":
            if evt["result"] == "victory":
                self.current_message = "Vous avez gagné le combat !"
            else:
                self.current_message = "Vous avez perdu le combat..."
            self.mode = MODE_MESSAGE
        
        else:
            # Unknown event, skip
            self._consume_next_event()
    
    
    def _start_animation(self, anim_type, data, target_side):
        """Start a visual animation."""
        self.animation_active = True
        self.animation_type = anim_type
        self.animation_timer = 0
        self.animation_target = target_side
        self.animation_data = data