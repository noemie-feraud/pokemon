# =============================================================================
# STATE_POKEDEX.PY - POKEDEX STATE
# =============================================================================
#
# This state displays the Pokedex - the catalog of all Pokemon the player
# has encountered or captured during their game.

import pygame
from states.state import State
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TOTAL_POKEMON


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

PANEL_X = 60
PANEL_Y = 30
PANEL_WIDTH = SCREEN_WIDTH - 120
PANEL_HEIGHT = SCREEN_HEIGHT - 60
VISIBLE_LINES = 8


# =============================================================================
# STATE POKEDEX CLASS
# =============================================================================

class StatePokedex(State):
    """
    Pokedex screen. Transparent overlay showing all Pokemon
    encountered and captured. Navigation only, no actions.
    """
    
    transparent = True
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager):
        """Initialize Pokedex state."""
        super().__init__(game_manager)
        
        self.player = game_manager.player
        
        # --- FONTS ---
        self.font_title = pygame.font.Font(None, 34)
        self.font_counter = pygame.font.Font(None, 22)
        self.font_entry = pygame.font.Font(None, 24)
        self.font_detail = pygame.font.Font(None, 22)
        self.font_info = pygame.font.Font(None, 20)
        
        # --- DATA ---
        # Load all Pokemon from catalog (all 54)
        self.pokemon_data = game_manager.pokemon_data
        self.all_ids = self.pokemon_data.get_all_ids()    # [1, 2, 3, ..., 54]
        
        # --- NAVIGATION ---
        self.selection_index = 0
        self.scroll_offset = 0
    
    
    # -------------------------------------------------------------------------
    # LIFECYCLE METHODS
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """No special music."""
        pass
    
    
    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """Handle player input."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            # --- QUIT ---
            if event.key == pygame.K_ESCAPE:
                self.game_manager.state_manager.pop()
                return
            
            # --- NAVIGATE ---
            if event.key == pygame.K_UP:
                self._navigate(-1)
            elif event.key == pygame.K_DOWN:
                self._navigate(1)
    
    
    def _navigate(self, direction):
        """
        Move cursor in the list.
        
        Args:
            direction: -1 (up) or +1 (down)
        """
        old = self.selection_index
        self.selection_index = max(0, min(len(self.all_ids) - 1, self.selection_index + direction))
        
        if self.selection_index != old:
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        # Adjust scroll
        if self.selection_index < self.scroll_offset:
            self.scroll_offset = self.selection_index
        if self.selection_index >= self.scroll_offset + VISIBLE_LINES:
            self.scroll_offset = self.selection_index - VISIBLE_LINES + 1
    
    
    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    
    def update(self, dt):
        """Nothing to update."""
        pass
    
    
    # -------------------------------------------------------------------------
    # RENDERING
    # -------------------------------------------------------------------------
    
    def render(self, screen):
        """
        Draw the Pokedex screen.
        Exploration is rendered below by state_manager (transparent=True).
        """
        # --- DARK OVERLAY ---
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(120)
        screen.blit(overlay, (0, 0))
        
        # --- MAIN PANEL ---
        panel = pygame.Surface((PANEL_WIDTH, PANEL_HEIGHT))
        panel.fill((25, 28, 48))
        screen.blit(panel, (PANEL_X, PANEL_Y))
        pygame.draw.rect(screen, (100, 100, 140),
                        (PANEL_X, PANEL_Y, PANEL_WIDTH, PANEL_HEIGHT), 2)
        
        # --- HEADER (title + counters) ---
        self._draw_header(screen)
        
        # --- LIST ---
        self._draw_list(screen)
        
        # --- DETAILS ---
        self._draw_details(screen)
        
        # --- CONTROLS ---
        self._draw_controls(screen)
    
    
    def _draw_header(self, screen):
        """Draw title and encounter counters."""
        # Title
        title_surface = self.font_title.render("Pokédex", True, (255, 255, 255))
        screen.blit(title_surface, (PANEL_X + 20, PANEL_Y + 10))
        
        # Counters
        pokedex = self.player.pokedex
        total = TOTAL_POKEMON    # 54
        
        seen_text = f"Vus: {pokedex.get_total_seen()}/{total}"
        captured_text = f"Capturés: {pokedex.get_total_captured()}/{total}"
        
        seen_surface = self.font_counter.render(seen_text, True, (180, 220, 255))
        captured_surface = self.font_counter.render(captured_text, True, (255, 220, 100))
        
        screen.blit(seen_surface, (PANEL_X + PANEL_WIDTH - 320, PANEL_Y + 15))
        screen.blit(captured_surface, (PANEL_X + PANEL_WIDTH - 160, PANEL_Y + 15))
        
        # Global progress bar
        bar_x = PANEL_X + 20
        bar_y = PANEL_Y + 42
        bar_width = PANEL_WIDTH - 40
        bar_height = 6
        
        ratio = pokedex.get_total_seen() / total if total > 0 else 0
        
        pygame.draw.rect(screen, (40, 40, 60),
                        (bar_x, bar_y, bar_width, bar_height))
        fill_width = int(bar_width * ratio)
        if fill_width > 0:
            pygame.draw.rect(screen, (100, 180, 255),
                            (bar_x, bar_y, fill_width, bar_height))
    
    
    def _draw_list(self, screen):
        """
        Draw the list of all 54 Pokemon.
        
        Each line:
            #001 ● Flamèche          Feu         ★
            #005   ?????????         ???
        
        ● = seen, ★ = captured, nothing = not encountered
        """
        list_x = PANEL_X + 15
        list_y = PANEL_Y + 58
        line_height = 30
        pokedex = self.player.pokedex
        
        start = self.scroll_offset
        end = min(start + VISIBLE_LINES, len(self.all_ids))
        
        for i in range(start, end):
            pokemon_id = self.all_ids[i]
            y = list_y + (i - start) * line_height
            is_seen = pokedex.is_seen(pokemon_id)
            is_captured = pokedex.is_captured(pokemon_id)
            
            # --- HIGHLIGHT ---
            if i == self.selection_index:
                bg_rect = pygame.Rect(list_x - 5, y, PANEL_WIDTH - 20, line_height - 2)
                pygame.draw.rect(screen, (45, 50, 75), bg_rect)
            
            # --- NUMBER ---
            num_text = f"#{pokemon_id:03d}"
            num_color = (200, 200, 200) if is_seen else (80, 80, 80)
            num_surface = self.font_entry.render(num_text, True, num_color)
            screen.blit(num_surface, (list_x, y + 3))
            
            # --- STATUS ICON ---
            if is_captured:
                icon = "●"
                icon_color = (100, 255, 100)
            elif is_seen:
                icon = "○"
                icon_color = (180, 180, 255)
            else:
                icon = " "
                icon_color = (80, 80, 80)
            
            icon_surface = self.font_entry.render(icon, True, icon_color)
            screen.blit(icon_surface, (list_x + 55, y + 3))
            
            # --- NAME ---
            if is_seen:
                pokemon_info = self.pokemon_data.get_info(pokemon_id)
                name = pokemon_info["name_custom"]
                name_color = (255, 255, 255)
            else:
                name = "?????????"
                name_color = (70, 70, 70)
            
            name_surface = self.font_entry.render(name, True, name_color)
            screen.blit(name_surface, (list_x + 80, y + 3))
            
            # --- TYPE ---
            if is_seen:
                types_text = " / ".join(pokemon_info["types"])
                type_color = (180, 200, 220)
            else:
                types_text = "???"
                type_color = (70, 70, 70)
            
            type_surface = self.font_info.render(types_text, True, type_color)
            screen.blit(type_surface, (list_x + 300, y + 5))
            
            # --- CAPTURED STAR ---
            if is_captured:
                star_surface = self.font_entry.render("★", True, (255, 220, 50))
                screen.blit(star_surface, (list_x + PANEL_WIDTH - 60, y + 3))
        
        # --- SCROLL INDICATORS ---
        if start > 0:
            surface = self.font_info.render("▲ ...", True, (150, 150, 150))
            screen.blit(surface, (list_x, list_y - 15))
        if end < len(self.all_ids):
            surface = self.font_info.render("▼ ...", True, (150, 150, 150))
            screen.blit(surface, (list_x, list_y + VISIBLE_LINES * line_height))
    
    
    def _draw_details(self, screen):
        """
        Draw details panel for selected Pokemon.
        
        If Pokemon is not seen → "Pokemon inconnu"
        If seen → name, types, base stats, evolution chain
        """
        detail_y = PANEL_Y + PANEL_HEIGHT - 175
        detail_height = 140
        
        # Frame
        detail_rect = pygame.Rect(PANEL_X + 10, detail_y,
                                  PANEL_WIDTH - 20, detail_height)
        pygame.draw.rect(screen, (30, 35, 55), detail_rect)
        pygame.draw.rect(screen, (80, 80, 120), detail_rect, 1)
        
        pokemon_id = self.all_ids[self.selection_index]
        pokedex = self.player.pokedex
        
        if not pokedex.is_seen(pokemon_id):
            # Not encountered
            surface = self.font_detail.render(
                f"Pokémon #{pokemon_id:03d} — Pas encore rencontré",
                True, (100, 100, 100))
            screen.blit(surface, (PANEL_X + 30, detail_y + 55))
            return
        
        # Seen → show details
        info = self.pokemon_data.get_info(pokemon_id)
        col_x = PANEL_X + 25
        col2_x = PANEL_X + PANEL_WIDTH // 2 + 10
        
        # --- LINE 1: ID, Name, Types ---
        id_text = f"#{pokemon_id:03d} {info['name_custom']} — Type: {' / '.join(info['types'])}"
        id_surface = self.font_detail.render(id_text, True, (255, 255, 255))
        screen.blit(id_surface, (col_x, detail_y + 10))
        
        # --- LINE 2: Base stats ---
        stats = info["base_stats"]
        stats_text = f"PV: {stats['hp']}   ATK: {stats['attack']}   DEF: {stats['defense']}"
        stats_surface = self.font_detail.render(stats_text, True, (200, 220, 255))
        screen.blit(stats_surface, (col_x, detail_y + 38))
        
        # --- LINE 3: Day/Night affinity ---
        day_night = info.get("day_night", "diurne")
        if day_night == "diurne":
            dn_text = "Affinité: Diurne (bonus le jour)"
            dn_color = (255, 220, 100)
        else:
            dn_text = "Affinité: Nocturne (bonus la nuit)"
            dn_color = (150, 150, 255)
        
        dn_surface = self.font_info.render(dn_text, True, dn_color)
        screen.blit(dn_surface, (col_x, detail_y + 63))
        
        # --- LINE 4: Evolution ---
        evolution = info.get("evolution", None)
        if evolution is not None and evolution.get("to") is not None:
            evo_id = evolution["to"]
            evo_info = self.pokemon_data.get_info(evo_id)
            evo_level = evolution.get("level", "?")
            
            # If evolution is seen, show name, else "???"
            if pokedex.is_seen(evo_id):
                evo_name = evo_info["name_custom"]
            else:
                evo_name = "???"
            
            evo_text = f"Évolue en {evo_name} au niveau {evo_level}"
        else:
            evo_text = "Dernier stade — Pas d'évolution"
        
        evo_surface = self.font_info.render(evo_text, True, (180, 180, 200))
        screen.blit(evo_surface, (col_x, detail_y + 85))
        
        # --- CAPTURED STATUS ---
        if pokedex.is_captured(pokemon_id):
            status_text = "★ Capturé"
            status_color = (255, 220, 50)
        else:
            status_text = "○ Vu uniquement"
            status_color = (180, 180, 220)
        
        status_surface = self.font_detail.render(status_text, True, status_color)
        screen.blit(status_surface, (col2_x, detail_y + 85))
        
        # --- STAGE ---
        stage = info.get("stade", 1)
        stage_text = f"Stade {stage}"
        stage_surface = self.font_info.render(stage_text, True, (150, 170, 200))
        screen.blit(stage_surface, (col2_x, detail_y + 38))
    
    
    def _draw_controls(self, screen):
        """Draw controls hint."""
        text = "[↑↓] Naviguer  [Échap] Fermer"
        surface = self.font_info.render(text, True, (120, 120, 120))
        x = PANEL_X + (PANEL_WIDTH - surface.get_width()) // 2
        screen.blit(surface, (x, PANEL_Y + PANEL_HEIGHT - 25))