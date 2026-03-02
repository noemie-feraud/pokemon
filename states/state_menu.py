# =============================================================================
# STATE_MENU.PY - MENU PRINCIPAL
# =============================================================================

import pygame
from states.state import State
from entities.player import Player
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_SPRITES_DIR
from ui.poke_style import (
    C_GOLD, C_WHITE, C_GRAY, C_BLACK, C_PANEL,
    font, make_gradient_bg, panel, corner_accents, text_c,
    blit_clipped, wrap, fit_and_crop,
)

MODE_PRINCIPAL      = "principal"
MODE_CHOIX_DRESSEUR = "choix_dresseur"
MODE_CHOIX_SLOT     = "choix_slot"


class StateMenu(State):

    # -------------------------------------------------------------------------
    def __init__(self, game_manager):
        super().__init__(game_manager)

        self.f_title = font(46)
        self.f_sub   = font(24)
        self.f_opt   = font(20)
        self.f_desc  = pygame.font.Font(None, 20)
        self.f_info  = pygame.font.Font(None, 18)
        self.f_hint  = pygame.font.Font(None, 18)

        self.mode = MODE_PRINCIPAL
        self.idx  = 0

        self.options = ["Nouvelle Partie", "Continuer", "Quitter"]

        self.infos_slots = None
        self.continuer_ok = False
        self._load_slots()

        self.personnages = [
            {"id": 1, "nom": "Linus",
             "description": "Un codeur decontracte, toujours un cafe a la main",
             "color": (50, 110, 200)},
            {"id": 2, "nom": "Ada",
             "description": "Une analyste brillante, carnet toujours en main",
             "color": (150, 55, 200)},
        ]

        self._raw_sprites = self._load_raw_sprites()
        self._bg = make_gradient_bg(SCREEN_WIDTH, SCREEN_HEIGHT)

    # -------------------------------------------------------------------------
    def _load_raw_sprites(self):
        out = {}
        names = {1: "linus", 2: "ada"}
        for cid, name in names.items():
            path = PLAYER_SPRITES_DIR / f"{name}_menu.png"
            try:
                out[cid] = pygame.image.load(str(path)).convert_alpha()
            except Exception:
                out[cid] = None
        return out

    def _load_slots(self):
        try:
            from core.save_manager import SaveManager
            self.infos_slots = SaveManager().get_all_slots_info()
            self.continuer_ok = any(
                s and s.get("occupied") for s in self.infos_slots
            )
        except Exception:
            self.infos_slots = [None, None, None]
            self.continuer_ok = False

    # -------------------------------------------------------------------------
    def on_enter(self):
        self.game_manager.audio_manager.play_music("menu")

    # -------------------------------------------------------------------------
    def handle_events(self, events):
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if   self.mode == MODE_PRINCIPAL:      self._ev_principal(event)
            elif self.mode == MODE_CHOIX_DRESSEUR: self._ev_dresseur(event)
            elif self.mode == MODE_CHOIX_SLOT:     self._ev_slot(event)

    def _ev_principal(self, event):
        if event.key == pygame.K_UP:
            self.idx = max(0, self.idx - 1)
            self.game_manager.audio_manager.play_sfx("menu_select")
        elif event.key == pygame.K_DOWN:
            self.idx = min(2, self.idx + 1)
            self.game_manager.audio_manager.play_sfx("menu_select")
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
            if self.idx == 0:
                self.mode, self.idx = MODE_CHOIX_DRESSEUR, 0
            elif self.idx == 1 and self.continuer_ok:
                self.mode, self.idx = MODE_CHOIX_SLOT, 0
            elif self.idx == 2:
                self.game_manager.running = False

    def _ev_dresseur(self, event):
        if event.key == pygame.K_LEFT:
            self.idx = 0
            self.game_manager.audio_manager.play_sfx("menu_select")
        elif event.key == pygame.K_RIGHT:
            self.idx = 1
            self.game_manager.audio_manager.play_sfx("menu_select")
        elif event.key == pygame.K_ESCAPE:
            self.mode, self.idx = MODE_PRINCIPAL, 0
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self._start_new_game(self.personnages[self.idx])

    def _ev_slot(self, event):
        if event.key == pygame.K_UP:
            self.idx = max(0, self.idx - 1)
            self.game_manager.audio_manager.play_sfx("menu_select")
        elif event.key == pygame.K_DOWN:
            self.idx = min(2, self.idx + 1)
            self.game_manager.audio_manager.play_sfx("menu_select")
        elif event.key == pygame.K_ESCAPE:
            self.mode, self.idx = MODE_PRINCIPAL, 1
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
            slot = self.infos_slots[self.idx]
            if slot and slot.get("occupied"):
                self._load_save(self.idx)

    # -------------------------------------------------------------------------
    def _start_new_game(self, perso):
        from economy.item import ItemCatalog
        from economy.inventory import Inventory
        from economy.quest import QuestManager
        catalogue = ItemCatalog()
        self.game_manager.item_catalog = catalogue
        joueur = Player(character_id=perso["id"], name=perso["nom"])
        joueur.inventory = Inventory(catalogue)
        joueur.inventory.add(4, 5)
        self.game_manager.player = joueur
        self.game_manager.quest_manager = QuestManager()
        from states.state_exploration import StateExploration
        try:
            self.game_manager.state_manager.change(StateExploration(self.game_manager))
        except Exception:
            import traceback; traceback.print_exc()

    def _load_save(self, index_slot):
        from core.save_manager import SaveManager
        from economy.item import ItemCatalog
        from economy.inventory import Inventory
        from economy.quest import QuestManager
        try:
            data = SaveManager().load(index_slot)
            if data is None:
                return
            catalogue = ItemCatalog()
            self.game_manager.item_catalog = catalogue
            joueur = Player.from_save(data)
            joueur.inventory = Inventory.from_dict(data.get("inventory", {}), catalogue)
            self.game_manager.player = joueur
            self.game_manager.current_save_slot = index_slot
            if "day_night_time" in data:
                self.game_manager.day_night_cycle.set_time(data["day_night_time"])
            self.game_manager.quest_manager = QuestManager()
            from states.state_exploration import StateExploration
            self.game_manager.state_manager.change(StateExploration(self.game_manager))
        except Exception:
            import traceback; traceback.print_exc()

    # -------------------------------------------------------------------------
    def update(self, dt):
        pass

    def render(self, screen):
        screen.blit(self._bg, (0, 0))
        if   self.mode == MODE_PRINCIPAL:      self._draw_principal(screen)
        elif self.mode == MODE_CHOIX_DRESSEUR: self._draw_dresseur(screen)
        elif self.mode == MODE_CHOIX_SLOT:     self._draw_slot(screen)

    # =========================================================================
    # MENU PRINCIPAL
    # =========================================================================
    def _draw_principal(self, screen):
        cx = SCREEN_WIDTH // 2

        # Banner
        bh = 94
        by = 105
        banner = pygame.Surface((SCREEN_WIDTH, bh), pygame.SRCALPHA)
        banner.fill((0, 0, 0, 65))
        screen.blit(banner, (0, by))
        pygame.draw.line(screen, C_GOLD, (0, by),      (SCREEN_WIDTH, by),      2)
        pygame.draw.line(screen, C_GOLD, (0, by + bh), (SCREEN_WIDTH, by + bh), 2)

        text_c(screen, self.f_title, "Pokemon",        C_GOLD,  cx, by + 6,  shadow=True)
        text_c(screen, self.f_sub,   "La Plateforme",  C_WHITE, cx, by + 56, shadow=True)

        # Panel
        pw, ph = 330, 210
        px, py = cx - pw // 2, 248
        panel(screen, px, py, pw, ph, border=C_GOLD)
        corner_accents(screen, px, py, pw, ph)

        for i, label in enumerate(self.options):
            oy       = py + 28 + i * 56
            is_sel   = (i == self.idx)
            disabled = (i == 1 and not self.continuer_ok)

            if is_sel and not disabled:
                hl = pygame.Surface((pw - 24, 44), pygame.SRCALPHA)
                hl.fill((*C_GOLD, 28))
                screen.blit(hl, (px + 12, oy - 8))
                pygame.draw.rect(screen, C_GOLD, (px + 12, oy - 8, pw - 24, 44), 1)
                arrow = self.f_opt.render(">", True, C_GOLD)
                screen.blit(arrow, (px + 20, oy))

            color = C_GRAY if disabled else (C_GOLD if is_sel else C_WHITE)
            txt = self.f_opt.render(label, True, color)
            screen.blit(txt, (px + 42, oy))

        hint = self.f_hint.render("[ENTREE] Valider   [HAUT/BAS] Naviguer", True, C_GRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, 502))

    # =========================================================================
    # CHOIX DRESSEUR  –  sprites 1920×1080 → fit_and_crop
    # =========================================================================
    def _draw_dresseur(self, screen):
        cx = SCREEN_WIDTH // 2
        text_c(screen, self.f_sub, "Choisis ton dresseur", C_GOLD, cx, 42, shadow=True)

        # Cards
        card_w, card_h = 340, 470
        gap    = 44
        sx     = cx - (card_w * 2 + gap) // 2
        card_y = (SCREEN_HEIGHT - card_h) // 2 + 14

        hdr_h      = 50   # colored header with name
        footer_h   = 70   # description + tag
        sprite_h   = card_h - hdr_h - footer_h   # ≈ 350 px

        for i, perso in enumerate(self.personnages):
            cx_c   = sx + i * (card_w + gap)
            is_sel = (i == self.idx)
            border = C_GOLD if is_sel else (55, 65, 108)
            bw     = 3 if is_sel else 1

            # Card background
            bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            bg.fill((*C_PANEL, 230 if is_sel else 165))
            screen.blit(bg, (cx_c, card_y))
            pygame.draw.rect(screen, border, (cx_c, card_y, card_w, card_h), bw)
            if is_sel:
                corner_accents(screen, cx_c, card_y, card_w, card_h, size=12)

            # Colored header
            hdr = pygame.Surface((card_w - bw * 2, hdr_h), pygame.SRCALPHA)
            hdr.fill((*perso["color"], 215 if is_sel else 130))
            screen.blit(hdr, (cx_c + bw, card_y + bw))

            name_s = self.f_opt.render(perso["nom"], True, C_WHITE)
            screen.blit(name_s, (
                cx_c + (card_w - name_s.get_width()) // 2,
                card_y + (hdr_h - name_s.get_height()) // 2,
            ))

            # Sprite — scale to fill sprite_h, center-crop to card_w
            raw = self._raw_sprites.get(perso["id"])
            cropped = fit_and_crop(raw, card_w - 4, sprite_h)
            if cropped:
                screen.blit(cropped, (cx_c + 2, card_y + hdr_h))
            else:
                ph_r = pygame.Rect(cx_c + 40, card_y + hdr_h + 20,
                                   card_w - 80, sprite_h - 40)
                pygame.draw.rect(screen, perso["color"], ph_r)

            # Separator
            sep_y = card_y + hdr_h + sprite_h + 6
            pygame.draw.line(screen, border,
                             (cx_c + 10, sep_y), (cx_c + card_w - 10, sep_y), 1)

            # Description (wrapped, 2 lines max)
            max_dw = card_w - 20
            lines = wrap(self.f_desc, perso["description"], max_dw)
            for j, line in enumerate(lines[:2]):
                dl = self.f_desc.render(line, True, C_WHITE if is_sel else C_GRAY)
                blit_clipped(screen, dl, cx_c + 10, sep_y + 8 + j * 19, max_dw)

            # Selection tag
            if is_sel:
                tag = self.f_hint.render("[ SELECTIONNE ]", True, C_GOLD)
                screen.blit(tag, (
                    cx_c + (card_w - tag.get_width()) // 2,
                    card_y + card_h - 18,
                ))

        hint = self.f_hint.render(
            "[< >] Choisir    [ENTREE] Valider    [ECHAP] Retour", True, C_GRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 26))

    # =========================================================================
    # CHOIX SLOT
    # =========================================================================
    def _draw_slot(self, screen):
        cx = SCREEN_WIDTH // 2
        text_c(screen, self.f_sub, "Choisir une sauvegarde", C_GOLD, cx, 52, shadow=True)

        sw, sh = 620, 100
        sx = cx - sw // 2

        for i in range(3):
            slot     = self.infos_slots[i] if self.infos_slots else None
            occupied = slot and slot.get("occupied")
            is_sel   = (i == self.idx)
            sy       = 136 + i * (sh + 20)
            border   = C_GOLD if is_sel else (55, 65, 108)

            panel(screen, sx, sy, sw, sh, border=border, alpha=210 if is_sel else 155)
            if is_sel:
                corner_accents(screen, sx, sy, sw, sh, size=10)

            # Number badge
            bw = 40
            badge = pygame.Surface((bw, sh), pygame.SRCALPHA)
            badge.fill((*( C_GOLD if is_sel else (45, 55, 95) ), 200))
            screen.blit(badge, (sx, sy))
            num = self.f_opt.render(str(i + 1), True, C_BLACK if is_sel else C_WHITE)
            screen.blit(num, (
                sx + (bw - num.get_width()) // 2,
                sy + (sh - num.get_height()) // 2,
            ))

            cx_c   = sx + bw + 12
            max_w  = sw - bw - 20

            if occupied:
                name_s = self.f_opt.render(
                    slot.get("trainer_name", "???"), True,
                    C_GOLD if is_sel else C_WHITE)
                blit_clipped(screen, name_s, cx_c, sy + 10, max_w)

                details = (f"Zone: {slot.get('zone','?')}   "
                           f"Pokemon: {slot.get('team_size','?')}   "
                           f"Temps: {slot.get('play_time_formatted','?')}")
                det_s = self.f_info.render(details, True, C_WHITE if is_sel else C_GRAY)
                blit_clipped(screen, det_s, cx_c, sy + 42, max_w)

                lvl_s = self.f_info.render(
                    f"Niveau max : {slot.get('max_level','?')}", True,
                    (140, 215, 140) if is_sel else C_GRAY)
                blit_clipped(screen, lvl_s, cx_c, sy + 64, max_w)
            else:
                empty = self.f_opt.render("Vide", True, C_GRAY)
                screen.blit(empty, (cx_c, sy + (sh - empty.get_height()) // 2))

        hint = self.f_hint.render(
            "[HAUT/BAS] Naviguer    [ENTREE] Charger    [ECHAP] Retour", True, C_GRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 26))
