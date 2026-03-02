# =============================================================================
# STATE_SHOP.PY - SHOP STATE  (Pokemon DA)
# =============================================================================

import pygame
from states.state import State
from economy.shop import Shop
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from ui.poke_style import (
    C_GOLD, C_GOLD_DIM, C_WHITE, C_GRAY, C_PANEL, C_GREEN,
    font, make_gradient_bg, panel, corner_accents, text_c, wrap,
)

# =============================================================================
# LAYOUT  (outer panel: 32px margin H, 18px margin V)
# =============================================================================
OX, OY = 32, 18
OW, OH  = SCREEN_WIDTH - OX * 2, SCREEN_HEIGHT - OY * 2   # 736 × 564

TITLE_H       = 60          # height of the title band
SEP_Y         = OY + TITLE_H + 4   # horizontal separator between title and content

# Content starts just below the separator
CONTENT_Y     = SEP_Y + 12
CONTENT_BOT   = OY + OH - 38       # leave 38px for hint at the bottom
CONTENT_H     = CONTENT_BOT - CONTENT_Y   # ≈ 432 px

# Vertical separator between list and info panels (relative to outer panel)
VSEP_REL      = 408         # from OX

LIST_X        = OX + 16
LIST_W        = VSEP_REL - 24      # ≈ 384
LIST_Y        = CONTENT_Y
LIST_H        = CONTENT_H

INFO_X        = OX + VSEP_REL + 12
INFO_W        = OX + OW - INFO_X - 12   # right edge of outer panel
INFO_Y        = CONTENT_Y
INFO_H        = CONTENT_H

ITEMS_PER_PAGE = 7
ROW_H          = LIST_H // ITEMS_PER_PAGE   # ≈ 61 px

# Item category palette
CATEGORY_COLORS = {
    "heal":     ( 80, 210, 100),
    "pokeball": (220,  80,  70),
    "boost":    ( 90, 160, 255),
    "revive":   (230, 200,  50),
    "status":   (180,  80, 230),
}
CATEGORY_LABELS = {
    "heal":     "SOIN",
    "pokeball": "BALL",
    "boost":    "BOOST",
    "revive":   "RAPPEL",
    "status":   "STATUT",
}

MESSAGE_DURATION = 1.8


# =============================================================================
# STATE
# =============================================================================

