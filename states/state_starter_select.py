# =============================================================================
# STATE_STARTER_SELECT.PY - STARTER SELECTION STATE
# =============================================================================

import pygame
from states.state import State
from entities.pokemon import Pokemon
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, POKEMON_SPRITES_DIR
from ui.poke_style import (
    C_GOLD, C_WHITE, C_GRAY, C_PANEL,
    font, make_gradient_bg, panel, corner_accents, text_c, blit_clipped,
)

MODE_CHOICE       = "choice"
MODE_CONFIRMATION = "confirmation"
STARTER_LEVEL     = 5
STARTER_IDS       = [1, 4, 7]

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

# Accent color per starter (Bulbasaur, Charmander, Squirtle)
STARTER_ACCENT = {
    1: ( 70, 190,  80),   # green
    4: (230,  80,  50),   # red
    7: ( 60, 140, 230),   # blue
}

CARD_W    = 272
CARD_H    = 410
CARD_GAP  = 30
SPRITE_SZ = 148   # pixels after upscale (nearest-neighbor)
HDR_H     = 48    # name header height


class StateStarterSelect(State):

    transparent = False

    # -------------------------------------------------------------------------
    def __init__(self, game_manager, npc_professor=None):
        super().__init__(game_manager)

        self.npc_professor = npc_professor

        self.f_title   = font(28)
        self.f_name    = font(18)
        self.f_stat    = pygame.font.Font(None, 20)
        self.f_type    = pygame.font.Font(None, 18)
        self.f_atk     = pygame.font.Font(None, 18)
        self.f_hint    = pygame.font.Font(None, 18)
        self.f_confirm = font(22)

        self.starters        = [Pokemon.from_data(pid, STARTER_LEVEL) for pid in STARTER_IDS]
        self.selection_index = 0
        self.mode            = MODE_CHOICE
        self.confirm_index   = 0

        self._bg      = make_gradient_bg(SCREEN_WIDTH, SCREEN_HEIGHT)
        self._sprites = self._load_sprites()

    # -------------------------------------------------------------------------
    def _load_sprites(self):
        out = {}
        for pid in STARTER_IDS:
            path = POKEMON_SPRITES_DIR / f"{pid}_front.png"
            try:
                raw     = pygame.image.load(str(path)).convert_alpha()
                scaled  = pygame.transform.scale(raw, (SPRITE_SZ, SPRITE_SZ))
                out[pid] = scaled
            except Exception:
                out[pid] = None
        return out

    # -------------------------------------------------------------------------
    def on_enter(self):
        self.game_manager.audio_manager.play_music("menu")

    # -------------------------------------------------------------------------
    def handle_events(self, events):
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if self.mode == MODE_CHOICE:
                self._handle_choice(event)
            else:
                self._handle_confirmation(event)

    def _handle_choice(self, event):
        if event.key == pygame.K_LEFT:
            old = self.selection_index
            self.selection_index = max(0, self.selection_index - 1)
            if self.selection_index != old:
                self.game_manager.audio_manager.play_sfx("menu_select")
        elif event.key == pygame.K_RIGHT:
            old = self.selection_index
            self.selection_index = min(2, self.selection_index + 1)
            if self.selection_index != old:
                self.game_manager.audio_manager.play_sfx("menu_select")
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.mode          = MODE_CONFIRMATION
            self.confirm_index = 0

    def _handle_confirmation(self, event):
        if event.key == pygame.K_LEFT:
            self.confirm_index = 0
        elif event.key == pygame.K_RIGHT:
            self.confirm_index = 1
        elif event.key == pygame.K_ESCAPE:
            self.mode = MODE_CHOICE
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
            if self.confirm_index == 0:
                self._give_starter()
            else:
                self.mode = MODE_CHOICE

    # -------------------------------------------------------------------------
    def _give_starter(self):
        player         = self.game_manager.player
        chosen         = self.starters[self.selection_index]
        player.team.add(chosen)
        player.starter_received = True
        if self.npc_professor is not None:
            self.npc_professor.starter_given = True
        player.pokedex.register_seen(chosen.id)
        player.pokedex.register_captured(chosen.id)
        self.game_manager.audio_manager.play_sfx("levelup")
        self.game_manager.state_manager.pop()

    # -------------------------------------------------------------------------
    def update(self, dt):
        pass

    # =========================================================================
    # RENDER
    # =========================================================================
    def render(self, screen):
        screen.blit(self._bg, (0, 0))
        self._draw_title(screen)
        self._draw_cards(screen)
        if self.mode == MODE_CONFIRMATION:
            self._draw_confirmation(screen)
        self._draw_hint(screen)

    # -------------------------------------------------------------------------
    def _draw_title(self, screen):
        cx = SCREEN_WIDTH // 2

        bh = 72
        by = 18
        banner = pygame.Surface((SCREEN_WIDTH, bh), pygame.SRCALPHA)
        banner.fill((0, 0, 0, 60))
        screen.blit(banner, (0, by))
        pygame.draw.line(screen, C_GOLD, (0, by),      (SCREEN_WIDTH, by),      1)
        pygame.draw.line(screen, C_GOLD, (0, by + bh), (SCREEN_WIDTH, by + bh), 1)

        text_c(screen, self.f_title, "Choisis ton Starter !", C_GOLD, cx, by + 10, shadow=True)
        sub = self.f_hint.render(
            f"Niveau {STARTER_LEVEL}  —  Navigue avec les fleches", True, C_GRAY)
        screen.blit(sub, (cx - sub.get_width() // 2, by + 46))

    # -------------------------------------------------------------------------
    def _draw_cards(self, screen):
        total_w = 3 * CARD_W + 2 * CARD_GAP
        sx      = (SCREEN_WIDTH - total_w) // 2
        card_y  = (SCREEN_HEIGHT - CARD_H) // 2 + 22

        for i, pokemon in enumerate(self.starters):
            cx_c   = sx + i * (CARD_W + CARD_GAP)
            is_sel = (i == self.selection_index)
            accent = STARTER_ACCENT.get(pokemon.id, C_GOLD)
            border = C_GOLD if is_sel else (55, 65, 108)
            bw     = 3 if is_sel else 1

            # Card background
            bg = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            bg.fill((*C_PANEL, 235 if is_sel else 170))
            screen.blit(bg, (cx_c, card_y))
            pygame.draw.rect(screen, border, (cx_c, card_y, CARD_W, CARD_H), bw)
            if is_sel:
                corner_accents(screen, cx_c, card_y, CARD_W, CARD_H, size=12)

            # Colored header
            hdr = pygame.Surface((CARD_W - bw * 2, HDR_H), pygame.SRCALPHA)
            hdr.fill((*accent, 210 if is_sel else 130))
            screen.blit(hdr, (cx_c + bw, card_y + bw))

            name_s = self.f_name.render(pokemon.name, True, C_WHITE)
            screen.blit(name_s, (
                cx_c + (CARD_W - name_s.get_width()) // 2,
                card_y + (HDR_H - name_s.get_height()) // 2,
            ))

            # Sprite (centered, nearest-neighbor upscale)
            sprite_zone_y = card_y + HDR_H
            sprite = self._sprites.get(pokemon.id)
            if sprite:
                sx_s = cx_c + (CARD_W - SPRITE_SZ) // 2
                sy_s = sprite_zone_y + 6
                screen.blit(sprite, (sx_s, sy_s))
            else:
                ph_r = pygame.Rect(cx_c + 60, sprite_zone_y + 10, CARD_W - 120, SPRITE_SZ - 20)
                pygame.draw.rect(screen, accent, ph_r)

            # Type badges
            ty = card_y + HDR_H + SPRITE_SZ + 14
            tx = cx_c + 10
            for t in pokemon.types:
                tc  = TYPE_COLORS.get(t.lower(), (120, 120, 140))
                t_s = self.f_type.render(t.upper(), True, (10, 10, 10))
                tbw = t_s.get_width() + 12
                tbh = t_s.get_height() + 6
                badge = pygame.Surface((tbw, tbh), pygame.SRCALPHA)
                badge.fill((*tc, 220))
                screen.blit(badge, (tx, ty))
                screen.blit(t_s, (tx + 6, ty + 3))
                tx += tbw + 6

            # Separator
            sep_y = ty + 26
            pygame.draw.line(screen, (35, 42, 72),
                             (cx_c + 8, sep_y), (cx_c + CARD_W - 8, sep_y), 1)

            # Stats
            stat_rows = [
                ("PV",  pokemon.max_hp,  (100, 210, 100)),
                ("ATQ", pokemon.attack,  (220, 100,  80)),
                ("DEF", pokemon.defense, ( 80, 140, 220)),
                ("VIT", pokemon.speed,   (230, 200,  60)),
            ]
            for j, (lbl, val, col) in enumerate(stat_rows):
                ry     = sep_y + 8 + j * 20
                lbl_s  = self.f_stat.render(lbl, True, C_GRAY)
                val_s  = self.f_stat.render(str(val), True, col)
                screen.blit(lbl_s, (cx_c + 10, ry))
                screen.blit(val_s, (cx_c + 50, ry))

                bar_x = cx_c + 86
                bar_w = CARD_W - 96
                ratio = min(val / 150, 1.0)
                pygame.draw.rect(screen, (30, 38, 70), (bar_x, ry + 3, bar_w, 10))
                if ratio > 0:
                    pygame.draw.rect(screen, col, (bar_x, ry + 3, int(bar_w * ratio), 10))

            # Attacks (bottom area)
            atk_y = sep_y + 98
            pygame.draw.line(screen, (35, 42, 72),
                             (cx_c + 8, atk_y - 4), (cx_c + CARD_W - 8, atk_y - 4), 1)
            for k, atk in enumerate(pokemon.attacks[:2]):
                atk_s = self.f_atk.render(
                    f"• {atk['name']}", True,
                    C_WHITE if is_sel else (140, 150, 180))
                blit_clipped(screen, atk_s, cx_c + 10, atk_y + k * 18, CARD_W - 20)

            # Selection tag
            if is_sel:
                tag = self.f_hint.render("[ SELECTIONNE ]", True, C_GOLD)
                screen.blit(tag, (
                    cx_c + (CARD_W - tag.get_width()) // 2,
                    card_y + CARD_H - 16,
                ))

    # -------------------------------------------------------------------------
    def _draw_confirmation(self, screen):
        pokemon = self.starters[self.selection_index]

        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 145))
        screen.blit(ov, (0, 0))

        cx = SCREEN_WIDTH // 2
        fw, fh = 460, 148
        fx, fy = cx - fw // 2, (SCREEN_HEIGHT - fh) // 2

        panel(screen, fx, fy, fw, fh, border=C_GOLD)
        corner_accents(screen, fx, fy, fw, fh)

        text_c(screen, self.f_confirm,
               f"Tu choisis {pokemon.name} ?", C_WHITE, cx, fy + 18)

        accent = STARTER_ACCENT.get(pokemon.id, C_GOLD)
        sub = self.f_hint.render(
            f"Type : {' / '.join(pokemon.types).upper()}", True, accent)
        screen.blit(sub, (cx - sub.get_width() // 2, fy + 56))

        for i, lbl in enumerate(["Oui", "Non"]):
            color = C_GOLD if i == self.confirm_index else C_WHITE
            pre   = "> " if i == self.confirm_index else "  "
            s = self.f_confirm.render(pre + lbl, True, color)
            screen.blit(s, (fx + 110 + i * 170, fy + 98))

    # -------------------------------------------------------------------------
    def _draw_hint(self, screen):
        if self.mode == MODE_CHOICE:
            text = "[<  >] Choisir    [ENTREE] Confirmer"
        else:
            text = "[<  >] Oui/Non    [ENTREE] Valider    [ECHAP] Retour"
        hint = self.f_hint.render(text, True, C_GRAY)
        screen.blit(hint, (
            SCREEN_WIDTH // 2 - hint.get_width() // 2,
            SCREEN_HEIGHT - 26,
        ))
