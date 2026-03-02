# =============================================================================
# STATE_CHEAT.PY - INTERFACE TRICHE POKÉDEX
# =============================================================================

import pygame
from states.state import State
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TOTAL_POKEMON, POKEMON_SPRITES_DIR
from ui.poke_style import (
    C_GOLD, C_GOLD_DIM, C_WHITE, C_GRAY, C_GREEN, C_BLUE,
    font, panel, corner_accents, text_c, blit_clipped,
)

C_RED    = (220, 60,  60)
C_ORANGE = (230, 130, 40)

VISIBLE_LINES = 11
LIST_W        = 340

TYPE_COLORS = {
    "feu":      (230,  80,  50),
    "eau":      ( 60, 140, 230),
    "plante":   ( 70, 190,  80),
    "electrik": (230, 210,  50),
    "psy":      (210,  80, 180),
    "combat":   (190,  80,  50),
    "poison":   (160,  60, 200),
    "vol":      (100, 160, 230),
    "roche":    (170, 150,  80),
    "sol":      (200, 160,  80),
    "glace":    (130, 210, 230),
    "spectre":  ( 90,  60, 160),
    "dragon":   ( 80,  60, 230),
    "normal":   (160, 160, 160),
    "tenebres": ( 80,  60,  60),
    "acier":    (160, 170, 190),
}


