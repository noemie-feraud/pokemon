# =============================================================================
# STATE_TEAM_SCREEN.PY - TEAM SCREEN STATE
# =============================================================================
#
# This state displays the player's team.
# Accessible by pressing P during exploration.

import pygame
from states.state import State
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_TEAM_SIZE


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

MODE_NORMAL = "normal"
MODE_EXCHANGE = "exchange"

PANEL_X = 80
PANEL_Y = 50
PANEL_WIDTH = SCREEN_WIDTH - 160
PANEL_HEIGHT = SCREEN_HEIGHT - 100

LEFT_COLUMN_WIDTH = 350
RIGHT_COLUMN_WIDTH = PANEL_WIDTH - LEFT_COLUMN_WIDTH - 40

LINE_HEIGHT = 45
MESSAGE_DURATION = 1.5


# =============================================================================
# STATE TEAM SCREEN CLASS
# =============================================================================

class StateTeamScreen(State):
    """
    Transparent team screen. Allows viewing and reorganizing the team.
    Accessible by pressing P during exploration.
    """
    
    transparent = True
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager):
        """Initialize team screen state."""
        super().__init__(game_manager)
        
        self.player = game_manager.player
        self.team = self.player.team
        
        # --- FONTS ---
        self.font_title = pygame.font.Font(None, 34)
        self.font_pokemon = pygame.font.Font(None, 26)
        self.font_stats = pygame.font.Font(None, 22)
        self.font_info = pygame.font.Font(None, 20)
        
        # --- NAVIGATION ---
        self.selection_index = 0
        self.mode = MODE_NORMAL
        self.exchange_source = None    # index of first selected Pokemon
        
        # --- MESSAGE ---
        self.temp_message = None
        self.message_timer = 0
    
    
    # -------------------------------------------------------------------------
    # LIFECYCLE METHODS
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """Reset navigation when entering."""
        self.selection_index = 0
        self.mode = MODE_NORMAL
        self.exchange_source = None
    
    
    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """Handle player input based on mode."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            # --- QUIT (Escape) ---
            if event.key == pygame.K_ESCAPE:
                self.game_manager.state_manager.pop()
                return
            
            if self.mode == MODE_NORMAL:
                self._handle_normal(event)
            else:
                self._handle_exchange(event)
    
    
    def _handle_normal(self, event):
        """Handle inputs in normal mode."""
        
        # --- NAVIGATE ---
        if event.key == pygame.K_UP:
            self._navigate(-1)
        
        elif event.key == pygame.K_DOWN:
            self._navigate(1)
        
        # --- ENTER EXCHANGE MODE ---
        elif event.key == pygame.K_e:
            self._begin_exchange()
        
        # --- OPTIONAL: VIEW DETAILS ---
        elif event.key == pygame.K_RETURN:
            self._show_details()
    
    
    def _handle_exchange(self, event):
        """Handle inputs in exchange mode."""
        
        # --- CANCEL EXCHANGE ---
        if event.key == pygame.K_ESCAPE:
            self.mode = MODE_NORMAL
            self.exchange_source = None
            self._show_message("Échange annulé", (200, 200, 200))
            return
        
        # --- NAVIGATE ---
        if event.key == pygame.K_UP:
            self._navigate(-1)
        
        elif event.key == pygame.K_DOWN:
            self._navigate(1)
        
        # --- CONFIRM EXCHANGE ---
        elif event.key in [pygame.K_e, pygame.K_RETURN]:
            self._confirm_exchange()
    
    
    def _navigate(self, direction):
        """Move cursor in the list."""
        old = self.selection_index
        self.selection_index = max(0, min(MAX_TEAM_SIZE - 1, 
                                          self.selection_index + direction))
        
        # If moving beyond actual team size, clamp to last Pokemon
        if self.selection_index >= len(self.team.pokemon):
            self.selection_index = max(0, len(self.team.pokemon) - 1)
        
        if self.selection_index != old:
            self.game_manager.audio_manager.play_sfx("menu_select")
    
    
    def _begin_exchange(self):
        """Enter exchange mode and mark source Pokemon."""
        if len(self.team.pokemon) < 2:
            self._show_message("Pas assez de Pokémon pour échanger", (255, 150, 100))
            return
        
        self.mode = MODE_EXCHANGE
        self.exchange_source = self.selection_index
        self._show_message(
            f"Sélectionnez le Pokémon à échanger avec {self.team.pokemon[self.selection_index].name}",
            (200, 220, 255)
        )
    
    
    def _confirm_exchange(self):
        """Exchange the two selected Pokemon."""
        if self.exchange_source is None:
            self.mode = MODE_NORMAL
            return
        
        source = self.exchange_source
        target = self.selection_index
        
        if source == target:
            self._show_message("C'est le même Pokémon !", (255, 150, 100))
            return
        
        # Perform exchange
        success = self.team.swap(source, target)
        
        if success:
            self._show_message(
                f"{self.team.pokemon[target].name} et {self.team.pokemon[source].name} échangés",
                (100, 255, 100)
            )
        else:
            self._show_message("Échange impossible", (255, 100, 100))
        
        # Exit exchange mode
        self.mode = MODE_NORMAL
        self.exchange_source = None
    
    
    def _show_details(self):
        """Show detailed view (placeholder)."""
        pokemon = self.team.pokemon[self.selection_index]
        self._show_message(
            f"Détails de {pokemon.name} (à implémenter)",
            (150, 150, 150)
        )
    
    
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
        We draw a dark overlay then the team panel.
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
        title_surface = self.font_title.render("Équipe", True, (255, 255, 255))
        title_x = PANEL_X + 20
        screen.blit(title_surface, (title_x, PANEL_Y + 10))
        
        # --- TEAM LIST (left column) ---
        self._draw_team_list(screen)
        
        # --- DETAILS (right column) ---
        self._draw_details(screen)
        
        # --- MESSAGE ---
        if self.temp_message is not None:
            self._draw_message(screen)
        
        # --- CONTROLS ---
        self._draw_controls(screen)
    
    
    def _draw_team_list(self, screen):
        """Draw the team list with 6 slots."""
        list_x = PANEL_X + 20
        list_y = PANEL_Y + 50
        
        # Display all 6 slots
        for i in range(MAX_TEAM_SIZE):
            y = list_y + i * LINE_HEIGHT
            
            # --- LINE BACKGROUND ---
            if i == self.selection_index:
                if self.mode == MODE_NORMAL:
                    bg_color = (50, 50, 80)
                else:
                    bg_color = (80, 60, 30)  # exchange mode
                bg_rect = pygame.Rect(list_x - 5, y, LEFT_COLUMN_WIDTH - 20, LINE_HEIGHT - 2)
                pygame.draw.rect(screen, bg_color, bg_rect)
            
            # --- EXCHANGE MARKER ---
            if self.mode == MODE_EXCHANGE and i == self.exchange_source:
                # Circle marker around source Pokemon
                pygame.draw.circle(screen, (255, 220, 50), (list_x - 15, y + 15), 6)
            
            # --- CONTENT ---
            if i < len(self.team.pokemon):
                pokemon = self.team.pokemon[i]
                
                # Number + name
                prefix = "> " if i == self.selection_index else "  "
                text = f"{prefix}{i+1}. {pokemon.name}"
                
                if pokemon.is_ko():
                    text_color = (150, 80, 80)
                else:
                    text_color = (255, 255, 255)
                
                name_surface = self.font_pokemon.render(text, True, text_color)
                screen.blit(name_surface, (list_x + 20, y + 8))
                
                # Level
                level_surface = self.font_stats.render(
                    f"Nv.{pokemon.level}", True, (200, 200, 200))
                screen.blit(level_surface, (list_x + 180, y + 10))
                
                # Types
                types_text = "/".join(pokemon.types)
                type_surface = self.font_info.render(types_text, True, (150, 150, 180))
                screen.blit(type_surface, (list_x + 250, y + 12))
                
                # HP bar (small)
                if not pokemon.is_ko():
                    bar_x = list_x + 320
                    bar_y = y + 15
                    bar_width = 60
                    bar_height = 8
                    
                    hp_ratio = pokemon.current_hp / pokemon.max_hp
                    
                    if hp_ratio > 0.5:
                        hp_color = (100, 255, 100)
                    elif hp_ratio > 0.2:
                        hp_color = (255, 255, 50)
                    else:
                        hp_color = (255, 50, 50)
                    
                    # Bar background
                    pygame.draw.rect(screen, (40, 40, 40),
                                    (bar_x, bar_y, bar_width, bar_height))
                    # Fill
                    fill_width = int(bar_width * hp_ratio)
                    if fill_width > 0:
                        pygame.draw.rect(screen, hp_color,
                                        (bar_x, bar_y, fill_width, bar_height))
                else:
                    ko_surface = self.font_info.render("KO", True, (255, 80, 80))
                    screen.blit(ko_surface, (list_x + 340, y + 8))
            
            else:
                # Empty slot
                prefix = "  "
                text = f"{prefix}{i+1}. (vide)"
                empty_surface = self.font_pokemon.render(text, True, (80, 80, 80))
                screen.blit(empty_surface, (list_x + 20, y + 8))
    
    
    def _draw_details(self, screen):
        """Draw details panel for selected Pokemon."""
        if len(self.team.pokemon) == 0:
            return
        
        pokemon = self.team.pokemon[self.selection_index]
        
        details_x = PANEL_X + LEFT_COLUMN_WIDTH + 30
        details_y = PANEL_Y + 60
        
        # Details frame
        details_rect = pygame.Rect(
            details_x - 10, details_y - 10,
            RIGHT_COLUMN_WIDTH - 20, 200
        )
        pygame.draw.rect(screen, (40, 40, 60), details_rect)
        pygame.draw.rect(screen, (80, 80, 120), details_rect, 1)
        
        # Name (large)
        name_surface = self.font_title.render(pokemon.name, True, (255, 255, 255))
        screen.blit(name_surface, (details_x, details_y))
        
        # Type
        types_text = "Type: " + " / ".join(pokemon.types)
        type_surface = self.font_stats.render(types_text, True, (180, 200, 255))
        screen.blit(type_surface, (details_x, details_y + 30))
        
        # Stats
        stats_y = details_y + 60
        stats = [
            ("PV", f"{pokemon.current_hp}/{pokemon.max_hp}"),
            ("ATK", str(pokemon.attack)),
            ("DEF", str(pokemon.defense)),
            ("VIT", str(pokemon.speed))
        ]
        
        for i, (label, value) in enumerate(stats):
            y = stats_y + i * 25
            label_surface = self.font_stats.render(label + ":", True, (150, 150, 150))
            screen.blit(label_surface, (details_x, y))
            value_surface = self.font_stats.render(value, True, (255, 255, 255))
            screen.blit(value_surface, (details_x + 80, y))
        
        # Attacks
        attacks_y = stats_y + 110
        attacks_title = self.font_stats.render("Attaques:", True, (200, 200, 200))
        screen.blit(attacks_title, (details_x, attacks_y))
        
        for j, attack in enumerate(pokemon.attacks):
            y = attacks_y + 20 + j * 22
            attack_text = f"• {attack.name} ({attack.type})"
            attack_surface = self.font_info.render(attack_text, True, (170, 170, 200))
            screen.blit(attack_surface, (details_x + 10, y))
        
        # XP (if not KO)
        if not pokemon.is_ko():
            xp_y = attacks_y + 90
            xp_text = f"XP: {pokemon.current_xp}/{pokemon.xp_for_next_level}"
            xp_surface = self.font_info.render(xp_text, True, (150, 200, 255))
            screen.blit(xp_surface, (details_x, xp_y))
            
            # Small XP bar
            bar_x = details_x + 120
            bar_y = xp_y + 2
            bar_width = 100
            bar_height = 8
            xp_ratio = pokemon.current_xp / pokemon.xp_for_next_level
            
            pygame.draw.rect(screen, (40, 40, 40),
                            (bar_x, bar_y, bar_width, bar_height))
            fill_width = int(bar_width * xp_ratio)
            if fill_width > 0:
                pygame.draw.rect(screen, (100, 100, 255),
                                (bar_x, bar_y, fill_width, bar_height))
    
    
    def _draw_message(self, screen):
        """Draw temporary message."""
        text_surface = self.font_stats.render(
            self.temp_message, True, self.message_color)
        
        padding = 15
        bg_width = text_surface.get_width() + padding * 2
        bg_height = text_surface.get_height() + padding
        bg = pygame.Surface((bg_width, bg_height))
        bg.fill((0, 0, 0))
        bg.set_alpha(200)
        
        center_x = (SCREEN_WIDTH - bg_width) // 2
        center_y = SCREEN_HEIGHT - 150
        
        screen.blit(bg, (center_x, center_y))
        screen.blit(text_surface, (center_x + padding, center_y + padding // 2))
    
    
    def _draw_controls(self, screen):
        """Draw controls hint at bottom."""
        if self.mode == MODE_NORMAL:
            text = "[↑↓] Naviguer  [E] Échanger  [Entrée] Détails  [Échap] Fermer"
        else:
            text = "[↑↓] Choisir  [E/Entrée] Confirmer échange  [Échap] Annuler"
        
        surface = self.font_info.render(text, True, (120, 120, 120))
        x = (SCREEN_WIDTH - surface.get_width()) // 2
        screen.blit(surface, (x, PANEL_Y + PANEL_HEIGHT - 30))