# =============================================================================
# COMBAT_UI.PY - COMBAT INTERFACE  (Pokemon DA — dark navy + gold)
# =============================================================================
#
# Layout:
#   Field area  (~70 % of screen height) — dark gradient / sprites / info panels
#   Command zone (~30 % of screen height) — dialog box (left) + buttons (right)
#
# Sprite placement:
#   Enemy  → top-RIGHT  (platform near horizon)
#   Ally   → bottom-LEFT (platform near command zone)
#
# Info panels:
#   Enemy HP  → top-LEFT
#   Ally HP   → bottom-RIGHT

import os
import pygame
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    HP_GREEN, HP_YELLOW, HP_RED,
)


# =============================================================================
# FONT HELPER
# =============================================================================

_FONT_SOLID = os.path.join("assets", "font", "Pokemon_Solid.ttf")

def _font(path, size):
    if os.path.exists(path):
        return pygame.font.Font(path, size)
    return pygame.font.Font(None, size + 6)


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

MODE_MENU        = "menu"
MODE_ATTACKS     = "attacks"
MODE_BAG         = "bag"
MODE_POKEMON     = "pokemon"
MODE_MESSAGE     = "message"
MODE_REPLACEMENT = "replacement"

# ---- Sprite sizes ----
SPRITE_SIZE_OPPONENT = 200
SPRITE_SIZE_PLAYER   = 230

# ---- Command zone (bottom ~28 %) ----
BOTTOM_ZONE_HEIGHT = 210
BOTTOM_ZONE_Y      = SCREEN_HEIGHT - BOTTOM_ZONE_HEIGHT

# Left portion = dialog area
DIALOG_AREA_W = 420

# ---- Field ----
FIELD_HORIZON = int(BOTTOM_ZONE_Y * 0.42)

# ---- Sprite X positions ----
OPPONENT_SPRITE_X = SCREEN_WIDTH - SPRITE_SIZE_OPPONENT - 100
PLAYER_SPRITE_X   = 80

# ---- Platform anchors ----
OPPONENT_PLATFORM_CX = OPPONENT_SPRITE_X + SPRITE_SIZE_OPPONENT // 2
OPPONENT_PLATFORM_Y  = FIELD_HORIZON + 22
PLAYER_PLATFORM_CX   = PLAYER_SPRITE_X + SPRITE_SIZE_PLAYER // 2
PLAYER_PLATFORM_Y    = BOTTOM_ZONE_Y - 28

# ---- Sprite Y derived from platform ----
OPPONENT_SPRITE_Y = OPPONENT_PLATFORM_Y - SPRITE_SIZE_OPPONENT
PLAYER_SPRITE_Y   = PLAYER_PLATFORM_Y   - SPRITE_SIZE_PLAYER

# ---- Info panels ----
OPPONENT_INFO_X = 24
OPPONENT_INFO_Y = 20
OPPONENT_INFO_W = 280
OPPONENT_INFO_H =  72

PLAYER_INFO_X   = SCREEN_WIDTH - 310
PLAYER_INFO_Y   = BOTTOM_ZONE_Y - 105
PLAYER_INFO_W   = 285
PLAYER_INFO_H   =  92

# ---- HP / XP bars ----
HP_BAR_WIDTH  = 160
HP_BAR_HEIGHT =   7

# ---- Animation durations ----
DAMAGE_FLASH_DURATION     = 0.4
HP_BAR_ANIMATION_DURATION = 0.5
KO_ANIMATION_DURATION     = 0.5

# ---- Pokemon DA palette ----
# Field background
C_BG_TOP    = ( 10,  14,  38)
C_BG_BTM    = ( 22,  32,  70)
C_STRIPE    = ( 28,  38,  80)

# Platform
C_PLATFORM_FILL = ( 30,  42,  88)
C_PLATFORM_RIM  = (255, 203,   5)

# Command zone
C_CMD_BG    = ( 14,  18,  48)
C_CMD_DLG   = ( 16,  22,  56)
C_CMD_SEP   = (255, 203,   5)   # gold

# Panels
C_PANEL_BG  = ( 16,  22,  52)
C_PANEL_BDR = (255, 203,   5)   # gold

# Text
C_TEXT_WHITE = (235, 235, 235)
C_TEXT_GOLD  = (255, 203,   5)
C_TEXT_GRAY  = (115, 115, 135)
C_TEXT_DARK  = ( 28,  24,  18)   # kept for dark-on-light attack buttons

# Button accent colours (vivid on dark background)
BTN_ACCENTS = [
    (220,  70,  50),   # Attaquer — red
    ( 58, 140, 230),   # Sac      — blue
    (160,  60, 200),   # Pokémon  — violet
    (115, 115, 135),   # Fuir     — gray
]

# Pokemon type colours
TYPE_COLORS = {
    "Normal":     (152, 152, 104),
    "Feu":        (212, 100,  36),
    "Eau":        ( 80, 120, 208),
    "Plante":     ( 92, 168,  58),
    "Électrique": (208, 178,  32),
    "Glace":      (118, 186, 192),
    "Combat":     (162,  36,  32),
    "Poison":     (132,  46, 132),
    "Sol":        (194, 162,  80),
    "Vol":        (138, 116, 210),
    "Psychique":  (210,  66, 108),
    "Insecte":    (138, 154,  20),
    "Roche":      (154, 132,  38),
    "Spectre":    ( 84,  62, 122),
    "Dragon":     ( 88,  38, 218),
    "Ténèbres":   ( 86,  62,  46),
    "Acier":      (154, 154, 174),
    "Fée":        (208, 122, 142),
    # lowercase fallbacks
    "normal":     (152, 152, 104),
    "feu":        (212, 100,  36),
    "eau":        ( 80, 120, 208),
    "plante":     ( 92, 168,  58),
    "electrik":   (208, 178,  32),
    "glace":      (118, 186, 192),
    "combat":     (162,  36,  32),
    "poison":     (132,  46, 132),
    "sol":        (194, 162,  80),
    "vol":        (138, 116, 210),
    "psy":        (210,  66, 108),
    "roche":      (154, 132,  38),
    "spectre":    ( 84,  62, 122),
    "dragon":     ( 88,  38, 218),
    "tenebres":   ( 86,  62,  46),
    "acier":      (154, 154, 174),
    # English fallbacks
    "fire":       (212, 100,  36),
    "water":      ( 80, 120, 208),
    "grass":      ( 92, 168,  58),
    "electric":   (208, 178,  32),
    "ice":        (118, 186, 192),
    "fighting":   (162,  36,  32),
    "ground":     (194, 162,  80),
    "flying":     (138, 116, 210),
    "psychic":    (210,  66, 108),
    "bug":        (138, 154,  20),
    "rock":       (154, 132,  38),
    "ghost":      ( 84,  62, 122),
    "dark":       ( 86,  62,  46),
    "steel":      (154, 154, 174),
    "fairy":      (208, 122, 142),
}


