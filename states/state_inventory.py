# =============================================================================
# STATE_INVENTORY.PY - INVENTORY STATE
# =============================================================================
#
# This state displays the player's inventory.
# Accessible by pressing I during exploration.

import pygame
from states.state import State
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

MODE_LIST = "list"
MODE_TARGET = "target"
MESSAGE_DURATION = 1.5

CATEGORY_ORDER = ["heal", "pokeball", "boost", "revive", "status"]
CATEGORY_NAMES = {
    "heal": "Soins",
    "pokeball": "Pokéballs",
    "boost": "Boosts",
    "revive": "Revive",
    "status": "Statut"
}

# Panel dimensions
PANEL_X = 80
PANEL_Y = 50
PANEL_WIDTH = SCREEN_WIDTH - 160
PANEL_HEIGHT = SCREEN_HEIGHT - 100
VISIBLE_ITEMS = 8


# =============================================================================
# STATE INVENTORY CLASS
# =============================================================================

class StateInventory(State):
    """
    Transparent inventory screen, pushed from exploration.
    Allows viewing and using items outside combat.
    """
    
    transparent = True
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager):
        """Initialize inventory state."""
        super().__init__(game_manager)
        
        self.player = game_manager.player
        
        # --- FONTS ---
        self.font_title = pygame.font.Font(None, 34)
        self.font_item = pygame.font.Font(None, 24)
        self.font_info = pygame.font.Font(None, 20)
        self.font_category = pygame.font.Font(None, 22)
        self.font_message = pygame.font.Font(None, 26)
        
        # --- BUILD DISPLAY LIST ---
        # We create a flat list containing either category separators or items.
        # Cursor only stops on items.
        self.lines = []
        self.item_indices = []    # indices in self.lines that are items
        self._build_list()
        
        # --- NAVIGATION ---
        self.cursor_pos = 0       # position in self.item_indices
        self.scroll_offset = 0
        
        # --- MODE ---
        self.mode = MODE_LIST
        self.selected_item = None
        self.target_index = 0
        
        # --- MESSAGE ---
        self.temp_message = None
        self.message_timer = 0
        self.message_color = (255, 255, 255)
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _build_list(self):
        """
        Build display list from inventory.
        Groups items by category with separators.
        
        Each entry is a dict:
            {"type": "category", "name": "Soins"}
            {"type": "item", "item": Item, "quantity": 5}
        
        Empty categories are omitted.
        """
        self.lines = []
        self.item_indices = []
        catalog = self.game_manager.item_catalog
        
        for category in CATEGORY_ORDER:
            # Get owned items in this category
            category_items = self.player.inventory.get_by_category(category, catalog)
            
            if len(category_items) == 0:
                continue
            
            # Separator
            self.lines.append({
                "type": "category",
                "name": CATEGORY_NAMES.get(category, category)
            })
            
            # Items
            for item, quantity in category_items:
                line_index = len(self.lines)
                self.lines.append({
                    "type": "item",
                    "item": item,
                    "quantity": quantity
                })
                self.item_indices.append(line_index)
    
    
    # -------------------------------------------------------------------------
    # LIFECYCLE METHODS
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """Rebuild list (may have changed after combat/purchase)."""
        self._build_list()
        self.cursor_pos = 0
        self.scroll_offset = 0
        self.mode = MODE_LIST
    
    
    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """Handle player input based on current mode."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            if self.mode == MODE_LIST:
                self._handle_list(event)
            elif self.mode == MODE_TARGET:
                self._handle_target(event)
    
    
    def _handle_list(self, event):
        """Handle inputs in list mode."""
        
        # --- QUIT ---
        if event.key == pygame.K_ESCAPE:
            self.game_manager.state_manager.pop()
            return
        
        # --- NAVIGATE ---
        if event.key == pygame.K_UP:
            self._navigate_list(-1)
        elif event.key == pygame.K_DOWN:
            self._navigate_list(1)
        
        # --- USE ITEM ---
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            self._attempt_use()
    
    
    def _navigate_list(self, direction):
        """
        Move cursor between items (skip separators).
        
        Args:
            direction: -1 (up) or +1 (down)
        """
        if len(self.item_indices) == 0:
            return
        
        old = self.cursor_pos
        self.cursor_pos = max(0, min(len(self.item_indices) - 1, self.cursor_pos + direction))
        
        if self.cursor_pos != old:
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        # Adjust scroll
        line_index = self.item_indices[self.cursor_pos]
        if line_index < self.scroll_offset:
            self.scroll_offset = max(0, line_index - 1)  # -1 to show separator above
        if line_index >= self.scroll_offset + VISIBLE_ITEMS:
            self.scroll_offset = line_index - VISIBLE_ITEMS + 1
    
    
    def _attempt_use(self):
        """Attempt to use the selected item."""
        if len(self.item_indices) == 0:
            return
        
        # Ignore if a message is displayed
        if self.temp_message is not None:
            return
        
        line_index = self.item_indices[self.cursor_pos]
        line = self.lines[line_index]
        item = line["item"]
        
        # Check if item is usable outside combat
        if not item.usable_outside_combat:
            self._show_message("Utilisable uniquement en combat", (255, 200, 100))
            return
        
        # Switch to target selection mode
        self.selected_item = item
        self.target_index = 0
        self.mode = MODE_TARGET
    
    
    def _handle_target(self, event):
        """Handle inputs in target selection mode."""
        
        # --- CANCEL ---
        if event.key == pygame.K_ESCAPE:
            self.mode = MODE_LIST
            self.selected_item = None
            return
        
        # --- NAVIGATE ---
        if event.key == pygame.K_UP:
            old = self.target_index
            self.target_index = max(0, self.target_index - 1)
            if self.target_index != old:
                self.game_manager.audio_manager.play_sfx("menu_select")
        
        elif event.key == pygame.K_DOWN:
            max_index = len(self.player.team.pokemon) - 1
            old = self.target_index
            self.target_index = min(max_index, self.target_index + 1)
            if self.target_index != old:
                self.game_manager.audio_manager.play_sfx("menu_select")
        
        # --- CONFIRM ---
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            self._apply_item()
    
    
    def _apply_item(self):
        """Apply selected item to target Pokemon."""
        pokemon = self.player.team.pokemon[self.target_index]
        item = self.selected_item
        
        # --- VALIDATION BY CATEGORY ---
        
        if item.category == "heal":
            if pokemon.is_ko():
                self._show_message(f"{pokemon.name} est KO, utilisez un Rappel", (255, 100, 100))
                return
            if pokemon.current_hp >= pokemon.max_hp:
                self._show_message(f"{pokemon.name} a déjà tous ses PV !", (255, 200, 100))
                return
        
        elif item.category == "revive":
            if not pokemon.is_ko():
                self._show_message(f"{pokemon.name} n'est pas KO !", (255, 100, 100))
                return
        
        elif item.category == "status":
            if not pokemon.has_status():
                self._show_message(f"{pokemon.name} n'a pas d'altération de statut", (255, 100, 100))
                return
        
        # --- APPLY EFFECT ---
        if item.category == "heal":
            hp_before = pokemon.current_hp
            pokemon.heal(item.effect_value)
            hp_healed = pokemon.current_hp - hp_before
            message = f"{pokemon.name} récupère {hp_healed} PV !"
        
        elif item.category == "revive":
            pokemon.revive(item.effect_value)
            message = f"{pokemon.name} est réanimé !"
        
        elif item.category == "status":
            pokemon.cure_status()
            message = f"{pokemon.name} est guéri !"
        
        else:
            message = f"{item.name} utilisé sur {pokemon.name} !"
        
        # --- REMOVE ITEM ---
        self.player.inventory.remove(item.id, 1)
        
        # --- SFX ---
        self.game_manager.audio_manager.play_sfx("heal")
        
        # --- REBUILD LIST ---
        self._build_list()
        
        # Adjust cursor if item disappeared
        if self.cursor_pos >= len(self.item_indices):
            self.cursor_pos = max(0, len(self.item_indices) - 1)
        
        # --- MESSAGE AND RETURN ---
        self._show_message(message, (100, 255, 100))
        self.mode = MODE_LIST
        self.selected_item = None
    
    
    # -------------------------------------------------------------------------
    # UTILITY
    # -------------------------------------------------------------------------
    
    def _show_message(self, text, color):
        """Display a temporary message."""
        self.temp_message = text
        self.message_color = color
        self.message_timer = MESSAGE_DURATION
    
    
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
        """
        Exploration is rendered below by state_manager (thanks to transparent=True).
        We draw a dark overlay then the inventory panel.
        """
        # --- DARK OVERLAY ---
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(120)
        screen.blit(overlay, (0, 0))
        
        # --- MAIN PANEL ---
        panel = pygame.Surface((PANEL_WIDTH, PANEL_HEIGHT))
        panel.fill((30, 30, 50))
        screen.blit(panel, (PANEL_X, PANEL_Y))
        pygame.draw.rect(screen, (100, 100, 140),
                        (PANEL_X, PANEL_Y, PANEL_WIDTH, PANEL_HEIGHT), 2)
        
        # --- TITLE ---
        title_surface = self.font_title.render("Inventaire", True, (255, 255, 255))
        title_x = PANEL_X + (PANEL_WIDTH - title_surface.get_width()) // 2
        screen.blit(title_surface, (title_x, PANEL_Y + 10))
        
        # --- ITEM LIST ---
        if len(self.lines) == 0:
            empty_surface = self.font_item.render("L'inventaire est vide", True, (100, 100, 100))
            screen.blit(empty_surface, (PANEL_X + 30, PANEL_Y + 80))
        else:
            self._draw_list(screen)
        
        # --- INFO PANEL (bottom of main panel) ---
        self._draw_item_info(screen)
        
        # --- TARGET SELECTION (if target mode) ---
        if self.mode == MODE_TARGET:
            self._draw_target_selection(screen)
        
        # --- CONTROLS ---
        self._draw_controls(screen)
        
        # --- MESSAGE ---
        if self.temp_message is not None:
            self._draw_message(screen)
    
    
    def _draw_list(self, screen):
        """Draw the item list."""
        list_x = PANEL_X + 20
        list_y = PANEL_Y + 50
        line_height = 30
        
        # Currently selected item (for highlighting)
        selected_line_index = -1
        if len(self.item_indices) > 0:
            selected_line_index = self.item_indices[self.cursor_pos]
        
        # Display visible lines
        start = self.scroll_offset
        end = min(start + VISIBLE_ITEMS, len(self.lines))
        
        for i in range(start, end):
            line = self.lines[i]
            y = list_y + (i - start) * line_height
            
            if line["type"] == "category":
                # --- SEPARATOR ---
                text = f"── {line['name']} ──"
                surface = self.font_category.render(text, True, (180, 180, 220))
                screen.blit(surface, (list_x, y + 5))
            
            elif line["type"] == "item":
                item = line["item"]
                quantity = line["quantity"]
                
                # Highlight if selected
                if i == selected_line_index and self.mode == MODE_LIST:
                    bg_rect = pygame.Rect(list_x - 5, y, PANEL_WIDTH - 30, line_height - 2)
                    pygame.draw.rect(screen, (50, 50, 80), bg_rect)
                
                # Cursor
                prefix = "> " if i == selected_line_index else "  "
                
                # Color based on usability outside combat
                if item.usable_outside_combat:
                    name_color = (255, 255, 255)
                else:
                    name_color = (120, 120, 120)
                
                # Name
                name_surface = self.font_item.render(
                    prefix + item.name, True, name_color)
                screen.blit(name_surface, (list_x, y + 3))
                
                # Quantity
                qty_text = f"x{quantity}"
                qty_surface = self.font_item.render(qty_text, True, (200, 200, 200))
                screen.blit(qty_surface, (list_x + 280, y + 3))
                
                # Effect summary or "Combat" tag
                if not item.usable_outside_combat:
                    tag = "[Combat]"
                    tag_color = (150, 100, 100)
                else:
                    tag = self._get_short_effect(item)
                    tag_color = (150, 200, 150)
                
                tag_surface = self.font_info.render(tag, True, tag_color)
                screen.blit(tag_surface, (list_x + 340, y + 6))
        
        # Scroll indicators
        if start > 0:
            surface = self.font_info.render("▲", True, (150, 150, 150))
            screen.blit(surface, (PANEL_X + PANEL_WIDTH - 30, list_y))
        if end < len(self.lines):
            surface = self.font_info.render("▼", True, (150, 150, 150))
            screen.blit(surface, (PANEL_X + PANEL_WIDTH - 30, list_y + VISIBLE_ITEMS * line_height))
    
    
    def _get_short_effect(self, item):
        """Return short effect description for an item."""
        if item.category == "heal":
            return f"+{item.effect_value} PV"
        elif item.category == "pokeball":
            return f"{item.effect_value}%"
        elif item.category == "boost":
            return f"+{item.effect_value}%"
        elif item.category == "revive":
            return "réanime"
        elif item.category == "status":
            return "guérit"
        else:
            return ""
    
    
    def _draw_item_info(self, screen):
        """Draw detailed info panel for selected item."""
        info_y = PANEL_Y + PANEL_HEIGHT - 80
        
        # Separator line
        pygame.draw.line(screen, (80, 80, 120),
                        (PANEL_X + 15, info_y),
                        (PANEL_X + PANEL_WIDTH - 15, info_y), 1)
        
        if len(self.item_indices) == 0:
            return
        
        line_index = self.item_indices[self.cursor_pos]
        item = self.lines[line_index]["item"]
        
        # Description
        description = self._get_full_description(item)
        surface = self.font_info.render(description, True, (200, 200, 200))
        screen.blit(surface, (PANEL_X + 25, info_y + 15))
        
        # Usage context
        contexts = []
        if item.usable_in_combat:
            contexts.append("Combat")
        if item.usable_outside_combat:
            contexts.append("Exploration")
        context_text = "Utilisable en : " + ", ".join(contexts) if contexts else "Non utilisable"
        context_surface = self.font_info.render(context_text, True, (150, 150, 180))
        screen.blit(context_surface, (PANEL_X + 25, info_y + 40))
    
    
    def _get_full_description(self, item):
        """Generate full item description."""
        if item.category == "heal":
            return f"Restaure {item.effect_value} PV d'un Pokémon. Ne fonctionne pas sur un KO."
        elif item.category == "pokeball":
            return f"Taux de capture de {item.effect_value}%. Utilisable sur Pokémon sauvage uniquement."
        elif item.category == "boost":
            return f"Augmente une statistique de {item.effect_value}% pour la durée d'un combat."
        elif item.category == "revive":
            return f"Réanime un Pokémon KO et restaure {item.effect_value} PV."
        elif item.category == "status":
            return "Soigne les altérations de statut (poison, paralysie, etc.)."
        else:
            return "Objet spécial."
    
    
    def _draw_target_selection(self, screen):
        """Draw sub-panel for target selection."""
        sub_width = 280
        sub_height = 300
        sub_x = PANEL_X + PANEL_WIDTH - sub_width - 10
        sub_y = PANEL_Y + 50
        
        # Background
        bg = pygame.Surface((sub_width, sub_height))
        bg.fill((25, 25, 45))
        screen.blit(bg, (sub_x, sub_y))
        pygame.draw.rect(screen, (255, 220, 50),
                        (sub_x, sub_y, sub_width, sub_height), 2)
        
        # Title
        title = f"Utiliser {self.selected_item.name} sur :"
        title_surface = self.font_info.render(title, True, (255, 220, 50))
        screen.blit(title_surface, (sub_x + 10, sub_y + 10))
        
        # Team list
        for i, pokemon in enumerate(self.player.team.pokemon):
            y = sub_y + 40 + i * 40
            
            # Highlight
            if i == self.target_index:
                bg_rect = pygame.Rect(sub_x + 5, y, sub_width - 10, 36)
                pygame.draw.rect(screen, (50, 50, 80), bg_rect)
            
            # Cursor
            prefix = "> " if i == self.target_index else "  "
            
            # Name and level
            text = f"{prefix}{pokemon.name}  Nv.{pokemon.level}"
            name_surface = self.font_item.render(text, True, (255, 255, 255))
            screen.blit(name_surface, (sub_x + 10, y + 5))
            
            # HP or KO
            if pokemon.is_ko():
                hp_text = "[KO]"
                hp_color = (255, 80, 80)
            else:
                hp_text = f"{pokemon.current_hp}/{pokemon.max_hp}"
                hp_color = (150, 255, 150)
            
            hp_surface = self.font_info.render(hp_text, True, hp_color)
            screen.blit(hp_surface, (sub_x + 200, y + 8))
        
        # Hint
        hint = "[Entrée] Confirmer  [Échap] Annuler"
        hint_surface = self.font_info.render(hint, True, (120, 120, 120))
        screen.blit(hint_surface, (sub_x + 10, sub_y + sub_height - 25))
    
    
    def _draw_controls(self, screen):
        """Draw controls hint."""
        if self.mode == MODE_LIST:
            text = "[↑↓] Naviguer  [Entrée] Utiliser  [Échap] Fermer"
        else:
            text = "[↑↓] Choisir Pokémon  [Entrée] Confirmer  [Échap] Annuler"
        
        surface = self.font_info.render(text, True, (120, 120, 120))
        x = PANEL_X + (PANEL_WIDTH - surface.get_width()) // 2
        screen.blit(surface, (x, PANEL_Y + PANEL_HEIGHT - 25))
    
    
    def _draw_message(self, screen):
        """Draw temporary message."""
        text_surface = self.font_message.render(
            self.temp_message, True, self.message_color)
        
        padding = 15
        bg_width = text_surface.get_width() + padding * 2
        bg_height = text_surface.get_height() + padding
        bg = pygame.Surface((bg_width, bg_height))
        bg.fill((0, 0, 0))
        bg.set_alpha(200)
        
        center_x = (SCREEN_WIDTH - bg_width) // 2
        center_y = SCREEN_HEIGHT // 2
        
        screen.blit(bg, (center_x, center_y))
        screen.blit(text_surface, (center_x + padding, center_y + padding // 2))