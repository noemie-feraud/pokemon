# =============================================================================
# STATE_SHOP.PY - SHOP STATE
# =============================================================================
#
# This state displays the shop when the player talks to the shopkeeper.
# It's a full-screen (not transparent) interface showing buyable items,
# their prices, owned quantities, and player credits.

import pygame
from states.state import State
from economy.shop import Shop
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

MESSAGE_DURATION = 1.5           # seconds to display temporary message
ITEMS_PER_PAGE = 6               # number of items visible on screen

CATEGORY_COLORS = {
    "heal": (100, 255, 100),      # green
    "pokeball": (255, 100, 100),  # red
    "boost": (100, 100, 255),     # blue
    "revive": (255, 255, 100),    # yellow
    "status": (200, 100, 255)     # purple
}


# =============================================================================
# STATE SHOP CLASS
# =============================================================================

class StateShop(State):
    """
    Shop screen. Displays buyable items, handles purchases.
    Pushed by NpcShopkeeper callback, pops on Escape.
    """
    
    transparent = False
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager):
        """
        Initialize shop state.
        
        Args:
            game_manager: reference to Game
        """
        super().__init__(game_manager)
        
        # --- FONTS ---
        self.font_title = pygame.font.Font(None, 36)
        self.font_item = pygame.font.Font(None, 26)
        self.font_info = pygame.font.Font(None, 22)
        self.font_message = pygame.font.Font(None, 28)
        
        # --- SHOP (purchase logic) ---
        self.shop = Shop(
            item_catalog=game_manager.item_catalog,
            player=game_manager.player
        )
        
        # --- CATALOG ---
        # List of buyable items, sorted by category then price
        self.catalog = self.shop.get_catalog()
        self._sort_catalog()
        
        # --- CURSOR ---
        self.selection_index = 0
        self.scroll_offset = 0    # for scrolling if more than ITEMS_PER_PAGE
        
        # --- TEMPORARY MESSAGE ---
        self.temp_message = None
        self.message_timer = 0
        self.message_color = (255, 255, 255)
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _sort_catalog(self):
        """Sort items by category (heal, pokeball, boost, revive, status)
           then by price within each category."""
        category_order = ["heal", "pokeball", "boost", "revive", "status"]
        
        self.catalog.sort(
            key=lambda item: (
                category_order.index(item.category) if item.category in category_order else 99,
                item.price
            )
        )
    
    
    # -------------------------------------------------------------------------
    # LIFECYCLE METHODS
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """Called when shop becomes active."""
        self.game_manager.audio_manager.play_music("shop")
    
    
    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """Handle player input."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            # --- QUIT (Escape) ---
            if event.key == pygame.K_ESCAPE:
                self.game_manager.state_manager.pop()
                return
            
            # --- NAVIGATION ---
            if event.key == pygame.K_UP:
                self._navigate(-1)
            
            elif event.key == pygame.K_DOWN:
                self._navigate(1)
            
            # --- BUY (Space/Enter) ---
            elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                self._attempt_purchase()
    
    
    def _navigate(self, direction):
        """
        Move cursor in the list. Handles scrolling.
        
        Args:
            direction: -1 (up) or +1 (down)
        """
        if len(self.catalog) == 0:
            return
        
        old_index = self.selection_index
        self.selection_index += direction
        
        # Clamp
        if self.selection_index < 0:
            self.selection_index = 0
        if self.selection_index >= len(self.catalog):
            self.selection_index = len(self.catalog) - 1
        
        # Navigation sound
        if self.selection_index != old_index:
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        # Adjust scroll
        if self.selection_index < self.scroll_offset:
            self.scroll_offset = self.selection_index
        if self.selection_index >= self.scroll_offset + ITEMS_PER_PAGE:
            self.scroll_offset = self.selection_index - ITEMS_PER_PAGE + 1
    
    
    def _attempt_purchase(self):
        """Attempt to buy the selected item."""
        if len(self.catalog) == 0:
            return
        
        # Ignore if a message is already displayed
        if self.temp_message is not None:
            return
        
        item = self.catalog[self.selection_index]
        
        # Attempt purchase via shop logic
        result = self.shop.buy(item.id)
        
        if result["success"]:
            self.temp_message = f"{item.name} acheté !"
            self.message_color = (100, 255, 100)    # green
            self.message_timer = MESSAGE_DURATION
            self.game_manager.audio_manager.play_sfx("purchase")
        
        else:
            if result["reason"] == "insufficient_credits":
                self.temp_message = "Pas assez de crédits !"
            else:
                self.temp_message = result.get("reason", "Achat impossible")
            
            self.message_color = (255, 100, 100)    # red
            self.message_timer = MESSAGE_DURATION
            self.game_manager.audio_manager.play_sfx("error")
    
    
    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    
    def update(self, dt):
        """Update temporary message timer."""
        if self.temp_message is not None:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.temp_message = None
    
    
    # -------------------------------------------------------------------------
    # RENDERING
    # -------------------------------------------------------------------------
    
    def render(self, screen):
        """Draw the shop screen."""
        # --- BACKGROUND ---
        screen.fill((30, 30, 50))
        
        # --- TITLE ---
        self._draw_title(screen)
        
        # --- ITEM LIST ---
        self._draw_list(screen)
        
        # --- INFO PANEL ---
        self._draw_info(screen)
        
        # --- PLAYER CREDITS ---
        self._draw_credits(screen)
        
        # --- TEMPORARY MESSAGE ---
        if self.temp_message is not None:
            self._draw_message(screen)
        
        # --- CONTROLS HINT ---
        self._draw_controls(screen)
    
    
    def _draw_title(self, screen):
        """Draw shop title."""
        surface = self.font_title.render("Boutique", True, (255, 255, 255))
        x = (SCREEN_WIDTH - surface.get_width()) // 2
        screen.blit(surface, (x, 20))
    
    
    def _draw_list(self, screen):
        """
        Draw the item list with cursor.
        Shows ITEMS_PER_PAGE items at a time, with scrolling.
        """
        list_x = 50
        list_y = 70
        line_height = 45
        player = self.game_manager.player
        
        # Determine visible items
        start = self.scroll_offset
        end = min(start + ITEMS_PER_PAGE, len(self.catalog))
        
        for i in range(start, end):
            item = self.catalog[i]
            y = list_y + (i - start) * line_height
            
            # --- LINE BACKGROUND (highlight if selected) ---
            if i == self.selection_index:
                bg_rect = pygame.Rect(list_x - 10, y - 5,
                                      SCREEN_WIDTH - 80, line_height)
                pygame.draw.rect(screen, (60, 60, 90), bg_rect)
            
            # --- CURSOR ---
            prefix = "> " if i == self.selection_index else "  "
            
            # --- CATEGORY TAG ---
            category_color = CATEGORY_COLORS.get(item.category, (200, 200, 200))
            tag = f"[{item.category[:4].upper()}]"
            tag_surface = self.font_info.render(tag, True, category_color)
            screen.blit(tag_surface, (list_x + 20, y + 2))
            
            # --- NAME ---
            name_surface = self.font_item.render(
                prefix + item.name, True, (255, 255, 255))
            screen.blit(name_surface, (list_x + 80, y))
            
            # --- PRICE ---
            # Gray out if player can't afford
            if player.credits >= item.price:
                price_color = (255, 255, 255)
            else:
                price_color = (150, 80, 80)
            
            price_text = f"{item.price} cr"
            price_surface = self.font_item.render(price_text, True, price_color)
            price_x = SCREEN_WIDTH - 200
            screen.blit(price_surface, (price_x, y))
            
            # --- OWNED QUANTITY ---
            quantity = player.inventory.get_quantity(item.id)
            qty_text = f"x{quantity}"
            qty_surface = self.font_info.render(qty_text, True, (180, 180, 180))
            screen.blit(qty_surface, (SCREEN_WIDTH - 100, y + 2))
        
        # --- SCROLL INDICATORS ---
        if start > 0:
            up_surface = self.font_info.render("▲ ...", True, (150, 150, 150))
            screen.blit(up_surface, (list_x, list_y - 20))
        
        if end < len(self.catalog):
            down_surface = self.font_info.render("▼ ...", True, (150, 150, 150))
            bottom_y = list_y + ITEMS_PER_PAGE * line_height
            screen.blit(down_surface, (list_x, bottom_y))
    
    
    def _draw_info(self, screen):
        """
        Draw information panel for selected item.
        Shows description and effect.
        """
        if len(self.catalog) == 0:
            return
        
        item = self.catalog[self.selection_index]
        
        # Info panel frame
        info_y = 380
        info_rect = pygame.Rect(50, info_y, SCREEN_WIDTH - 100, 120)
        pygame.draw.rect(screen, (40, 40, 65), info_rect)
        pygame.draw.rect(screen, (100, 100, 140), info_rect, 2)
        
        # Item name (larger)
        name_surface = self.font_item.render(item.name, True, (255, 255, 255))
        screen.blit(name_surface, (70, info_y + 10))
        
        # Description / effect
        description = self._get_item_description(item)
        desc_surface = self.font_info.render(description, True, (200, 200, 200))
        screen.blit(desc_surface, (70, info_y + 40))
        
        # Usable in combat / outside combat
        contexts = []
        if item.usable_in_combat:
            contexts.append("Combat")
        if item.usable_outside_combat:
            contexts.append("Hors combat")
        context_text = "Utilisable : " + ", ".join(contexts)
        ctx_surface = self.font_info.render(context_text, True, (150, 150, 180))
        screen.blit(ctx_surface, (70, info_y + 65))
    
    
    def _get_item_description(self, item):
        """Generate readable description of item effect."""
        if item.category == "heal":
            return f"Restaure {item.effect_value} PV"
        elif item.category == "pokeball":
            return f"Taux de capture : {item.effect_value}%"
        elif item.category == "boost":
            return f"Augmente une stat de {item.effect_value}% (1 combat)"
        elif item.category == "revive":
            return f"Réanime un Pokémon KO avec {item.effect_value} PV"
        elif item.category == "status":
            return "Soigne les altérations de statut"
        else:
            return "Objet spécial"
    
    
    def _draw_credits(self, screen):
        """Display player credits at bottom right."""
        player = self.game_manager.player
        text = f"Crédits : {player.credits}"
        surface = self.font_item.render(text, True, (255, 220, 50))
        x = SCREEN_WIDTH - surface.get_width() - 50
        screen.blit(surface, (x, 520))
    
    
    def _draw_message(self, screen):
        """
        Draw temporary message (purchase success/failure).
        Centered with semi-transparent background.
        """
        text_surface = self.font_message.render(
            self.temp_message, True, self.message_color)
        
        padding = 20
        bg_width = text_surface.get_width() + padding * 2
        bg_height = text_surface.get_height() + padding
        bg = pygame.Surface((bg_width, bg_height))
        bg.fill((0, 0, 0))
        bg.set_alpha(180)
        
        center_x = (SCREEN_WIDTH - bg_width) // 2
        center_y = (SCREEN_HEIGHT - bg_height) // 2
        
        screen.blit(bg, (center_x, center_y))
        screen.blit(text_surface, (center_x + padding, center_y + padding // 2))
    
    
    def _draw_controls(self, screen):
        """Draw controls hint at bottom."""
        text = "[↑↓] Naviguer  [Entrée] Acheter  [Échap] Quitter"
        surface = self.font_info.render(text, True, (120, 120, 120))
        x = (SCREEN_WIDTH - surface.get_width()) // 2
        screen.blit(surface, (x, SCREEN_HEIGHT - 40))