class StateCheat(State):

    transparent = True

    def __init__(self, game_manager):
        super().__init__(game_manager)

        self.player = game_manager.player

        self.f_title  = font(28)
        self.f_sub    = font(18)
        self.f_entry  = pygame.font.Font(None, 22)
        self.f_detail = pygame.font.Font(None, 20)
        self.f_type   = pygame.font.Font(None, 18)
        self.f_hint   = pygame.font.Font(None, 18)

        self.pokemon_data    = game_manager.pokemon_catalog
        self.all_ids         = self.pokemon_data.get_all_ids()
        self.selection_index = 0
        self.scroll_offset   = 0
        self._sprite_cache   = {}

        self._flash_msg   = None
        self._flash_timer = 0.0

    # -------------------------------------------------------------------------
    def _get_sprite(self, pokemon_id, size=192):
        key = (pokemon_id, size)
        if key not in self._sprite_cache:
            path = POKEMON_SPRITES_DIR / f"{pokemon_id}_front.png"
            try:
                raw = pygame.image.load(str(path)).convert_alpha()
                self._sprite_cache[key] = pygame.transform.scale(raw, (size, size))
            except Exception:
                self._sprite_cache[key] = None
        return self._sprite_cache[key]

    def on_enter(self):
        pass

    # -------------------------------------------------------------------------
    def handle_events(self, events):
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                self.game_manager.state_manager.pop()
                return

            if event.key == pygame.K_UP:
                self._navigate(-1)
            elif event.key == pygame.K_DOWN:
                self._navigate(1)

            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._toggle_selected()

            elif event.key == pygame.K_a:
                self._capture_all()

            elif event.key == pygame.K_z:
                self._clear_all()

    def _navigate(self, d):
        old = self.selection_index
        self.selection_index = max(0, min(len(self.all_ids) - 1,
                                         self.selection_index + d))
        if self.selection_index != old:
            self.game_manager.audio_manager.play_sfx("menu_select")
        if self.selection_index < self.scroll_offset:
            self.scroll_offset = self.selection_index
        if self.selection_index >= self.scroll_offset + VISIBLE_LINES:
            self.scroll_offset = self.selection_index - VISIBLE_LINES + 1

    def _toggle_selected(self):
        pid     = self.all_ids[self.selection_index]
        pokedex = self.player.pokedex
        if pokedex.is_captured(pid):
            # Déjà capturé → retirer complètement
            pokedex.seen.discard(pid)
            pokedex.captured.discard(pid)
            self._flash("Retiré du Pokédex", C_GRAY)
        else:
            # Pas encore capturé → ajouter comme vu ET capturé
            pokedex.register_captured(pid)
            info = self.pokemon_data.get_info(pid)
            name = info.get("name_custom", f"#{pid:03d}")
            self._flash(f"{name} ajouté !", C_GREEN)
        self.game_manager.audio_manager.play_sfx("levelup")

    def _capture_all(self):
        for pid in self.all_ids:
            self.player.pokedex.register_captured(pid)
        self._flash(f"Tous les Pokémon ajoutés !", C_ORANGE)
        self.game_manager.audio_manager.play_sfx("levelup")

    def _clear_all(self):
        self.player.pokedex.reset()
        self._flash("Pokédex effacé.", C_GRAY)

    def _flash(self, msg, color=None):
        self._flash_msg   = msg
        self._flash_color = color or C_WHITE
        self._flash_timer = 2.0

    # -------------------------------------------------------------------------
    def update(self, dt):
        if self._flash_timer > 0:
            self._flash_timer -= dt
            if self._flash_timer <= 0:
                self._flash_msg = None

    # =========================================================================
    # RENDER
    # =========================================================================
    def render(self, screen):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 155))
        screen.blit(ov, (0, 0))

        px, py = 40, 24
        pw, ph = SCREEN_WIDTH - 80, SCREEN_HEIGHT - 48

        panel(screen, px, py, pw, ph, border=C_RED)
        corner_accents(screen, px, py, pw, ph, color=C_RED)

        cx = px + pw // 2

        # Titre
        text_c(screen, self.f_title, "⚠ MODE TRICHE ⚠", C_RED, cx, py + 12, shadow=True)

        # Compteurs
        pokedex = self.player.pokedex
        total   = TOTAL_POKEMON
        cap_s = self.f_type.render(
            f"Capturés : {pokedex.get_total_captured()}/{total}", True, C_ORANGE)
        screen.blit(cap_s, (px + pw - 200, py + 18))

        sep_y = py + 64
        pygame.draw.line(screen, C_RED,
                         (px + 16, sep_y), (px + pw - 16, sep_y), 1)

        self._draw_list(screen, px, py, sep_y)
        self._draw_detail(screen, px, pw, sep_y)

        # Hint bas
        hint = self.f_hint.render(
            "[↑↓] Naviguer   [ENTRÉE] Ajouter/Retirer   [A] Tout capturer   [Z] Tout effacer   [ECHAP] Fermer",
            True, C_GRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, py + ph - 22))

        # Message flash
        if self._flash_msg:
            self._draw_flash(screen)

    # -------------------------------------------------------------------------
    def _draw_list(self, screen, px, py, sep_y):
        pokedex = self.player.pokedex
        lx = px + 12
        ly = sep_y + 8
        lh = 28

        for i in range(VISIBLE_LINES):
            idx = self.scroll_offset + i
            if idx >= len(self.all_ids):
                break
            pid    = self.all_ids[idx]
            y      = ly + i * lh
            is_cap = pokedex.is_captured(pid)
            is_seen = pokedex.is_seen(pid)
            is_sel = (idx == self.selection_index)

            if is_sel:
                hl = pygame.Surface((LIST_W, lh - 2), pygame.SRCALPHA)
                hl.fill((*C_RED, 35))
                screen.blit(hl, (lx, y))
                pygame.draw.rect(screen, C_RED, (lx, y, LIST_W, lh - 2), 1)

            # Numéro
            num_s = self.f_entry.render(f"#{pid:03d}", True,
                                        C_ORANGE if is_sel else C_WHITE)
            screen.blit(num_s, (lx + 4, y + 4))

            # Icône statut
            if is_cap:
                icon, ic = "●", C_GREEN
            elif is_seen:
                icon, ic = "○", C_BLUE
            else:
                icon, ic = "·", (55, 60, 85)
            ic_s = self.f_entry.render(icon, True, ic)
            screen.blit(ic_s, (lx + 60, y + 4))

            # Nom (toujours visible en mode triche)
            info  = self.pokemon_data.get_info(pid)
            name  = info["name_custom"]
            col   = C_GREEN if is_cap else (C_BLUE if is_seen else C_GRAY)
            name_s = self.f_entry.render(name, True, col)
            blit_clipped(screen, name_s, lx + 80, y + 4, LIST_W - 84)

        # Flèches scroll
        if self.scroll_offset > 0:
            a = self.f_hint.render("▲", True, C_GRAY)
            screen.blit(a, (lx + LIST_W // 2 - a.get_width() // 2, ly - 14))
        if self.scroll_offset + VISIBLE_LINES < len(self.all_ids):
            a = self.f_hint.render("▼", True, C_GRAY)
            screen.blit(a, (lx + LIST_W // 2 - a.get_width() // 2,
                            ly + VISIBLE_LINES * lh + 2))

        # Séparateur vertical
        pygame.draw.line(screen, (80, 30, 30),
                         (px + LIST_W + 16, sep_y + 2),
                         (px + LIST_W + 16, sep_y + VISIBLE_LINES * lh + 16), 1)

    # -------------------------------------------------------------------------
    def _draw_detail(self, screen, px, pw, sep_y):
        pokedex    = self.player.pokedex
        pid        = self.all_ids[self.selection_index]
        info       = self.pokemon_data.get_info(pid)
        is_cap     = pokedex.is_captured(pid)
        is_seen    = pokedex.is_seen(pid)

        dx = px + LIST_W + 28
        dw = pw - LIST_W - 44
        dy = sep_y + 8

        # Sprite (toujours visible)
        BOX = 192
        box_bg = pygame.Surface((BOX, BOX), pygame.SRCALPHA)
        box_bg.fill((40, 10, 10, 200))
        screen.blit(box_bg, (dx, dy))
        pygame.draw.rect(screen, C_RED, (dx, dy, BOX, BOX), 2)

        sprite = self._get_sprite(pid, BOX)
        if sprite:
            screen.blit(sprite, (dx, dy))

        # Infos à droite du sprite
        ix = dx + BOX + 14
        iw = dx + dw - ix - 6

        name_s = self.f_sub.render(f"#{pid:03d}  {info['name_custom']}", True, C_ORANGE)
        blit_clipped(screen, name_s, ix, dy + 4, iw)

        # Statut actuel
        if is_cap:
            status_txt = "● Capturé"
            status_col = C_GREEN
        elif is_seen:
            status_txt = "○ Vu uniquement"
            status_col = C_BLUE
        else:
            status_txt = "· Non enregistré"
            status_col = C_GRAY
        screen.blit(self.f_detail.render(status_txt, True, status_col), (ix, dy + 30))

        # Action dispo
        if is_cap:
            action_txt = "[ENTRÉE] Retirer du Pokédex"
            action_col = (200, 80, 80)
        else:
            action_txt = "[ENTRÉE] Ajouter comme capturé"
            action_col = C_GREEN
        screen.blit(self.f_detail.render(action_txt, True, action_col), (ix, dy + 52))

        # Types
        tx = ix
        for t in info.get("types", []):
            tc  = TYPE_COLORS.get(t.lower(), (120, 120, 140))
            t_s = self.f_type.render(t.upper(), True, (10, 10, 10))
            bw  = t_s.get_width() + 12
            bh  = t_s.get_height() + 6
            bdg = pygame.Surface((bw, bh), pygame.SRCALPHA)
            bdg.fill((*tc, 220))
            screen.blit(bdg, (tx, dy + 78))
            screen.blit(t_s,  (tx + 6, dy + 81))
            tx += bw + 6

        # Stats rapides
        stats = info.get("base_stats", {})
        sy = dy + 110
        for lbl, key, col in [
            ("PV",  "hp",      (100, 210, 100)),
            ("ATQ", "attack",  (220, 100,  80)),
            ("DEF", "defense", ( 80, 140, 220)),
        ]:
            val = stats.get(key, "?")
            screen.blit(self.f_type.render(f"{lbl}: {val}", True, col), (ix, sy))
            sy += 20

    # -------------------------------------------------------------------------
    def _draw_flash(self, screen):
        surf = self.f_detail.render(self._flash_msg, True, self._flash_color)
        pad  = 14
        bw   = surf.get_width() + pad * 2
        bh   = surf.get_height() + pad
        bg   = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 210))
        pygame.draw.rect(bg, self._flash_color, (0, 0, bw, bh), 1)
        x = (SCREEN_WIDTH - bw) // 2
        y = SCREEN_HEIGHT // 2 + 100
        screen.blit(bg,   (x, y))
        screen.blit(surf, (x + pad, y + pad // 2))
