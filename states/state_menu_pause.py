# =============================================================================
# STATE_MENU_PAUSE.PY - PAUSE MENU STATE
# =============================================================================

import pygame
from states.state import State
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from ui.poke_style import (
    C_GOLD, C_GOLD_DIM, C_WHITE, C_GRAY, C_BLACK,
    font, panel, corner_accents, text_c, blit_clipped,
)

MODE_MENU         = "menu"
MODE_SAVE         = "save"
MODE_CONFIRM_QUIT = "confirm_quit"
MODE_CONFIRM_MENU = "confirm_menu"
MESSAGE_DURATION  = 2.0


class StateMenuPause(State):

    transparent = True

    # -------------------------------------------------------------------------
    def __init__(self, game_manager):
        super().__init__(game_manager)

        self.f_title   = font(34)
        self.f_opt     = font(20)
        self.f_info    = pygame.font.Font(None, 20)
        self.f_hint    = pygame.font.Font(None, 18)
        self.f_confirm = font(22)

        self.options = [
            "Reprendre",
            "Pokedex",
            "Quetes",
            "Tricher",
            "Sauvegarder",
            "Menu principal",
            "Quitter le jeu",
        ]

        self.selection_index = 0
        self.mode            = MODE_MENU
        self.confirm_index   = 1

        self.slot_selection = 0
        self.slots_info     = None

        self.temp_message  = None
        self.message_timer = 0
        self.message_color = C_WHITE

    # -------------------------------------------------------------------------
    def on_enter(self):
        pass

    # -------------------------------------------------------------------------
    def handle_events(self, events):
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if   self.mode == MODE_MENU:         self._handle_menu(event)
            elif self.mode == MODE_SAVE:         self._handle_save(event)
            elif self.mode == MODE_CONFIRM_QUIT: self._handle_confirm(event, "quit")
            elif self.mode == MODE_CONFIRM_MENU: self._handle_confirm(event, "menu")

    def _handle_menu(self, event):
        if event.key == pygame.K_ESCAPE:
            self.game_manager.state_manager.pop(); return
        if event.key == pygame.K_UP:
            old = self.selection_index
            self.selection_index = max(0, self.selection_index - 1)
            if self.selection_index != old:
                self.game_manager.audio_manager.play_sfx("menu_select")
        elif event.key == pygame.K_DOWN:
            old = self.selection_index
            self.selection_index = min(len(self.options) - 1, self.selection_index + 1)
            if self.selection_index != old:
                self.game_manager.audio_manager.play_sfx("menu_select")
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self._execute_option()

    def _execute_option(self):
        opt = self.options[self.selection_index]
        if opt == "Reprendre":
            self.game_manager.state_manager.pop()
        elif opt == "Pokedex":
            from states.state_pokedex import StatePokedex
            self.game_manager.state_manager.push(StatePokedex(self.game_manager))
        elif opt == "Quetes":
            from states.state_quests import StateQuests
            self.game_manager.state_manager.push(StateQuests(self.game_manager))
        elif opt == "Tricher":
            from states.state_cheat import StateCheat
            self.game_manager.state_manager.push(StateCheat(self.game_manager))
        elif opt == "Sauvegarder":
            self._begin_save()
        elif opt == "Menu principal":
            self.mode = MODE_CONFIRM_MENU; self.confirm_index = 1
        elif opt == "Quitter le jeu":
            self.mode = MODE_CONFIRM_QUIT; self.confirm_index = 1

    def _begin_save(self):
        if self.game_manager.current_save_slot is not None:
            self._perform_save(self.game_manager.current_save_slot)
        else:
            self._load_slot_info()
            self.mode = MODE_SAVE
            self.slot_selection = 0

    def _load_slot_info(self):
        try:
            from core.save_manager import SaveManager
            self.slots_info = SaveManager().get_all_slots_info()
        except Exception:
            self.slots_info = [None, None, None]

    def _perform_save(self, slot_index):
        try:
            from core.save_manager import SaveManager
            SaveManager().save(self.game_manager, slot_index)
            self.game_manager.current_save_slot = slot_index
            self._msg("Partie sauvegardee !", (100, 230, 100))
            self.mode = MODE_MENU
        except Exception:
            self._msg("Erreur de sauvegarde", (230, 80, 80))
            self.mode = MODE_MENU

    def _handle_save(self, event):
        if event.key == pygame.K_ESCAPE:
            self.mode = MODE_MENU; return
        if event.key == pygame.K_UP:
            self.slot_selection = max(0, self.slot_selection - 1)
            self.game_manager.audio_manager.play_sfx("menu_select")
        elif event.key == pygame.K_DOWN:
            self.slot_selection = min(2, self.slot_selection + 1)
            self.game_manager.audio_manager.play_sfx("menu_select")
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self._perform_save(self.slot_selection)

    def _handle_confirm(self, event, action):
        if event.key == pygame.K_ESCAPE:
            self.mode = MODE_MENU; return
        if event.key == pygame.K_LEFT:
            self.confirm_index = 0
        elif event.key == pygame.K_RIGHT:
            self.confirm_index = 1
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
            if self.confirm_index == 0:
                if action == "quit":
                    self.game_manager.running = False
                elif action == "menu":
                    self._return_to_main_menu()
            else:
                self.mode = MODE_MENU

    def _return_to_main_menu(self):
        from states.state_menu import StateMenu
        self.game_manager.state_manager.clear()
        self.game_manager.player            = None
        self.game_manager.quest_manager     = None
        self.game_manager.current_save_slot = None
        self.game_manager.state_manager.push(StateMenu(self.game_manager))

    def _msg(self, text, color=None):
        self.temp_message  = text
        self.message_color = color or C_WHITE
        self.message_timer = MESSAGE_DURATION

    def _format_time(self):
        if not self.game_manager.player:
            return "00:00:00"
        t = int(self.game_manager.player.play_time)
        return f"{t//3600:02d}:{(t%3600)//60:02d}:{t%60:02d}"

    # -------------------------------------------------------------------------
    def update(self, dt):
        if self.temp_message:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.temp_message = None

    # =========================================================================
    # RENDER
    # =========================================================================
    def render(self, screen):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 145))
        screen.blit(ov, (0, 0))

        if   self.mode == MODE_MENU:         self._draw_menu(screen)
        elif self.mode == MODE_SAVE:         self._draw_save(screen)
        elif self.mode == MODE_CONFIRM_QUIT: self._draw_confirm(
            screen, "Quitter le jeu ?", "La progression non sauvegardee sera perdue.")
        elif self.mode == MODE_CONFIRM_MENU: self._draw_confirm(
            screen, "Menu principal ?", "La progression non sauvegardee sera perdue.")

        if self.temp_message:
            self._draw_msg(screen)

    # -------------------------------------------------------------------------
    def _draw_menu(self, screen):
        cx = SCREEN_WIDTH // 2
        fw, fh = 300, 478
        fx, fy = cx - fw // 2, (SCREEN_HEIGHT - fh) // 2

        panel(screen, fx, fy, fw, fh, border=C_GOLD)
        corner_accents(screen, fx, fy, fw, fh)

        text_c(screen, self.f_title, "Pause", C_GOLD, cx, fy + 14, shadow=True)

        t_surf = self.f_info.render(f"Temps : {self._format_time()}", True, C_GRAY)
        screen.blit(t_surf, (cx - t_surf.get_width() // 2, fy + 54))

        pygame.draw.line(screen, C_GOLD_DIM,
                         (fx + 16, fy + 74), (fx + fw - 16, fy + 74), 1)

        for i, opt in enumerate(self.options):
            oy     = fy + 86 + i * 50
            is_sel = (i == self.selection_index)
            is_red = (opt == "Quitter le jeu" and is_sel)

            if is_sel:
                hl = pygame.Surface((fw - 24, 40), pygame.SRCALPHA)
                hl.fill((*C_GOLD, 28))
                screen.blit(hl, (fx + 12, oy - 5))
                pygame.draw.rect(screen, C_GOLD, (fx + 12, oy - 5, fw - 24, 40), 1)
                arrow = self.f_opt.render(">", True, C_GOLD)
                screen.blit(arrow, (fx + 20, oy))

            is_cheat = (opt == "Tricher")
            color = (230, 80, 80) if is_red else ((230, 130, 40) if is_cheat else (C_GOLD if is_sel else C_WHITE))
            txt = self.f_opt.render(opt, True, color)
            screen.blit(txt, (fx + 42, oy))

        hint = self.f_hint.render("[ECHAP] Reprendre", True, C_GRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, fy + fh - 24))

    # -------------------------------------------------------------------------
    def _draw_save(self, screen):
        cx = SCREEN_WIDTH // 2
        fw, fh = 480, 295
        fx, fy = cx - fw // 2, (SCREEN_HEIGHT - fh) // 2

        panel(screen, fx, fy, fw, fh, border=C_GOLD)
        corner_accents(screen, fx, fy, fw, fh)
        text_c(screen, self.f_opt, "Choisir un slot", C_GOLD, cx, fy + 14)
        pygame.draw.line(screen, C_GOLD_DIM,
                         (fx + 16, fy + 40), (fx + fw - 16, fy + 40), 1)

        for i in range(3):
            sy      = fy + 52 + i * 70
            is_sel  = (i == self.slot_selection)
            border  = C_GOLD if is_sel else (55, 65, 108)
            slot    = self.slots_info[i] if self.slots_info else None
            occupied = slot and slot.get("occupied")

            sr = pygame.Rect(fx + 16, sy, fw - 32, 58)
            if is_sel:
                hl = pygame.Surface((sr.w, sr.h), pygame.SRCALPHA)
                hl.fill((*C_GOLD, 22))
                screen.blit(hl, sr.topleft)
            pygame.draw.rect(screen, border, sr, 1)

            # Badge numéro
            bw = 34
            badge = pygame.Surface((bw, sr.h), pygame.SRCALPHA)
            badge.fill((*( C_GOLD if is_sel else (45, 55, 95) ), 200))
            screen.blit(badge, sr.topleft)
            n = self.f_opt.render(str(i + 1), True, C_BLACK if is_sel else C_WHITE)
            screen.blit(n, (sr.x + (bw - n.get_width()) // 2,
                            sr.y + (sr.h - n.get_height()) // 2))

            cx_c  = sr.x + bw + 10
            max_w = sr.w - bw - 14
            if occupied:
                nm = self.f_opt.render(slot.get("trainer_name", "???"), True,
                                       C_GOLD if is_sel else C_WHITE)
                blit_clipped(screen, nm, cx_c, sy + 8, max_w)
                det = self.f_info.render(
                    f"Zone: {slot.get('zone','?')}   Temps: {slot.get('play_time_formatted','?')}",
                    True, C_WHITE if is_sel else C_GRAY)
                blit_clipped(screen, det, cx_c, sy + 34, max_w)
                if is_sel:
                    warn = self.f_hint.render("Ecrasera la sauvegarde existante",
                                              True, (230, 150, 80))
                    blit_clipped(screen, warn, cx_c, sy + 46, max_w)
            else:
                em = self.f_opt.render("Vide", True, C_GRAY)
                screen.blit(em, (cx_c, sy + (sr.h - em.get_height()) // 2))

        hint = self.f_hint.render(
            "[HAUT/BAS] Naviguer   [ENTREE] Sauvegarder   [ECHAP] Annuler", True, C_GRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, fy + fh - 22))

    # -------------------------------------------------------------------------
    def _draw_confirm(self, screen, title, subtitle):
        cx = SCREEN_WIDTH // 2
        fw, fh = 460, 155
        fx, fy = cx - fw // 2, (SCREEN_HEIGHT - fh) // 2

        panel(screen, fx, fy, fw, fh, border=(210, 90, 60))
        corner_accents(screen, fx, fy, fw, fh, color=(210, 90, 60))

        text_c(screen, self.f_confirm, title, C_WHITE, cx, fy + 18)
        st = self.f_info.render(subtitle, True, (230, 170, 120))
        screen.blit(st, (cx - st.get_width() // 2, fy + 54))

        for i, lbl in enumerate(["Oui", "Non"]):
            color = C_GOLD if i == self.confirm_index else C_WHITE
            pre   = "> " if i == self.confirm_index else "  "
            s = self.f_confirm.render(pre + lbl, True, color)
            screen.blit(s, (fx + 120 + i * 160, fy + 98))

    # -------------------------------------------------------------------------
    def _draw_msg(self, screen):
        surf = self.f_info.render(self.temp_message, True, self.message_color)
        pad  = 14
        bw   = surf.get_width() + pad * 2
        bh   = surf.get_height() + pad
        bg   = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 200))
        cx   = (SCREEN_WIDTH - bw) // 2
        cy   = SCREEN_HEIGHT // 2 + 110
        screen.blit(bg,   (cx, cy))
        screen.blit(surf, (cx + pad, cy + pad // 2))