# =============================================================================
# COMBAT UI CLASS
# =============================================================================

class CombatUI:

    # -------------------------------------------------------------------------
    def __init__(self, game_manager):
        self.game_manager = game_manager

        self.font_title   = _font(_FONT_SOLID, 18)
        self.font_name    = _font(_FONT_SOLID, 16)
        self.font_hp      = _font(_FONT_SOLID, 15)
        self.font_menu    = _font(_FONT_SOLID, 20)
        self.font_message = _font(_FONT_SOLID, 18)
        self.font_small   = _font(_FONT_SOLID, 14)
        self.font_type    = _font(_FONT_SOLID, 13)

        self.mode            = MODE_MENU
        self.selection_index = 0

        self.player_sprite   = None
        self.opponent_sprite = None

        self.displayed_hp_player   = 0
        self.displayed_hp_opponent = 0
        self.target_hp_player      = 0
        self.target_hp_opponent    = 0

        self.animation_active = False
        self.animation_type   = None
        self.animation_timer  = 0
        self.animation_target = None
        self.animation_data   = None

        self.pending_events  = []
        self.current_event   = None
        self.current_message = ""

        self.combat_state = None
        self.menu_options = ["Attaquer", "Sac", "Pokémon", "Fuir"]

        self._team_sprites = {}

        # Pre-render static field background
        self._field_bg = self._make_field_bg()

    # -------------------------------------------------------------------------
    def _make_field_bg(self):
        """Pre-render the dark navy gradient + diagonal stripes field."""
        surf = pygame.Surface((SCREEN_WIDTH, BOTTOM_ZONE_Y))
        for y in range(BOTTOM_ZONE_Y):
            t = y / BOTTOM_ZONE_Y
            r = int(C_BG_TOP[0] + (C_BG_BTM[0] - C_BG_TOP[0]) * t)
            g = int(C_BG_TOP[1] + (C_BG_BTM[1] - C_BG_TOP[1]) * t)
            b = int(C_BG_TOP[2] + (C_BG_BTM[2] - C_BG_TOP[2]) * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        for i in range(-BOTTOM_ZONE_Y, SCREEN_WIDTH + BOTTOM_ZONE_Y, 120):
            pts = [
                (i,                   0),
                (i + 70,              0),
                (i + 70 + BOTTOM_ZONE_Y, BOTTOM_ZONE_Y),
                (i + BOTTOM_ZONE_Y,  BOTTOM_ZONE_Y),
            ]
            pygame.draw.polygon(surf, C_STRIPE, pts)
        return surf

    # -------------------------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------------------------

    def set_state(self, player_pokemon, opponent_pokemon, combat_type, player_team=None):
        combat_items = []
        player = self.game_manager.player
        if player is not None and hasattr(player, "inventory"):
            combat_items = player.inventory.get_usable_in_combat()

        self.combat_state = {
            "player_pokemon":   player_pokemon,
            "opponent_pokemon": opponent_pokemon,
            "combat_type":      combat_type,
            "player_team":      player_team.get_all() if player_team is not None else [],
            "combat_items":     combat_items,
        }
        if player_pokemon   is not None:
            self.target_hp_player   = player_pokemon.current_hp
        if opponent_pokemon is not None:
            self.target_hp_opponent = opponent_pokemon.current_hp

    def _crop_sprite(self, surface):
        bbox = surface.get_bounding_rect()
        if bbox.width == 0 or bbox.height == 0:
            return surface
        cropped = pygame.Surface((bbox.width, bbox.height), pygame.SRCALPHA)
        cropped.blit(surface, (0, 0), bbox)
        return cropped

    def load_sprites(self, player_pokemon, opponent_pokemon):
        try:
            if player_pokemon and player_pokemon.sprite_back \
                    and os.path.exists(player_pokemon.sprite_back):
                raw = pygame.image.load(player_pokemon.sprite_back).convert_alpha()
                self.player_sprite = self._crop_sprite(raw)
            else:
                self.player_sprite = self._placeholder((80, 100, 195))
        except Exception:
            self.player_sprite = self._placeholder((80, 100, 195))

        try:
            if opponent_pokemon and opponent_pokemon.sprite_front \
                    and os.path.exists(opponent_pokemon.sprite_front):
                raw = pygame.image.load(opponent_pokemon.sprite_front).convert_alpha()
                self.opponent_sprite = self._crop_sprite(raw)
            else:
                self.opponent_sprite = self._placeholder((195, 80, 80))
        except Exception:
            self.opponent_sprite = self._placeholder((195, 80, 80))

        self.displayed_hp_player   = player_pokemon.current_hp   if player_pokemon   else 0
        self.displayed_hp_opponent = opponent_pokemon.current_hp if opponent_pokemon else 0
        self.target_hp_player      = self.displayed_hp_player
        self.target_hp_opponent    = self.displayed_hp_opponent

    def set_events(self, events):
        self.pending_events = events.copy()
        self._consume_next_event()

    def set_mode(self, mode):
        self.mode = mode
        self.selection_index = 0
        if mode == MODE_REPLACEMENT and self.combat_state:
            team = self.combat_state.get("player_team", [])
            for i, pokemon in enumerate(team):
                if not pokemon.is_ko:
                    self.selection_index = i
                    break

    def next_event(self):
        if self.pending_events:
            self._consume_next_event()
            return True
        return False

    def is_animation_finished(self):
        return not self.animation_active

    def skip_animation(self):
        if self.animation_active:
            self.animation_active = False
            self.displayed_hp_player   = self.target_hp_player
            self.displayed_hp_opponent = self.target_hp_opponent

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        if self.mode == MODE_MESSAGE:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.next_event()
                return {"type": "advance_message"}

        if self.mode == MODE_MENU:
            if   event.key == pygame.K_UP:    self.selection_index = max(0, self.selection_index - 2)
            elif event.key == pygame.K_DOWN:  self.selection_index = min(3, self.selection_index + 2)
            elif event.key == pygame.K_LEFT:  self.selection_index = max(0, self.selection_index - 1)
            elif event.key == pygame.K_RIGHT: self.selection_index = min(3, self.selection_index + 1)
            elif event.key == pygame.K_ESCAPE:
                return {"type": "flee"}
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if   self.selection_index == 0: self.mode = MODE_ATTACKS; self.selection_index = 0
                elif self.selection_index == 1: self.mode = MODE_BAG;     self.selection_index = 0
                elif self.selection_index == 2: self.mode = MODE_POKEMON; self.selection_index = 0
                elif self.selection_index == 3: return {"type": "flee"}

        elif self.mode == MODE_ATTACKS:
            attacks = self.combat_state["player_pokemon"].attacks
            n = len(attacks)
            if n == 0:
                if event.key == pygame.K_ESCAPE:
                    self.mode = MODE_MENU; self.selection_index = 0
            else:
                if   event.key == pygame.K_UP:
                    self.selection_index = max(0, self.selection_index - 2)
                elif event.key == pygame.K_DOWN:
                    self.selection_index = min(n - 1, self.selection_index + 2)
                elif event.key == pygame.K_LEFT:
                    if self.selection_index % 2 == 1:
                        self.selection_index -= 1
                elif event.key == pygame.K_RIGHT:
                    if self.selection_index % 2 == 0 and self.selection_index + 1 < n:
                        self.selection_index += 1
                elif event.key == pygame.K_ESCAPE:
                    self.mode = MODE_MENU; self.selection_index = 0
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if self.selection_index < n:
                        self.mode = MODE_MESSAGE
                        return {"type": "attack", "attack": attacks[self.selection_index]}

        elif self.mode == MODE_BAG:
            items = self.combat_state.get("combat_items", [])
            if   event.key == pygame.K_UP:     self.selection_index = max(0, self.selection_index-1)
            elif event.key == pygame.K_DOWN:
                if items: self.selection_index = min(len(items)-1, self.selection_index+1)
            elif event.key == pygame.K_ESCAPE: self.mode = MODE_MENU; self.selection_index = 0
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if 0 <= self.selection_index < len(items):
                    item, _ = items[self.selection_index]
                    return {"type": "item", "item_id": item.id}

        elif self.mode == MODE_POKEMON:
            team = self.combat_state.get("player_team", [])
            n = len(team)
            if   event.key == pygame.K_UP:    self.selection_index = max(0, self.selection_index - 2)
            elif event.key == pygame.K_DOWN:  self.selection_index = min(n - 1, self.selection_index + 2)
            elif event.key == pygame.K_LEFT:
                if self.selection_index % 2 == 1:
                    self.selection_index -= 1
            elif event.key == pygame.K_RIGHT:
                if self.selection_index % 2 == 0 and self.selection_index + 1 < n:
                    self.selection_index += 1
            elif event.key == pygame.K_ESCAPE: self.mode = MODE_MENU; self.selection_index = 0
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self.selection_index < n and not team[self.selection_index].is_ko:
                    return {"type": "switch", "index": self.selection_index}

        elif self.mode == MODE_REPLACEMENT:
            team = self.combat_state.get("player_team", [])
            if   event.key == pygame.K_UP:   self.selection_index = max(0, self.selection_index-1)
            elif event.key == pygame.K_DOWN: self.selection_index = min(len(team)-1, self.selection_index+1)
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self.selection_index < len(team) and not team[self.selection_index].is_ko:
                    return {"type": "replacement", "index": self.selection_index}

        return None

    def update(self, dt):
        speed = 100
        for d_attr, t_attr in (("displayed_hp_player",   "target_hp_player"),
                                ("displayed_hp_opponent", "target_hp_opponent")):
            d, t = getattr(self, d_attr), getattr(self, t_attr)
            if d != t:
                setattr(self, d_attr, max(t, d - speed*dt) if d > t else min(t, d + speed*dt))

        if self.animation_active:
            self.animation_timer += dt
            if self.animation_type == "damage_flash" and self.animation_timer >= DAMAGE_FLASH_DURATION:
                self.animation_active = False
            if self.animation_type == "ko"           and self.animation_timer >= KO_ANIMATION_DURATION:
                self.animation_active = False

    def draw(self, screen):
        if self.combat_state is None:
            return
        self._draw_background(screen)
        self._draw_sprites(screen)
        self._draw_opponent_info(screen)
        self._draw_player_info(screen)
        self._draw_command_zone(screen)
        if self.mode in (MODE_POKEMON, MODE_REPLACEMENT):
            self._overlay_team(screen)
        elif self.mode == MODE_BAG:
            self._overlay_bag(screen)

    # =========================================================================
    # FIELD DRAWING
    # =========================================================================

    def _draw_background(self, screen):
        """Dark navy gradient field with gold-rimmed platforms."""
        screen.blit(self._field_bg, (0, 0))

        # Soft shadow at command zone top
        sh = pygame.Surface((SCREEN_WIDTH, 12), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 60))
        screen.blit(sh, (0, BOTTOM_ZONE_Y - 6))

        # Gold-rimmed platforms
        for cx, cy, pw in (
            (OPPONENT_PLATFORM_CX, OPPONENT_PLATFORM_Y, 180),
            (PLAYER_PLATFORM_CX,   PLAYER_PLATFORM_Y,   200),
        ):
            pygame.draw.ellipse(screen, C_PLATFORM_FILL,
                                (cx - pw//2, cy - 14, pw, 28))
            pygame.draw.ellipse(screen, C_PLATFORM_RIM,
                                (cx - pw//2, cy - 14, pw, 28), 2)

    def _draw_sprites(self, screen):
        for side, sx, sy, size, sattr in (
            ("opponent", OPPONENT_SPRITE_X, OPPONENT_SPRITE_Y,
             SPRITE_SIZE_OPPONENT, "opponent_sprite"),
            ("player",   PLAYER_SPRITE_X,   PLAYER_SPRITE_Y,
             SPRITE_SIZE_PLAYER,   "player_sprite"),
        ):
            sprite = getattr(self, sattr)
            if sprite is None:
                continue
            draw_it, oy = True, 0

            if self.animation_active and self.animation_target == side:
                if self.animation_type == "damage_flash":
                    if int(self.animation_timer * 15) % 2 == 0:
                        draw_it = False
                elif self.animation_type == "ko":
                    oy = int(self.animation_timer / KO_ANIMATION_DURATION * 100)

            if draw_it:
                scaled = pygame.transform.scale(sprite, (size, size))
                screen.blit(scaled, (sx, sy + oy))

    # =========================================================================
    # INFO PANELS
    # =========================================================================

    def _panel(self, screen, x, y, w, h):
        """Dark navy panel with gold border + corner accents."""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((*C_PANEL_BG, 225))
        screen.blit(surf, (x, y))
        pygame.draw.rect(screen, C_PANEL_BDR, (x, y, w, h), 2)
        # Corner accents
        size = 8
        for ax, dx in ((x, 1), (x + w, -1)):
            for ay, dy in ((y, 1), (y + h, -1)):
                pygame.draw.line(screen, C_PANEL_BDR, (ax, ay), (ax + dx*size, ay), 2)
                pygame.draw.line(screen, C_PANEL_BDR, (ax, ay), (ax, ay + dy*size), 2)

    def _draw_opponent_info(self, screen):
        pk = self.combat_state["opponent_pokemon"]
        if pk is None:
            return
        x, y, w, h = OPPONENT_INFO_X, OPPONENT_INFO_Y, OPPONENT_INFO_W, OPPONENT_INFO_H
        self._panel(screen, x, y, w, h)

        ns = self.font_title.render(pk.name,          True, C_TEXT_WHITE)
        ls = self.font_name .render(f"Nv.{pk.level}", True, C_TEXT_GOLD)
        screen.blit(ns, (x + 12, y + 8))
        screen.blit(ls, (x + w - ls.get_width() - 12, y + 10))

        bar_x = x + 42
        bar_y = y + 44
        pvs = self.font_small.render("PV", True, C_TEXT_GRAY)
        screen.blit(pvs, (x + 12, bar_y - 4))
        self._hp_bar(screen, bar_x, bar_y, w - 42 - 16,
                     self.displayed_hp_opponent, pk.max_hp)

    def _draw_player_info(self, screen):
        pk = self.combat_state["player_pokemon"]
        if pk is None:
            return
        x, y, w, h = PLAYER_INFO_X, PLAYER_INFO_Y, PLAYER_INFO_W, PLAYER_INFO_H
        self._panel(screen, x, y, w, h)

        ns = self.font_title.render(pk.name,          True, C_TEXT_WHITE)
        ls = self.font_name .render(f"Nv.{pk.level}", True, C_TEXT_GOLD)
        screen.blit(ns, (x + 12, y + 8))
        screen.blit(ls, (x + w - ls.get_width() - 12, y + 10))

        bar_x = x + 42
        bar_y = y + 42
        bar_w = w - 42 - 16
        pvs = self.font_small.render("PV", True, C_TEXT_GRAY)
        screen.blit(pvs, (x + 12, bar_y - 4))
        self._hp_bar(screen, bar_x, bar_y, bar_w,
                     self.displayed_hp_player, pk.max_hp)

        hp_s = self.font_hp.render(
            f"{int(self.displayed_hp_player)}/{pk.max_hp}", True, C_TEXT_WHITE)
        screen.blit(hp_s, (x + w - hp_s.get_width() - 12, bar_y + 12))

        if pk.xp_for_next_level > 0:
            xp_y = bar_y + 30
            exs = self.font_small.render("EXP", True, C_TEXT_GRAY)
            screen.blit(exs, (x + 12, xp_y - 2))
            xr = pk.current_xp / pk.xp_for_next_level
            self._bar(screen, bar_x, xp_y + 2, bar_w, 4, xr, (96, 136, 210))

    # =========================================================================
    # BAR PRIMITIVES
    # =========================================================================

    def _hp_bar(self, screen, x, y, width, cur, mx):
        if mx == 0:
            return
        ratio = max(0.0, min(1.0, cur / mx))
        color = HP_GREEN if ratio > 0.5 else (HP_YELLOW if ratio > 0.2 else HP_RED)
        self._bar(screen, x, y, width, HP_BAR_HEIGHT, ratio, color)

    def _bar(self, screen, x, y, width, height, ratio, color):
        # Track
        pygame.draw.rect(screen, (10, 14, 38), (x-1, y-1, width+2, height+2), border_radius=4)
        pygame.draw.rect(screen, (20, 26, 55), (x,   y,   width,   height),   border_radius=3)
        # Fill
        fw = int(width * ratio)
        if fw > 0:
            pygame.draw.rect(screen, color, (x, y, fw, height), border_radius=3)
            lc = tuple(min(255, c + 52) for c in color)
            pygame.draw.line(screen, lc, (x, y), (x + fw - 1, y))

    # =========================================================================
    # COMMAND ZONE
    # =========================================================================

    def _draw_command_zone(self, screen):
        # Dark navy base
        pygame.draw.rect(screen, C_CMD_BG,
                         (0, BOTTOM_ZONE_Y, SCREEN_WIDTH, BOTTOM_ZONE_HEIGHT))
        # Gold top separator
        pygame.draw.line(screen, C_CMD_SEP,
                         (0, BOTTOM_ZONE_Y), (SCREEN_WIDTH, BOTTOM_ZONE_Y), 2)

        if   self.mode == MODE_MENU:    self._view_menu(screen)
        elif self.mode == MODE_ATTACKS: self._view_attacks(screen)
        elif self.mode == MODE_MESSAGE: self._view_message(screen)

    # ---- MENU ----------------------------------------------------------------

    def _view_menu(self, screen):
        # Dialog section (slightly lighter navy)
        pygame.draw.rect(screen, C_CMD_DLG,
                         (0, BOTTOM_ZONE_Y, DIALOG_AREA_W, BOTTOM_ZONE_HEIGHT))
        # Vertical gold separator
        pygame.draw.line(screen, C_CMD_SEP,
                         (DIALOG_AREA_W, BOTTOM_ZONE_Y + 14),
                         (DIALOG_AREA_W, BOTTOM_ZONE_Y + BOTTOM_ZONE_HEIGHT - 14), 1)

        # "Que faire ?" centered in dialog area
        qs = self.font_message.render("Que faire ?", True, C_TEXT_GOLD)
        qx = (DIALOG_AREA_W - qs.get_width())  // 2
        qy = BOTTOM_ZONE_Y + (BOTTOM_ZONE_HEIGHT - qs.get_height()) // 2
        screen.blit(qs, (qx, qy))

        # 2×2 button grid
        avail_w = SCREEN_WIDTH - DIALOG_AREA_W - 48
        avail_h = BOTTOM_ZONE_HEIGHT - 40
        gap_x, gap_y = 12, 12
        btn_w = (avail_w - gap_x) // 2
        btn_h = (avail_h - gap_y) // 2

        bx0 = DIALOG_AREA_W + 18
        bx1 = bx0 + btn_w + gap_x
        by0 = BOTTOM_ZONE_Y + 20
        by1 = by0 + btn_h + gap_y

        for i, label in enumerate(self.menu_options):
            bx = bx0 if i % 2 == 0 else bx1
            by = by0 if i < 2      else by1
            self._button(screen, bx, by, btn_w, btn_h, label,
                         BTN_ACCENTS[i], i == self.selection_index)

    def _button(self, screen, x, y, w, h, label, accent, selected):
        if selected:
            # Filled accent + top highlight
            pygame.draw.rect(screen, accent, (x, y, w, h), border_radius=8)
            hl = pygame.Surface((w - 4, max(1, h // 3)), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 30))
            screen.blit(hl, (x + 2, y + 2))
            pygame.draw.rect(screen, C_TEXT_GOLD, (x, y, w, h), 2, border_radius=8)
            tc = (255, 255, 255)
        else:
            # Dark navy fill + accent border
            pygame.draw.rect(screen, (22, 30, 68), (x, y, w, h), border_radius=8)
            pygame.draw.rect(screen, accent,       (x, y, w, h), 2, border_radius=8)
            tc = tuple(min(255, c + 60) for c in accent)

        ts = self.font_menu.render(label, True, tc)
        screen.blit(ts, (x + (w - ts.get_width())  // 2,
                         y + (h - ts.get_height()) // 2))

    # ---- ATTACKS -------------------------------------------------------------

    def _view_attacks(self, screen):
        attacks = self.combat_state["player_pokemon"].attacks

        if not attacks:
            msg = self.font_menu.render("Aucune attaque disponible !", True, C_TEXT_GRAY)
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2,
                              BOTTOM_ZONE_Y + BOTTOM_ZONE_HEIGHT // 2 - msg.get_height() // 2))
            self._hint(screen, "[ECHAP] Retour")
            return

        pad = 18
        gap = 12
        btn_w = (SCREEN_WIDTH - pad * 2 - gap) // 2
        btn_h = (BOTTOM_ZONE_HEIGHT - pad * 2 - gap) // 2
        xs = [pad, pad + btn_w + gap]
        ys = [BOTTOM_ZONE_Y + pad, BOTTOM_ZONE_Y + pad + btn_h + gap]

        for i, atk in enumerate(attacks[:4]):
            bx, by = xs[i % 2], ys[i // 2]
            sel    = (i == self.selection_index)
            tcolor = TYPE_COLORS.get(atk.get("type", "Normal"), (148, 148, 104))

            if sel:
                bg = tcolor
                tc = (255, 255, 255)
                bc = C_TEXT_GOLD
                bw = 2
            else:
                bg = tuple(max(0, c - 50) for c in tcolor)
                tc = tuple(min(255, c + 80) for c in tcolor)
                bc = tuple(min(255, c + 20) for c in tcolor)
                bw = 1

            pygame.draw.rect(screen, bg, (bx, by, btn_w, btn_h), border_radius=7)
            pygame.draw.rect(screen, bc, (bx, by, btn_w, btn_h), bw, border_radius=7)

            # Attack name
            ns = self.font_menu.render(atk["name"], True, tc)
            screen.blit(ns, (bx + 9, by + 9))

            # Power
            pw   = atk.get("power", 0)
            pw_s = self.font_small.render(f"Puiss. {pw}" if pw else "Statut", True, tc)
            screen.blit(pw_s, (bx + btn_w - pw_s.get_width() - 9, by + 11))

            # Type badge
            tname     = atk.get("type", "Normal")
            badge_clr = tuple(max(0, c - 44) for c in tcolor)
            badge_w   = max(52, self.font_type.size(tname)[0] + 12)
            pygame.draw.rect(screen, badge_clr,
                             (bx + 8, by + btn_h - 24, badge_w, 17), border_radius=8)
            bs = self.font_type.render(tname, True, (235, 235, 235))
            screen.blit(bs, (bx + 13, by + btn_h - 23))

        self._hint(screen, "[ECHAP] Retour")

    # ---- BAG -----------------------------------------------------------------

    def _view_bag(self, screen):
        items = self.combat_state.get("combat_items", [])

        ts = self.font_name.render("Objets — combat", True, C_TEXT_GOLD)
        screen.blit(ts, (22, BOTTOM_ZONE_Y + 13))

        if not items:
            es = self.font_menu.render("Aucun objet disponible", True, C_TEXT_GRAY)
            screen.blit(es, (22, BOTTOM_ZONE_Y + 55))
        else:
            for i, (item, qty) in enumerate(items):
                ry  = BOTTOM_ZONE_Y + 46 + i * 35
                sel = (i == self.selection_index)
                if sel:
                    hl = pygame.Surface((SCREEN_WIDTH - 28, 27), pygame.SRCALPHA)
                    hl.fill((*C_TEXT_GOLD, 28))
                    screen.blit(hl, (14, ry - 3))
                    pygame.draw.rect(screen, C_TEXT_GOLD,
                                     (14, ry - 3, SCREEN_WIDTH - 28, 27), 1, border_radius=5)
                pfx = "▶  " if sel else "    "
                cs  = self.font_menu.render(
                    f"{pfx}{item.name}  ×{qty}", True,
                    C_TEXT_GOLD if sel else C_TEXT_WHITE)
                screen.blit(cs, (22, ry))

        self._hint(screen, "[ECHAP] Retour")

    # ---- TEAM ----------------------------------------------------------------

    def _view_team(self, screen):
        team  = self.combat_state.get("player_team", [])
        title = "Choisissez un Pokemon !" if self.mode == MODE_REPLACEMENT else "Equipe"
        ts    = self.font_name.render(title, True, C_TEXT_GOLD)
        screen.blit(ts, (22, BOTTOM_ZONE_Y + 11))

        for i, pk in enumerate(team):
            ry  = BOTTOM_ZONE_Y + 44 + i * 33
            sel = (i == self.selection_index)
            ko  = pk.is_ko

            if sel:
                accent = (200, 60, 60) if ko else C_TEXT_GOLD
                hl = pygame.Surface((SCREEN_WIDTH - 28, 25), pygame.SRCALPHA)
                hl.fill((*accent, 28))
                screen.blit(hl, (14, ry - 2))
                pygame.draw.rect(screen, accent,
                                 (14, ry - 2, SCREEN_WIDTH - 28, 25), 1, border_radius=5)

            pfx = "▶  " if sel else "    "
            nc  = (220, 70, 70) if ko else (C_TEXT_GOLD if sel else C_TEXT_WHITE)
            ns  = self.font_menu.render(
                f"{pfx}{pk.name}  Nv.{pk.level}", True, nc)
            screen.blit(ns, (22, ry))

            if ko:
                ks = self.font_hp.render("KO", True, (220, 70, 70))
                screen.blit(ks, (SCREEN_WIDTH - 66, ry + 4))
            else:
                hs = self.font_hp.render(
                    f"{pk.current_hp}/{pk.max_hp}", True, C_TEXT_GRAY)
                screen.blit(hs, (SCREEN_WIDTH - hs.get_width() - 66, ry + 4))
                r   = pk.current_hp / pk.max_hp if pk.max_hp > 0 else 0
                clr = HP_GREEN if r > 0.5 else (HP_YELLOW if r > 0.2 else HP_RED)
                self._bar(screen, SCREEN_WIDTH - 62, ry + 8, 50, 6, r, clr)

        if self.mode != MODE_REPLACEMENT:
            self._hint(screen, "[ECHAP] Retour")

    # ---- MESSAGE -------------------------------------------------------------

    def _view_message(self, screen):
        if self.current_message:
            lines   = self._wrap(self.current_message, self.font_message,
                                 SCREEN_WIDTH - 80)
            total_h = len(lines) * 36
            start_y = BOTTOM_ZONE_Y + (BOTTOM_ZONE_HEIGHT - total_h) // 2 - 6
            for j, line in enumerate(lines):
                ls = self.font_message.render(line, True, C_TEXT_WHITE)
                screen.blit(ls, (38, start_y + j * 36))

        self._hint(screen, "[ESPACE] Continuer")

    # ---- HINT ----------------------------------------------------------------

    def _hint(self, screen, text):
        hs = self.font_small.render(text, True, C_TEXT_GRAY)
        screen.blit(hs, (SCREEN_WIDTH  - hs.get_width()  - 12,
                         BOTTOM_ZONE_Y + BOTTOM_ZONE_HEIGHT - hs.get_height() - 8))

    # =========================================================================
    # FULL-SCREEN OVERLAYS
    # =========================================================================

    def _get_team_sprite(self, pokemon, size=96):
        key = (id(pokemon), size)
        if key not in self._team_sprites:
            try:
                raw = pygame.image.load(pokemon.sprite_front).convert_alpha()
                self._team_sprites[key] = pygame.transform.scale(raw, (size, size))
            except Exception:
                s = pygame.Surface((size, size), pygame.SRCALPHA)
                s.fill((60, 80, 120))
                self._team_sprites[key] = s
        return self._team_sprites[key]

    def _overlay_team(self, screen):
        # Dark background
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))

        team = self.combat_state.get("player_team", [])
        is_replacement = (self.mode == MODE_REPLACEMENT)
        title_txt = "Choisissez un Pokémon !" if is_replacement else "Équipe Pokémon"

        PW, PH = 900, 540
        px = (SCREEN_WIDTH - PW) // 2
        py = (SCREEN_HEIGHT - PH) // 2
        self._panel(screen, px, py, PW, PH)

        ts = self.font_name.render(title_txt, True, C_TEXT_GOLD)
        screen.blit(ts, (px + 20, py + 14))

        CARD_W  = (PW - 60) // 2
        CARD_H  = 130
        GAP_X   = 20
        GAP_Y   = 10
        SPRITE  = 96
        gx = px + 20
        gy = py + 50

        for i, pk in enumerate(team[:6]):
            col = i % 2
            row = i // 2
            cx  = gx + col * (CARD_W + GAP_X)
            cy  = gy + row * (CARD_H + GAP_Y)
            sel = (i == self.selection_index)
            ko  = pk.is_ko

            # Card background
            card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            if ko:
                card_surf.fill((55, 18, 18, 230))
            elif sel:
                card_surf.fill((22, 30, 72, 245))
            else:
                card_surf.fill((16, 22, 52, 225))
            screen.blit(card_surf, (cx, cy))

            border_col = (180, 50, 50) if ko else (C_TEXT_GOLD if sel else (45, 55, 95))
            pygame.draw.rect(screen, border_col, (cx, cy, CARD_W, CARD_H), 2, border_radius=6)

            # Sprite
            sprite = self._get_team_sprite(pk, SPRITE)
            sy = cy + (CARD_H - SPRITE) // 2
            if ko:
                faded = sprite.copy()
                faded.set_alpha(50)
                screen.blit(faded, (cx + 10, sy))
            else:
                screen.blit(sprite, (cx + 10, sy))

            # Text area
            tx = cx + SPRITE + 22
            tw = CARD_W - SPRITE - 30

            name_col = (200, 70, 70) if ko else (C_TEXT_GOLD if sel else C_TEXT_WHITE)
            ns = self.font_name.render(pk.name, True, name_col)
            screen.blit(ns, (tx, cy + 12))

            lv_s = self.font_hp.render(f"Nv.{pk.level}", True, C_TEXT_GRAY)
            screen.blit(lv_s, (tx + tw - lv_s.get_width(), cy + 14))

            if ko:
                ko_s = self.font_menu.render("K.O.", True, (220, 70, 70))
                screen.blit(ko_s, (tx + (tw - ko_s.get_width()) // 2, cy + 52))
            else:
                hp_s = self.font_hp.render(f"{pk.current_hp}/{pk.max_hp} PV", True, C_TEXT_GRAY)
                screen.blit(hp_s, (tx, cy + 40))
                r   = pk.current_hp / pk.max_hp if pk.max_hp > 0 else 0
                clr = HP_GREEN if r > 0.5 else (HP_YELLOW if r > 0.2 else HP_RED)
                self._bar(screen, tx, cy + 62, tw, 8, r, clr)

        if not is_replacement:
            hint_s = self.font_small.render("[ECHAP] Retour", True, C_TEXT_GRAY)
            screen.blit(hint_s,
                        (px + PW - hint_s.get_width() - 14,
                         py + PH - hint_s.get_height() - 10))

    def _overlay_bag(self, screen):
        CAT_COLORS = {
            "heal":     ( 80, 200, 100),
            "pokeball": (200,  80,  80),
            "boost":    (200, 170,  60),
            "revive":   (140, 100, 200),
            "status":   ( 80, 160, 220),
        }

        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))

        items = self.combat_state.get("combat_items", [])

        PW, PH = 900, 480
        px = (SCREEN_WIDTH - PW) // 2
        py = (SCREEN_HEIGHT - PH) // 2
        self._panel(screen, px, py, PW, PH)

        ts = self.font_name.render("Sac — objets de combat", True, C_TEXT_GOLD)
        screen.blit(ts, (px + 20, py + 14))

        if not items:
            es = self.font_menu.render("Aucun objet disponible", True, C_TEXT_GRAY)
            screen.blit(es, (px + (PW - es.get_width()) // 2, py + PH // 2 - 10))
            hint_s = self.font_small.render("[ECHAP] Retour", True, C_TEXT_GRAY)
            screen.blit(hint_s,
                        (px + PW - hint_s.get_width() - 14,
                         py + PH - hint_s.get_height() - 10))
            return

        # Left list panel
        LIST_W  = PW // 2 - 10
        ITEM_H  = 46
        VISIBLE = 8
        scroll  = max(0, self.selection_index - VISIBLE + 1)
        sep_x   = px + LIST_W + 10

        pygame.draw.line(screen, (40, 50, 90),
                         (sep_x, py + 45), (sep_x, py + PH - 20), 1)

        lx = px + 14
        ly = py + 48
        for i in range(VISIBLE):
            idx = scroll + i
            if idx >= len(items):
                break
            item, qty = items[idx]
            ry  = ly + i * ITEM_H
            sel = (idx == self.selection_index)
            cat_col = CAT_COLORS.get(item.category, C_TEXT_GRAY)

            if sel:
                hl = pygame.Surface((LIST_W - 8, ITEM_H - 4), pygame.SRCALPHA)
                hl.fill((*cat_col, 30))
                screen.blit(hl, (lx, ry))
                pygame.draw.rect(screen, cat_col,
                                 (lx, ry, LIST_W - 8, ITEM_H - 4), 1, border_radius=4)

            # Category dot
            pygame.draw.circle(screen, cat_col, (lx + 12, ry + ITEM_H // 2 - 2), 6)

            # Name
            nc = C_TEXT_GOLD if sel else C_TEXT_WHITE
            ns = self.font_menu.render(item.name, True, nc)
            screen.blit(ns, (lx + 26, ry + 6))

            # Quantity
            qc = C_TEXT_GOLD if sel else C_TEXT_GRAY
            qs = self.font_hp.render(f"×{qty}", True, qc)
            screen.blit(qs, (lx + LIST_W - qs.get_width() - 12, ry + 10))

        # Scroll arrows
        if scroll > 0:
            a = self.font_small.render("▲", True, C_TEXT_GRAY)
            screen.blit(a, (lx + LIST_W // 2 - a.get_width() // 2, ly - 14))
        if scroll + VISIBLE < len(items):
            a = self.font_small.render("▼", True, C_TEXT_GRAY)
            screen.blit(a, (lx + LIST_W // 2 - a.get_width() // 2,
                            ly + VISIBLE * ITEM_H + 2))

        # Right detail panel
        sel_item, sel_qty = items[self.selection_index]
        cat_col = CAT_COLORS.get(sel_item.category, C_TEXT_GRAY)
        rx = sep_x + 16
        rw = PW - LIST_W - 36
        dy = py + 50

        # Item name
        big_ns = self.font_menu.render(sel_item.name, True, C_TEXT_WHITE)
        screen.blit(big_ns, (rx, dy))

        # Category badge
        badge = pygame.Surface((rw, 22), pygame.SRCALPHA)
        badge.fill((*cat_col, 55))
        screen.blit(badge, (rx, dy + 30))
        pygame.draw.rect(screen, cat_col, (rx, dy + 30, rw, 22), 1, border_radius=3)
        cat_s = self.font_small.render(sel_item.category.upper(), True, cat_col)
        screen.blit(cat_s, (rx + 8, dy + 34))

        # Description
        if sel_item.description:
            desc_lines = self._wrap(sel_item.description, self.font_small, rw - 10)
            for j, line in enumerate(desc_lines[:3]):
                ds = self.font_small.render(line, True, C_TEXT_GRAY)
                screen.blit(ds, (rx, dy + 62 + j * 20))

        # Effect value
        if sel_item.effect_value:
            if sel_item.category == "heal":
                eff_txt = f"+{sel_item.effect_value} PV"
            elif sel_item.category == "boost":
                stat = sel_item.target_stat or ""
                eff_txt = f"+{sel_item.effect_value}% {stat}"
            elif sel_item.category == "revive":
                eff_txt = f"Récupère {sel_item.effect_value}% PV max"
            elif sel_item.category == "pokeball":
                eff_txt = f"Taux de capture: {sel_item.effect_value}%"
            else:
                eff_txt = str(sel_item.effect_value)
            eff_s = self.font_name.render(eff_txt, True, cat_col)
            screen.blit(eff_s, (rx, dy + 130))

        # Quantity remaining
        qty_s = self.font_hp.render(f"Quantité: ×{sel_qty}", True, C_TEXT_GRAY)
        screen.blit(qty_s, (rx, dy + 158))

        # Use action
        use_s = self.font_name.render("[ENTRÉE] Utiliser", True, C_TEXT_GOLD)
        screen.blit(use_s, (rx, dy + 200))

        # Hint
        hint_s = self.font_small.render("[ECHAP] Retour", True, C_TEXT_GRAY)
        screen.blit(hint_s,
                    (px + PW - hint_s.get_width() - 14,
                     py + PH - hint_s.get_height() - 10))

    # =========================================================================
    # UTILITY
    # =========================================================================

    def _wrap(self, text, font, max_w):
        words, lines, cur = text.split(" "), [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        return lines or [""]

    def _placeholder(self, color):
        s = pygame.Surface((200, 200))
        s.fill(color)
        return s

    # =========================================================================
    # EVENT QUEUE
    # =========================================================================

    def _consume_next_event(self):
        if not self.pending_events:
            self.current_event = None
            self.mode = MODE_MENU
            self.selection_index = 0
            return

        self.current_event = evt = self.pending_events.pop(0)

        if evt["type"] == "attack":
            self.current_message = f"{evt['attacker'].name} utilise {evt['attack_name']} !"
            self.mode = MODE_MESSAGE
            if evt["result"]["hit"] and not evt["result"]["immune"]:
                self._start_anim("damage_flash", evt["result"], evt["side"])

        elif evt["type"] == "ko":
            self.current_message = f"{evt['pokemon'].name} est KO !"
            self.mode = MODE_MESSAGE
            self._start_anim("ko", None, evt["side"])

        elif evt["type"] == "item_used":
            iname = evt["item"].name
            if   evt["effect"] == "heal":   self.current_message = f"Vous utilisez {iname} !"
            elif evt["effect"] == "boost":  self.current_message = f"{evt['stat']} augmente !"
            elif evt["effect"] == "revive": self.current_message = f"{evt['target'].name} est réanimé !"
            else:                           self.current_message = f"Vous utilisez {iname} !"
            self.mode = MODE_MESSAGE

        elif evt["type"] == "capture":
            if evt["result"]["capture_success"]:
                self.current_message = f"Gotcha ! {evt['result']['captured_pokemon'].name} a été capturé !"
            else:
                self.current_message = (
                    "On ne peut pas capturer le Pokemon d'un dresseur !"
                    if evt["result"]["failure_reason"] == "trainer_combat"
                    else "Oh non ! Il s'est libéré !")
            self.mode = MODE_MESSAGE

        elif evt["type"] == "message":
            self.current_message = evt.get("text", "")
            self.mode = MODE_MESSAGE

        elif evt["type"] == "switch":
            np = evt.get("new_pokemon") or evt.get("new")
            if np:
                self.current_message = (f"Go {np.name} !"
                                        if evt.get("side") == "player"
                                        else f"L'adversaire envoie {np.name} !")
            self.mode = MODE_MESSAGE
            self.load_sprites(self.combat_state["player_pokemon"],
                              self.combat_state["opponent_pokemon"])

        elif evt["type"] == "xp":
            self.current_message = f"{evt['pokemon'].name} gagne {evt['xp_gained']} XP !"
            self.mode = MODE_MESSAGE

        elif evt["type"] == "level_up":
            self.current_message = f"{evt['pokemon'].name} monte au niveau {evt['new_level']} !"
            self.mode = MODE_MESSAGE

        elif evt["type"] == "evolution_possible":
            self.current_message = f"{evt['pokemon'].name} peut évoluer !"
            self.mode = MODE_MESSAGE

        elif evt["type"] in ("flee", "flee_impossible"):
            self.current_message = evt["message"]
            self.mode = MODE_MESSAGE

        elif evt["type"] == "replacement_choice":
            self.current_message = "Choisissez un Pokemon !"
            self.set_mode(MODE_REPLACEMENT)

        elif evt["type"] == "combat_end":
            self.current_message = ("Vous avez gagné le combat !"
                                    if evt["result"] == "victory"
                                    else "Vous avez perdu le combat...")
            self.mode = MODE_MESSAGE

        else:
            self._consume_next_event()

    def _start_anim(self, anim_type, data, target):
        self.animation_active = True
        self.animation_type   = anim_type
        self.animation_timer  = 0
        self.animation_target = target
        self.animation_data   = data
