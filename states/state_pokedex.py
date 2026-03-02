# =============================================================================
# STATE_POKEDEX.PY - POKEDEX STATE
# =============================================================================

import pygame
from states.state import State
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TOTAL_POKEMON, POKEMON_SPRITES_DIR
from ui.poke_style import (
    C_GOLD, C_GOLD_DIM, C_WHITE, C_GRAY, C_GREEN, C_BLUE,
    font, panel, corner_accents, text_c, blit_clipped,
)

# Type colour map
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

VISIBLE_LINES = 11
LIST_W        = 340   # left panel width


class StatePokedex(State):

    transparent = True

    # -------------------------------------------------------------------------
    def __init__(self, game_manager):
        super().__init__(game_manager)

        self.player = game_manager.player

        self.f_title   = font(30)
        self.f_sub     = font(18)
        self.f_entry   = pygame.font.Font(None, 22)
        self.f_detail  = pygame.font.Font(None, 20)
        self.f_type    = pygame.font.Font(None, 18)
        self.f_hint    = pygame.font.Font(None, 18)

        self.pokemon_data    = game_manager.pokemon_catalog
        self.all_ids         = self.pokemon_data.get_all_ids()
        self.selection_index = 0
        self.scroll_offset   = 0
        self._sprite_cache   = {}   # pokemon_id → scaled Surface | None
        self._feedback       = ""
        self._feedback_timer = 0.0

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

    # -------------------------------------------------------------------------
    def on_enter(self):
        pass

    def handle_events(self, events):
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                self.game_manager.state_manager.pop(); return
            if event.key == pygame.K_UP:
                self._navigate(-1)
            elif event.key == pygame.K_DOWN:
                self._navigate(1)
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._toggle_team()

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

    def _toggle_team(self):
        """Add or remove selected Pokémon from active team."""
        pokemon_id = self.all_ids[self.selection_index]
        if not self.player.pokedex.is_captured(pokemon_id):
            return

        team    = self.player.team
        storage = self.player.storage

        # If it's in the team → move back to storage
        for i, pk in enumerate(team.get_all()):
            if pk.id == pokemon_id:
                removed = team.remove(i)
                if removed:
                    storage.add(removed)
                    self._set_feedback(f"{removed.name} retiré de l'équipe.")
                else:
                    self._set_feedback("Impossible : dernier Pokémon valide !")
                return

        # If it's in storage → move to team
        for i, pk in enumerate(storage.get_all()):
            if pk.id == pokemon_id:
                if team.is_full:
                    self._set_feedback("Équipe pleine ! (6/6)")
                    return
                storage.remove(i)
                team.add(pk)
                self._set_feedback(f"{pk.name} ajouté à l'équipe !")
                return

        # Captured in Pokédex but no instance yet → create one from catalog
        try:
            from entities.pokemon import Pokemon
            pk = Pokemon.from_data(pokemon_id, level=5)
            if team.is_full:
                storage.add(pk)
                self._set_feedback(f"{pk.name} ajouté au stockage (équipe pleine).")
            else:
                team.add(pk)
                self._set_feedback(f"{pk.name} ajouté à l'équipe !")
        except Exception:
            self._set_feedback("Erreur : données introuvables pour ce Pokémon.")

    def _set_feedback(self, msg):
        self._feedback       = msg
        self._feedback_timer = 2.5

    def update(self, dt):
        if self._feedback_timer > 0:
            self._feedback_timer = max(0.0, self._feedback_timer - dt)

    # =========================================================================
    # RENDER
    # =========================================================================
    def render(self, screen):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 145))
        screen.blit(ov, (0, 0))

        # Outer panel
        px, py = 40, 24
        pw, ph = SCREEN_WIDTH - 80, SCREEN_HEIGHT - 48

        panel(screen, px, py, pw, ph, border=C_GOLD)
        corner_accents(screen, px, py, pw, ph)

        cx = px + pw // 2

        # Title
        text_c(screen, self.f_title, "Pokedex", C_GOLD, cx, py + 12, shadow=True)

        # Counters + bar
        self._draw_header(screen, px, py, pw)

        sep_y = py + 64
        pygame.draw.line(screen, C_GOLD_DIM,
                         (px + 16, sep_y), (px + pw - 16, sep_y), 1)

        # Two-column layout
        self._draw_list(screen, px, py, sep_y)
        self._draw_detail(screen, px, pw, sep_y)

        # Feedback toast (above hint)
        if self._feedback_timer > 0:
            alpha = min(255, int(self._feedback_timer / 2.5 * 255))
            fb_s  = self.f_sub.render(self._feedback, True, C_GOLD)
            fb_x  = cx - fb_s.get_width() // 2
            fb_y  = py + ph - 46
            fb_bg = pygame.Surface((fb_s.get_width() + 20, fb_s.get_height() + 8), pygame.SRCALPHA)
            fb_bg.fill((14, 18, 48, min(220, alpha)))
            screen.blit(fb_bg, (fb_x - 10, fb_y - 4))
            fb_s.set_alpha(alpha)
            screen.blit(fb_s, (fb_x, fb_y))

        # Controls
        hint = self.f_hint.render(
            "[HAUT/BAS] Naviguer   [ENTREE] Équipe   [ECHAP] Fermer", True, C_GRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, py + ph - 22))

    # -------------------------------------------------------------------------
    def _draw_header(self, screen, px, py, pw):
        pokedex = self.player.pokedex
        total   = TOTAL_POKEMON

        seen_s = self.f_type.render(
            f"Vus : {pokedex.get_total_seen()}/{total}", True, C_BLUE)
        cap_s  = self.f_type.render(
            f"Captures : {pokedex.get_total_captured()}/{total}", True, C_GOLD)

        screen.blit(seen_s, (px + pw - 300, py + 18))
        screen.blit(cap_s,  (px + pw - 148, py + 18))

        # Capture progress bar
        bx, by = px + 16, py + 50
        bw     = pw - 32
        ratio  = pokedex.get_total_captured() / total if total else 0
        pygame.draw.rect(screen, (30, 38, 70), (bx, by, bw, 8))
        if ratio > 0:
            pygame.draw.rect(screen, C_GOLD, (bx, by, int(bw * ratio), 8))
        pygame.draw.rect(screen, C_GOLD_DIM, (bx, by, bw, 8), 1)

    # -------------------------------------------------------------------------
    def _draw_list(self, screen, px, py, sep_y):
        pokedex = self.player.pokedex
        lx      = px + 12
        ly      = sep_y + 8
        lh      = 28     # line height

        for i in range(VISIBLE_LINES):
            idx        = self.scroll_offset + i
            if idx >= len(self.all_ids):
                break
            pokemon_id = self.all_ids[idx]
            y          = ly + i * lh
            is_seen    = pokedex.is_seen(pokemon_id)
            is_cap     = pokedex.is_captured(pokemon_id)
            is_sel     = (idx == self.selection_index)

            if is_sel:
                hl = pygame.Surface((LIST_W, lh - 2), pygame.SRCALPHA)
                hl.fill((*C_GOLD, 28))
                screen.blit(hl, (lx, y))
                pygame.draw.rect(screen, C_GOLD, (lx, y, LIST_W, lh - 2), 1)

            # Number
            num_c = C_WHITE if is_seen else (60, 65, 90)
            num_s = self.f_entry.render(f"#{pokemon_id:03d}", True,
                                        C_GOLD if is_sel else num_c)
            screen.blit(num_s, (lx + 4, y + 4))

            # Status icon
            in_team = self.player.team.contains(pokemon_id)
            if in_team:
                icon, ic = "★", C_GOLD
            elif is_cap:
                icon, ic = "●", C_GREEN
            elif is_seen:
                icon, ic = "○", C_BLUE
            else:
                icon, ic = "·", (55, 60, 85)
            ic_s = self.f_entry.render(icon, True, ic)
            screen.blit(ic_s, (lx + 60, y + 4))

            # Name
            if is_seen:
                info   = self.pokemon_data.get_info(pokemon_id)
                name   = info["name_custom"]
                name_c = C_WHITE
            else:
                name, name_c = "?????????", (55, 60, 85)

            name_s = self.f_entry.render(name, True, name_c)
            blit_clipped(screen, name_s, lx + 80, y + 4, LIST_W - 84)

        # Scroll arrows
        if self.scroll_offset > 0:
            a = self.f_hint.render("▲", True, C_GRAY)
            screen.blit(a, (lx + LIST_W // 2 - a.get_width() // 2, ly - 14))
        if self.scroll_offset + VISIBLE_LINES < len(self.all_ids):
            a = self.f_hint.render("▼", True, C_GRAY)
            screen.blit(a, (lx + LIST_W // 2 - a.get_width() // 2,
                            ly + VISIBLE_LINES * lh + 2))

        # Vertical separator
        pygame.draw.line(screen, C_GOLD_DIM,
                         (px + LIST_W + 16, sep_y + 2),
                         (px + LIST_W + 16, sep_y + VISIBLE_LINES * lh + 16), 1)

    # -------------------------------------------------------------------------
    def _draw_detail(self, screen, px, pw, sep_y):
        pokedex    = self.player.pokedex
        pokemon_id = self.all_ids[self.selection_index]

        dx = px + LIST_W + 28   # 408
        dw = pw - LIST_W - 44   # 560
        dy = sep_y + 8

        if not pokedex.is_seen(pokemon_id):
            BOX = 208
            sil = pygame.Surface((BOX, BOX), pygame.SRCALPHA)
            sil.fill((15, 20, 50, 160))
            screen.blit(sil, (dx + 4, dy + 4))
            pygame.draw.rect(screen, (55, 65, 108), (dx + 4, dy + 4, BOX, BOX), 1)
            msg = self.f_detail.render(
                f"#{pokemon_id:03d} — Pas encore rencontre", True, (70, 75, 105))
            screen.blit(msg, (dx + BOX + 20, dy + 24))
            return

        info   = self.pokemon_data.get_info(pokemon_id)
        is_cap = pokedex.is_captured(pokemon_id)

        # ================================================================
        # BLOC 1 — Grand sprite (gauche) + infos (droite)
        # ================================================================
        BOX   = 208   # boîte extérieure
        SPR   = 192   # sprite à l'intérieur (96×2)
        box_x = dx + 4
        box_y = dy + 4

        box_bg = pygame.Surface((BOX, BOX), pygame.SRCALPHA)
        box_bg.fill((20, 28, 64, 215))
        screen.blit(box_bg, (box_x, box_y))
        pygame.draw.rect(screen, C_GOLD, (box_x, box_y, BOX, BOX), 2)
        for ax, ddx in ((box_x, 1), (box_x + BOX, -1)):
            for ay, ddy in ((box_y, 1), (box_y + BOX, -1)):
                pygame.draw.line(screen, C_GOLD, (ax, ay), (ax + ddx*10, ay), 2)
                pygame.draw.line(screen, C_GOLD, (ax, ay), (ax, ay + ddy*10), 2)

        sprite = self._get_sprite(pokemon_id, SPR)
        if sprite:
            screen.blit(sprite, (box_x + (BOX - SPR) // 2,
                                 box_y + (BOX - SPR) // 2))

        # Colonne droite : dx+226 → dx+dw-8 ≈ 326px de large
        ix = box_x + BOX + 14
        iw = dx + dw - ix - 6

        name_s = self.f_sub.render(
            f"#{pokemon_id:03d}  {info['name_custom']}", True, C_GOLD)
        blit_clipped(screen, name_s, ix, dy + 4, iw)

        cap_lbl = "★ Capture" if is_cap else "○ Vu uniquement"
        cap_col = C_GOLD if is_cap else C_BLUE
        screen.blit(self.f_detail.render(cap_lbl, True, cap_col), (ix, dy + 30))

        # Type badges
        tx = ix
        for t in info.get("types", []):
            tc  = TYPE_COLORS.get(t.lower(), (120, 120, 140))
            t_s = self.f_type.render(t.upper(), True, (10, 10, 10))
            bw  = t_s.get_width() + 12
            bh  = t_s.get_height() + 6
            bdg = pygame.Surface((bw, bh), pygame.SRCALPHA)
            bdg.fill((*tc, 220))
            screen.blit(bdg, (tx, dy + 56))
            screen.blit(t_s,  (tx + 6, dy + 59))
            tx += bw + 6

        pygame.draw.line(screen, (35, 42, 72),
                         (ix, dy + 80), (ix + iw, dy + 80), 1)

        # Diurne/Nocturne
        dn     = info.get("day_night", "diurne")
        dn_txt = "Diurne" if dn == "diurne" else "Nocturne"
        dn_col = (240, 210, 80) if dn == "diurne" else (140, 140, 240)
        screen.blit(self.f_detail.render(dn_txt, True, dn_col), (ix, dy + 88))

        # Stade
        screen.blit(
            self.f_detail.render(
                f"Stade {info.get('evolution_stage', info.get('stade', 1))}",
                True, C_GRAY),
            (ix, dy + 110))

        # Capacites (4 max)
        screen.blit(self.f_type.render("Capacites :", True, C_GRAY), (ix, dy + 136))
        for k, atk in enumerate(info.get("all_attacks", [])[:4]):
            atc = TYPE_COLORS.get(atk.get("type", "normal").lower(), (120, 120, 140))
            a_s = self.f_type.render(
                f"• {atk['name']}", True, tuple(min(255, c + 60) for c in atc))
            blit_clipped(screen, a_s, ix, dy + 154 + k * 16, iw)

        # ================================================================
        # BLOC 2 — Statistiques (pleine largeur)
        # ================================================================
        sep1 = dy + BOX + 8   # dy + 216
        pygame.draw.line(screen, C_GOLD_DIM, (dx, sep1), (dx + dw, sep1), 1)

        lbl_st = self.f_type.render("STATISTIQUES DE BASE", True, C_GOLD_DIM)
        screen.blit(lbl_st, (dx, sep1 + 8))

        stats     = info.get("base_stats", {})
        stat_rows = [
            ("PV",  stats.get("hp",      "?"), (100, 210, 100)),
            ("ATQ", stats.get("attack",  "?"), (220, 100,  80)),
            ("DEF", stats.get("defense", "?"), ( 80, 140, 220)),
        ]
        for si, (lbl, val, col) in enumerate(stat_rows):
            ry = sep1 + 30 + si * 34
            screen.blit(self.f_detail.render(lbl,      True, C_GRAY), (dx,      ry))
            screen.blit(self.f_detail.render(str(val), True, col),    (dx + 48, ry))
            try:
                ratio = min(int(val) / 150, 1.0)
            except Exception:
                ratio = 0.0
            bar_x = dx + 90
            bar_w = dw - 94
            pygame.draw.rect(screen, (30, 38, 70), (bar_x, ry + 2, bar_w, 16))
            if ratio > 0:
                pygame.draw.rect(screen, col, (bar_x, ry + 2, int(bar_w * ratio), 16))
            pygame.draw.rect(screen, (40, 50, 90), (bar_x, ry + 2, bar_w, 16), 1)

        # ================================================================
        # BLOC 3 — Evolution (pleine largeur, centré)
        # ================================================================
        sep2 = sep1 + 30 + len(stat_rows) * 34 + 8
        pygame.draw.line(screen, C_GOLD_DIM, (dx, sep2), (dx + dw, sep2), 1)

        lbl_ev = self.f_type.render("EVOLUTION", True, C_GOLD_DIM)
        screen.blit(lbl_ev, (dx, sep2 + 8))

        evo_y  = sep2 + 30
        evo    = info.get("evolution")
        SZ     = 84    # boîte sprite
        SPR_EV = 80    # sprite à l'intérieur
        GAP    = 100   # espace entre les deux boîtes (flèche + niveau)

        def _draw_evo_box(bx, by, pid, seen, border_col):
            """Boîte de sprite pour l'évolution."""
            bg = pygame.Surface((SZ, SZ), pygame.SRCALPHA)
            bg.fill((20, 28, 64, 200))
            screen.blit(bg, (bx, by))
            pygame.draw.rect(screen, border_col, (bx, by, SZ, SZ), 2)
            # Corner accents
            for ax2, dx2 in ((bx, 1), (bx + SZ, -1)):
                for ay2, dy2 in ((by, 1), (by + SZ, -1)):
                    pygame.draw.line(screen, border_col, (ax2, ay2), (ax2 + dx2*6, ay2), 1)
                    pygame.draw.line(screen, border_col, (ax2, ay2), (ax2, ay2 + dy2*6), 1)
            if seen:
                spr = self._get_sprite(pid, SPR_EV)
                if spr:
                    screen.blit(spr, (bx + (SZ - SPR_EV) // 2, by + (SZ - SPR_EV) // 2))
            else:
                q = self.f_sub.render("?", True, (60, 65, 90))
                screen.blit(q, (bx + (SZ - q.get_width()) // 2,
                                by + (SZ - q.get_height()) // 2))

        if evo and evo.get("to"):
            # Layout centré : [BoxA] ──Niv.X──→ [BoxB]
            total_w = SZ + GAP + SZ
            start_x = dx + (dw - total_w) // 2

            ax = start_x
            bx = start_x + SZ + GAP

            # Boîte A — Pokémon courant
            _draw_evo_box(ax, evo_y, pokemon_id, True, C_GOLD)
            cur_n = self.f_type.render(info["name_custom"], True, C_WHITE)
            screen.blit(cur_n, (ax + (SZ - cur_n.get_width()) // 2, evo_y + SZ + 6))

            # Flèche et niveau dans la zone centrale
            gap_cx  = start_x + SZ + GAP // 2
            arr     = self.f_sub.render("→", True, C_GOLD)
            lv_s    = self.f_type.render(f"Niv. {evo.get('level', '?')}", True, C_GRAY)
            screen.blit(arr,  (gap_cx - arr.get_width()  // 2, evo_y + SZ // 2 - arr.get_height() // 2 - 6))
            screen.blit(lv_s, (gap_cx - lv_s.get_width() // 2, evo_y + SZ // 2 + 6))

            # Boîte B — Pokémon évolué
            evo_id   = evo["to"]
            evo_info = self.pokemon_data.get_info(evo_id)
            evo_seen = pokedex.is_seen(evo_id)
            _draw_evo_box(bx, evo_y, evo_id, evo_seen,
                          C_GOLD_DIM if evo_seen else (55, 65, 108))
            ev_name = evo_info["name_custom"] if evo_seen else "???"
            en_s = self.f_type.render(ev_name, True, C_WHITE if evo_seen else C_GRAY)
            screen.blit(en_s, (bx + (SZ - en_s.get_width()) // 2, evo_y + SZ + 6))

        else:
            # Forme finale — sprite centré seul
            cx_evo = dx + (dw - SZ) // 2
            _draw_evo_box(cx_evo, evo_y, pokemon_id, True, C_GOLD)
            cur_n = self.f_type.render(info["name_custom"], True, C_WHITE)
            screen.blit(cur_n, (cx_evo + (SZ - cur_n.get_width()) // 2, evo_y + SZ + 6))
            fin_s = self.f_detail.render("Forme finale", True, C_GRAY)
            screen.blit(fin_s, (dx + (dw - fin_s.get_width()) // 2, evo_y + SZ + 26))