class StateShop(State):
    """Full-screen shop, Pokemon DA style."""

    transparent = False

    # -------------------------------------------------------------------------
    def __init__(self, game_manager, npc=None):
        super().__init__(game_manager)
        self.npc = npc

        # ---- fonts -----------------------------------------------------------
        self.f_title  = font(26)            # "BOUTIQUE"
        self.f_sub    = font(14)            # shopkeeper name
        self.f_item   = font(14)            # item name in list
        self.f_price  = font(14)            # price in list
        self.f_cat    = pygame.font.Font(None, 17)
        self.f_info   = pygame.font.Font(None, 21)
        self.f_desc   = pygame.font.Font(None, 20)
        self.f_hint   = pygame.font.Font(None, 19)
        self.f_iname  = font(18)            # item name in info panel
        self.f_iprice = font(20)            # price in info panel
        self.f_cred   = font(18)            # credits display

        # ---- shop logic ------------------------------------------------------
        self.shop    = Shop(game_manager.item_catalog, game_manager.player)
        self.catalog = self.shop.get_catalog()
        self._sort_catalog()

        self.selection_index = 0
        self.scroll_offset   = 0

        # ---- feedback message ------------------------------------------------
        self.temp_message  = None
        self.message_timer = 0.0
        self.message_ok    = True

        self._bg = make_gradient_bg(SCREEN_WIDTH, SCREEN_HEIGHT)

    # -------------------------------------------------------------------------
    def _sort_catalog(self):
        order = ["heal", "pokeball", "boost", "revive", "status"]
        self.catalog.sort(key=lambda it: (
            order.index(it.category) if it.category in order else 99,
            it.price
        ))

    # -------------------------------------------------------------------------
    def on_enter(self):
        self.game_manager.audio_manager.play_music("shop")

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
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._attempt_purchase()

    def _navigate(self, d):
        if not self.catalog:
            return
        old = self.selection_index
        self.selection_index = max(0, min(len(self.catalog) - 1, self.selection_index + d))
        if self.selection_index != old:
            self.game_manager.audio_manager.play_sfx("menu_select")
        if self.selection_index < self.scroll_offset:
            self.scroll_offset = self.selection_index
        if self.selection_index >= self.scroll_offset + ITEMS_PER_PAGE:
            self.scroll_offset = self.selection_index - ITEMS_PER_PAGE + 1

    def _attempt_purchase(self):
        if not self.catalog or self.temp_message is not None:
            return
        item   = self.catalog[self.selection_index]
        result = self.shop.buy(item.id)
        if result["success"]:
            self.temp_message  = f"{item.name} acheté !"
            self.message_ok    = True
            self.message_timer = MESSAGE_DURATION
            self.game_manager.audio_manager.play_sfx("purchase")
        else:
            reason = result.get("failure_reason", "")
            self.temp_message  = ("Pas assez de crédits !"
                                  if reason == "insufficient_credits"
                                  else "Achat impossible.")
            self.message_ok    = False
            self.message_timer = MESSAGE_DURATION
            self.game_manager.audio_manager.play_sfx("error")

    # -------------------------------------------------------------------------
    def update(self, dt):
        if self.temp_message is not None:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.temp_message = None

    # =========================================================================
    # RENDER
    # =========================================================================
    def render(self, screen):
        screen.blit(self._bg, (0, 0))

        # Outer panel
        panel(screen, OX, OY, OW, OH, border=C_GOLD)
        corner_accents(screen, OX, OY, OW, OH)

        self._draw_title(screen)
        self._draw_list(screen)
        self._draw_vsep(screen)
        self._draw_info(screen)
        self._draw_hint(screen)

        if self.temp_message is not None:
            self._draw_message(screen)

    # -------------------------------------------------------------------------
    def _draw_title(self, screen):
        cx = OX + OW // 2

        # "BOUTIQUE"
        text_c(screen, self.f_title, "BOUTIQUE", C_GOLD, cx, OY + 10, shadow=True)

        # Shopkeeper name
        if self.npc is not None:
            sub = self.f_sub.render(self.npc.name, True, C_GRAY)
            screen.blit(sub, (cx - sub.get_width() // 2, OY + 40))

        # Horizontal separator
        pygame.draw.line(screen, C_GOLD_DIM,
                         (OX + 16, SEP_Y), (OX + OW - 16, SEP_Y), 1)

    def _draw_vsep(self, screen):
        """Vertical separator between list and info panels."""
        pygame.draw.line(screen, C_GOLD_DIM,
                         (OX + VSEP_REL, CONTENT_Y),
                         (OX + VSEP_REL, CONTENT_BOT), 1)

    # -------------------------------------------------------------------------
    def _draw_list(self, screen):
        player = self.game_manager.player
        start  = self.scroll_offset
        end    = min(start + ITEMS_PER_PAGE, len(self.catalog))

        for i in range(start, end):
            item       = self.catalog[i]
            row_y      = LIST_Y + (i - start) * ROW_H
            is_sel     = (i == self.selection_index)
            cat_c      = CATEGORY_COLORS.get(item.category, C_GRAY)
            affordable = player.credits >= item.price

            # --- Selection highlight ------------------------------------------
            if is_sel:
                hl = pygame.Surface((LIST_W, ROW_H - 2), pygame.SRCALPHA)
                hl.fill((*C_GOLD, 25))
                screen.blit(hl, (LIST_X, row_y + 1))
                # Gold left accent bar
                pygame.draw.rect(screen, C_GOLD, (LIST_X, row_y + 4, 3, ROW_H - 8))

            # --- Category badge -----------------------------------------------
            badge_w, badge_h = 50, 20
            badge_x = LIST_X + 8
            badge_y = row_y + (ROW_H - badge_h) // 2
            badge   = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
            badge.fill((*cat_c, 190))
            screen.blit(badge, (badge_x, badge_y))
            lbl = self.f_cat.render(CATEGORY_LABELS.get(item.category, "?"), True, (8, 8, 8))
            screen.blit(lbl, (badge_x + (badge_w - lbl.get_width()) // 2,
                               badge_y + (badge_h - lbl.get_height()) // 2))

            # --- Item name ----------------------------------------------------
            name_col = C_WHITE if affordable else (110, 70, 70)
            name_s   = self.f_item.render(item.name, True, name_col)
            name_y   = row_y + (ROW_H - name_s.get_height()) // 2
            screen.blit(name_s, (LIST_X + badge_w + 18, name_y))

            # --- Owned qty (right-aligned, before price) ----------------------
            qty   = player.inventory.get_quantity(item.id)
            qty_s = self.f_cat.render(f"×{qty}", True, C_GRAY)
            qty_x = LIST_X + LIST_W - 84
            screen.blit(qty_s, (qty_x, row_y + (ROW_H - qty_s.get_height()) // 2 + 2))

            # --- Price (right-aligned) ----------------------------------------
            price_col = C_GOLD if affordable else (150, 60, 60)
            price_s   = self.f_price.render(f"{item.price} cr", True, price_col)
            price_x   = LIST_X + LIST_W - price_s.get_width()
            screen.blit(price_s, (price_x, row_y + (ROW_H - price_s.get_height()) // 2))

            # --- Row separator ------------------------------------------------
            if i < end - 1:
                pygame.draw.line(screen, (30, 38, 70),
                                 (LIST_X + 4, row_y + ROW_H - 1),
                                 (LIST_X + LIST_W - 4, row_y + ROW_H - 1), 1)

        # --- Scroll arrows ----------------------------------------------------
        arrow_cx = LIST_X + LIST_W // 2
        if start > 0:
            arr = self.f_cat.render("▲", True, C_GRAY)
            screen.blit(arr, (arrow_cx - arr.get_width() // 2, LIST_Y + 2))
        if end < len(self.catalog):
            arr = self.f_cat.render("▼", True, C_GRAY)
            screen.blit(arr, (arrow_cx - arr.get_width() // 2,
                               LIST_Y + LIST_H - arr.get_height() - 2))

    # -------------------------------------------------------------------------
    def _draw_info(self, screen):
        if not self.catalog:
            return

        item       = self.catalog[self.selection_index]
        player     = self.game_manager.player
        cat_c      = CATEGORY_COLORS.get(item.category, C_GRAY)
        affordable = player.credits >= item.price

        cy = INFO_Y

        # --- Category header band --------------------------------------------
        hdr = pygame.Surface((INFO_W, 28), pygame.SRCALPHA)
        hdr.fill((*cat_c, 170))
        screen.blit(hdr, (INFO_X, cy))
        cat_lbl = CATEGORY_LABELS.get(item.category, item.category.upper())
        cs = self.f_cat.render(cat_lbl, True, (8, 8, 8))
        screen.blit(cs, (INFO_X + (INFO_W - cs.get_width()) // 2,
                          cy + (28 - cs.get_height()) // 2))
        cy += 36

        # --- Item name (Pokemon font, centered) ------------------------------
        ns = self.f_iname.render(item.name, True, C_WHITE)
        screen.blit(ns, (INFO_X + (INFO_W - ns.get_width()) // 2, cy))
        cy += ns.get_height() + 8

        # --- Price (Pokemon font, gold or red, centered) ---------------------
        pc = C_GOLD if affordable else (210, 70, 70)
        ps = self.f_iprice.render(f"{item.price} cr", True, pc)
        screen.blit(ps, (INFO_X + (INFO_W - ps.get_width()) // 2, cy))
        cy += ps.get_height() + 12

        pygame.draw.line(screen, C_GOLD_DIM,
                         (INFO_X + 8, cy), (INFO_X + INFO_W - 8, cy), 1)
        cy += 10

        # --- Description (wrapped system font) --------------------------------
        for line in wrap(self.f_desc, self._get_desc(item), INFO_W - 16):
            ls = self.f_desc.render(line, True, C_GRAY)
            screen.blit(ls, (INFO_X + 8, cy))
            cy += ls.get_height() + 3
        cy += 10

        pygame.draw.line(screen, C_GOLD_DIM,
                         (INFO_X + 8, cy), (INFO_X + INFO_W - 8, cy), 1)
        cy += 10

        # --- Usage badges ----------------------------------------------------
        badges = []
        if item.usable_in_combat:
            badges.append(("Combat",      ( 90, 160, 255)))
        if item.usable_outside_combat:
            badges.append(("Hors combat", ( 80, 210, 100)))

        bx = INFO_X + 8
        for label, bcol in badges:
            lw, lh = self.f_cat.size(label)
            bs = pygame.Surface((lw + 12, lh + 6), pygame.SRCALPHA)
            bs.fill((*bcol, 170))
            screen.blit(bs, (bx, cy))
            ls = self.f_cat.render(label, True, (8, 8, 8))
            screen.blit(ls, (bx + 6, cy + 3))
            bx += bs.get_width() + 6
        cy += self.f_cat.get_height() + 14

        # --- Owned quantity --------------------------------------------------
        qty = player.inventory.get_quantity(item.id)
        qs  = self.f_info.render(f"Possédé : ×{qty}", True, C_GRAY)
        screen.blit(qs, (INFO_X + 8, cy))
        cy += qs.get_height() + 20

        # --- Credits (Pokemon font, gold, centered) --------------------------
        pygame.draw.line(screen, C_GOLD_DIM,
                         (INFO_X + 8, cy), (INFO_X + INFO_W - 8, cy), 1)
        cy += 10
        cr_s = self.f_cred.render(f"Crédits : {player.credits}", True, C_GOLD)
        screen.blit(cr_s, (INFO_X + (INFO_W - cr_s.get_width()) // 2, cy))

    # -------------------------------------------------------------------------
    def _get_desc(self, item):
        if item.category == "heal":
            return f"Restaure {item.effect_value} PV à un Pokémon."
        if item.category == "pokeball":
            return f"Taux de capture : {item.effect_value}%."
        if item.category == "boost":
            return f"Augmente une stat de {item.effect_value}% pour 1 combat."
        if item.category == "revive":
            return f"Réanime un Pokémon K.O. ({item.effect_value}% de ses PV)."
        if item.category == "status":
            return "Soigne toutes les altérations de statut."
        return "Objet spécial."

    # -------------------------------------------------------------------------
    def _draw_hint(self, screen):
        hint = "[↑↓] Choisir    [Entrée] Acheter    [Échap] Quitter"
        hs   = self.f_hint.render(hint, True, C_GRAY)
        cx   = OX + OW // 2
        screen.blit(hs, (cx - hs.get_width() // 2,
                          OY + OH - 26))

    # -------------------------------------------------------------------------
    def _draw_message(self, screen):
        col      = C_GREEN if self.message_ok else (220, 80, 80)
        ms       = self.f_iname.render(self.temp_message, True, col)
        pad_x, pad_y = 28, 14
        bw = ms.get_width()  + pad_x * 2
        bh = ms.get_height() + pad_y * 2
        bx = (SCREEN_WIDTH  - bw) // 2
        by = (SCREEN_HEIGHT - bh) // 2
        bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bg.fill((*C_PANEL, 245))
        screen.blit(bg, (bx, by))
        pygame.draw.rect(screen, col, (bx, by, bw, bh), 2)
        corner_accents(screen, bx, by, bw, bh, color=col, size=8)
        screen.blit(ms, (bx + pad_x, by + pad_y))
