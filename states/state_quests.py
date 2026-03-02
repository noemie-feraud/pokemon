# =============================================================================
# STATE_QUESTS.PY - QUESTS AND CHALLENGES SCREEN
# =============================================================================

import json
import pygame
from states.state import State
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, QUESTS_DATA_FILE
from ui.poke_style import (
    C_GOLD, C_GOLD_DIM, C_WHITE, C_GRAY, C_GREEN, C_PANEL,
    font, panel, corner_accents, text_c, blit_clipped,
)


class StateQuests(State):

    transparent = True

    # -------------------------------------------------------------------------
    def __init__(self, game_manager):
        super().__init__(game_manager)

        self.f_title  = font(30)
        self.f_header = font(18)
        self.f_body   = pygame.font.Font(None, 20)
        self.f_hint   = pygame.font.Font(None, 18)

        self._entries = self._build_entries()
        self._scroll  = 0
        self._sel     = 0

    # -------------------------------------------------------------------------
    def _build_entries(self):
        player  = self.game_manager.player
        entries = []

        # --- quests.json system ---
        try:
            with open(QUESTS_DATA_FILE, "r", encoding="utf-8") as f:
                all_quests = json.load(f)
            qmap = {q["id"]: q for q in all_quests}
        except Exception:
            qmap = {}

        for qid in player.active_quests:
            q = qmap.get(qid)
            if not q:
                continue
            progress = self._quest_progress(q, player)
            reward   = q.get("reward", {})
            entries.append({
                "title":    q.get("title", f"Quete {qid}"),
                "desc":     q.get("description", ""),
                "progress": progress,
                "reward":   f"{reward.get('amount', '?')} credits" if reward else "",
                "done":     False,
            })

        # --- challenge system ---
        total_owned = len(player.team) + len(player.storage)
        for npc_id, ch in player.challenges.items():
            target = ch["target"]
            entries.append({
                "title":    "Defi capture",
                "desc":     f"Capture {target} Pokemon",
                "progress": f"{min(total_owned, target)}/{target}",
                "reward":   f"{ch['reward']} credits",
                "done":     False,
            })

        return entries

    def _quest_progress(self, q, player):
        qt = q.get("type")
        if qt == "capture_type":
            tt    = q.get("target_type", "")
            count = sum(1 for p in player.team    if tt in p.types)
            count += sum(1 for p in player.storage if tt in p.types)
            return f"{count}/{q['target_count']}"
        if qt == "level_up":
            best = max((p.level for p in player.team), default=0)
            return f"Niv.{best}/{q['target_level']}"
        if qt == "defeat_trainers":
            return f"{len(player.trainers_beaten)}/{q['target_count']}"
        return "?"

    # -------------------------------------------------------------------------
    def on_enter(self):
        pass

    def handle_events(self, events):
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.game_manager.state_manager.pop()
            elif event.key == pygame.K_UP   and self._sel > 0:
                self._sel -= 1
                self._clamp_scroll()
            elif event.key == pygame.K_DOWN and self._sel < len(self._entries) - 1:
                self._sel += 1
                self._clamp_scroll()

    VISIBLE = 5

    def _clamp_scroll(self):
        if self._sel < self._scroll:
            self._scroll = self._sel
        if self._sel >= self._scroll + self.VISIBLE:
            self._scroll = self._sel - self.VISIBLE + 1

    def update(self, dt):
        pass

    # =========================================================================
    # RENDER
    # =========================================================================
    def render(self, screen):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 145))
        screen.blit(ov, (0, 0))

        cx = SCREEN_WIDTH // 2
        pw, ph = 560, 480
        px, py = cx - pw // 2, (SCREEN_HEIGHT - ph) // 2

        panel(screen, px, py, pw, ph, border=C_GOLD)
        corner_accents(screen, px, py, pw, ph)

        # Title
        text_c(screen, self.f_title, "Quetes & Defis", C_GOLD, cx, py + 14, shadow=True)

        # Counters
        player = self.game_manager.player
        total  = len(self._entries)
        done   = len(player.quests_completed) + len(player.challenges_completed)
        stats  = self.f_body.render(
            f"En cours : {total}    Terminees : {done}", True, C_GRAY)
        screen.blit(stats, (cx - stats.get_width() // 2, py + 50))

        pygame.draw.line(screen, C_GOLD_DIM,
                         (px + 16, py + 68), (px + pw - 16, py + 68), 1)

        # Empty state
        if not self._entries:
            msg = self.f_body.render("Aucune quete ou defi en cours.", True, C_GRAY)
            screen.blit(msg, (cx - msg.get_width() // 2, py + ph // 2 - 10))
        else:
            self._draw_entries(screen, px, py, pw, ph)

        # Scroll arrows
        if self._scroll > 0:
            arr = self.f_hint.render("▲", True, C_GRAY)
            screen.blit(arr, (cx - arr.get_width() // 2, py + 72))
        if self._scroll + self.VISIBLE < len(self._entries):
            arr = self.f_hint.render("▼", True, C_GRAY)
            screen.blit(arr, (cx - arr.get_width() // 2, py + ph - 38))

        hint = self.f_hint.render("[HAUT/BAS] Naviguer    [ECHAP] Fermer", True, C_GRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, py + ph - 22))

    # -------------------------------------------------------------------------
    def _draw_entries(self, screen, px, py, pw, ph):
        cx      = px + pw // 2
        entry_h = 74
        start_y = py + 78

        for rank in range(self.VISIBLE):
            idx = self._scroll + rank
            if idx >= len(self._entries):
                break

            entry  = self._entries[idx]
            ey     = start_y + rank * entry_h
            is_sel = (idx == self._sel)
            max_w  = pw - 32

            # Selection highlight
            if is_sel:
                hl = pygame.Surface((pw - 24, entry_h - 6), pygame.SRCALPHA)
                hl.fill((*C_GOLD, 22))
                screen.blit(hl, (px + 12, ey))
                pygame.draw.rect(screen, C_GOLD,
                                 (px + 12, ey, pw - 24, entry_h - 6), 1)

            # Title + progress badge
            title_s = self.f_header.render(entry["title"], True,
                                           C_GOLD if is_sel else C_WHITE)
            blit_clipped(screen, title_s, px + 20, ey + 6, max_w - 120)

            prog_s = self.f_header.render(entry["progress"], True,
                                          C_GREEN if is_sel else (100, 200, 120))
            screen.blit(prog_s, (px + pw - 20 - prog_s.get_width(), ey + 6))

            # Progress bar
            bar_x, bar_y, bar_w, bar_h = px + 20, ey + 28, pw - 40, 6
            try:
                cur_str, tot_str = entry["progress"].split("/")
                ratio = min(int(cur_str.replace("Niv.", "")) /
                            int(tot_str.replace("Niv.", "")), 1.0)
            except Exception:
                ratio = 0.0
            pygame.draw.rect(screen, (40, 50, 80), (bar_x, bar_y, bar_w, bar_h))
            if ratio > 0:
                pygame.draw.rect(screen, C_GREEN,
                                 (bar_x, bar_y, int(bar_w * ratio), bar_h))

            # Description
            desc_s = self.f_body.render(entry["desc"], True, C_GRAY)
            blit_clipped(screen, desc_s, px + 20, ey + 40, max_w - 120)

            # Reward
            if entry["reward"]:
                rew_s = self.f_body.render(
                    f"Recompense : {entry['reward']}", True,
                    (180, 230, 140) if is_sel else C_GRAY)
                screen.blit(rew_s, (px + pw - 20 - rew_s.get_width(), ey + 42))

            # Separator
            sep_y = ey + entry_h - 4
            pygame.draw.line(screen, (38, 48, 78),
                             (px + 16, sep_y), (px + pw - 16, sep_y), 1)
