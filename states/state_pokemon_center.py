# =============================================================================
# STATE_POKEMON_CENTER.PY - POKEMON CENTER STATE
# =============================================================================
#
# This state displays the Pokemon Center screen where the player can
# exchange Pokemon between their team and storage.

import pygame
from states.state import State
from economy.pokemon_center import PokemonCenter
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

PANEL_TEAM = "team"
PANEL_STORAGE = "storage"
MODE_NORMAL = "normal"
MODE_EXCHANGE = "exchange"
MESSAGE_DURATION = 1.5
POKEMON_PER_PAGE = 6          # visible in storage panel


# =============================================================================
# STATE POKEMON CENTER CLASS
# =============================================================================

class StatePokemonCenter(State):
    """
    Pokemon Center screen. Allows team/storage management.
    Non-transparent full screen.
    """
    
    transparent = False
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager):
        """Initialize Pokemon Center state."""
        super().__init__(game_manager)
        
        # --- FONTS ---
        self.font_title = pygame.font.Font(None, 36)
        self.font_pokemon = pygame.font.Font(None, 24)
        self.font_info = pygame.font.Font(None, 20)
        self.font_message = pygame.font.Font(None, 28)
        
        # --- LOGIC ---
        self.pokemon_center = PokemonCenter(game_manager.player)
        self.player = game_manager.player
        
        # --- NAVIGATION ---
        self.active_panel = PANEL_TEAM
        self.team_index = 0
        self.storage_index = 0
        self.storage_scroll = 0    # scroll for storage (can be long)
        
        # --- MODE ---
        self.mode = MODE_NORMAL
        self.exchange_source_panel = None
        self.exchange_source_index = None
        
        # --- MESSAGE ---
        self.temp_message = None
        self.message_timer = 0
        self.message_color = (255, 255, 255)
    
    
    # -------------------------------------------------------------------------
    # LIFECYCLE METHODS
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """No special music, keep zone music."""
        pass
    
    
    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """Handle player input based on current mode."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            if self.mode == MODE_NORMAL:
                self._handle_normal(event)
            elif self.mode == MODE_EXCHANGE:
                self._handle_exchange(event)
    
    
    # -------------------------------------------------------------------------
    # NORMAL MODE HANDLING
    # -------------------------------------------------------------------------
    
    def _handle_normal(self, event):
        """Handle inputs in normal mode."""
        
        # --- QUIT ---
        if event.key == pygame.K_ESCAPE:
            self.game_manager.state_manager.pop()
            return
        
        # --- SWITCH PANELS ---
        if event.key == pygame.K_LEFT:
            self.active_panel = PANEL_TEAM
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        elif event.key == pygame.K_RIGHT:
            self.active_panel = PANEL_STORAGE
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        # --- NAVIGATE IN PANEL ---
        elif event.key == pygame.K_UP:
            self._navigate_panel(-1)
        
        elif event.key == pygame.K_DOWN:
            self._navigate_panel(1)
        
        # --- DEPOSIT (D) ---
        elif event.key == pygame.K_d:
            self._attempt_deposit()
        
        # --- WITHDRAW (R) ---
        elif event.key == pygame.K_r:
            self._attempt_withdraw()
        
        # --- EXCHANGE (E) ---
        elif event.key == pygame.K_e:
            self._begin_exchange()
    
    
    # -------------------------------------------------------------------------
    # EXCHANGE MODE HANDLING
    # -------------------------------------------------------------------------
    
    def _handle_exchange(self, event):
        """Handle inputs in exchange mode."""
        
        # --- CANCEL ---
        if event.key == pygame.K_ESCAPE:
            self.mode = MODE_NORMAL
            self.exchange_source_panel = None
            self.exchange_source_index = None
            return
        
        # --- SWITCH PANELS ---
        if event.key == pygame.K_LEFT:
            self.active_panel = PANEL_TEAM
        elif event.key == pygame.K_RIGHT:
            self.active_panel = PANEL_STORAGE
        
        # --- NAVIGATE ---
        elif event.key == pygame.K_UP:
            self._navigate_panel(-1)
        elif event.key == pygame.K_DOWN:
            self._navigate_panel(1)
        
        # --- CONFIRM EXCHANGE ---
        elif event.key in [pygame.K_e, pygame.K_SPACE, pygame.K_RETURN]:
            self._confirm_exchange()
    
    
    # -------------------------------------------------------------------------
    # NAVIGATION
    # -------------------------------------------------------------------------
    
    def _navigate_panel(self, direction):
        """Move cursor in current panel."""
        if self.active_panel == PANEL_TEAM:
            size = len(self.player.team.pokemon)
            if size == 0:
                return
            old = self.team_index
            self.team_index = max(0, min(size - 1, self.team_index + direction))
            if self.team_index != old:
                self.game_manager.audio_manager.play_sfx("menu_select")
        
        else:  # STORAGE
            size = len(self.player.storage.pokemon)
            if size == 0:
                return
            old = self.storage_index
            self.storage_index = max(0, min(size - 1, self.storage_index + direction))
            if self.storage_index != old:
                self.game_manager.audio_manager.play_sfx("menu_select")
            
            # Adjust scroll
            if self.storage_index < self.storage_scroll:
                self.storage_scroll = self.storage_index
            if self.storage_index >= self.storage_scroll + POKEMON_PER_PAGE:
                self.storage_scroll = self.storage_index - POKEMON_PER_PAGE + 1
    
    
    # -------------------------------------------------------------------------
    # DEPOSIT (team → storage)
    # -------------------------------------------------------------------------
    
    def _attempt_deposit(self):
        """Attempt to deposit selected Pokemon from team to storage."""
        if self.active_panel != PANEL_TEAM:
            return
        if len(self.player.team.pokemon) == 0:
            return
        
        pokemon = self.player.team.pokemon[self.team_index]
        
        # Pre-check
        if not self.pokemon_center.can_deposit(pokemon):
            self._show_message(
                "Impossible ! Vous devez garder au moins 1 Pokémon valide.",
                (255, 100, 100)
            )
            return
        
        # Perform deposit
        result = self.pokemon_center.deposit(pokemon)
        
        if result["success"]:
            self._show_message(
                f"{pokemon.name} déposé au stockage.",
                (100, 255, 100)
            )
            # Adjust cursor if needed
            if self.team_index >= len(self.player.team.pokemon):
                self.team_index = max(0, len(self.player.team.pokemon) - 1)
        else:
            self._show_message(result["reason"], (255, 100, 100))
    
    
    # -------------------------------------------------------------------------
    # WITHDRAW (storage → team)
    # -------------------------------------------------------------------------
    
    def _attempt_withdraw(self):
        """Attempt to withdraw selected Pokemon from storage to team."""
        if self.active_panel != PANEL_STORAGE:
            return
        if len(self.player.storage.pokemon) == 0:
            return
        
        pokemon = self.player.storage.pokemon[self.storage_index]
        
        # Pre-check
        if not self.pokemon_center.can_withdraw(pokemon):
            self._show_message(
                "L'équipe est pleine ! (max 6)",
                (255, 100, 100)
            )
            return
        
        # Perform withdraw
        result = self.pokemon_center.withdraw(pokemon)
        
        if result["success"]:
            self._show_message(
                f"{pokemon.name} rejoint l'équipe !",
                (100, 255, 100)
            )
            # Adjust cursor
            if self.storage_index >= len(self.player.storage.pokemon):
                self.storage_index = max(0, len(self.player.storage.pokemon) - 1)
        else:
            self._show_message(result["reason"], (255, 100, 100))
    
    
    # -------------------------------------------------------------------------
    # EXCHANGE (swap team ↔ storage)
    # -------------------------------------------------------------------------
    
    def _begin_exchange(self):
        """Start exchange mode by marking source Pokemon."""
        if self.active_panel == PANEL_TEAM:
            if len(self.player.team.pokemon) == 0:
                return
            self.exchange_source_panel = PANEL_TEAM
            self.exchange_source_index = self.team_index
        else:
            if len(self.player.storage.pokemon) == 0:
                return
            self.exchange_source_panel = PANEL_STORAGE
            self.exchange_source_index = self.storage_index
        
        # Switch to other panel
        if self.active_panel == PANEL_TEAM:
            self.active_panel = PANEL_STORAGE
        else:
            self.active_panel = PANEL_TEAM
        
        self.mode = MODE_EXCHANGE
        self._show_message(
            "Choisissez le Pokémon à échanger, puis [E] pour confirmer",
            (200, 200, 255)
        )
    
    
    def _confirm_exchange(self):
        """Confirm and perform the exchange."""
        # Determine the two Pokemon
        if self.exchange_source_panel == PANEL_TEAM:
            team_pokemon = self.player.team.pokemon[self.exchange_source_index]
            if self.active_panel != PANEL_STORAGE:
                self._show_message("Sélectionnez un Pokémon du stockage", (255, 200, 100))
                return
            if len(self.player.storage.pokemon) == 0:
                return
            storage_pokemon = self.player.storage.pokemon[self.storage_index]
        
        else:  # source is storage
            storage_pokemon = self.player.storage.pokemon[self.exchange_source_index]
            if self.active_panel != PANEL_TEAM:
                self._show_message("Sélectionnez un Pokémon de l'équipe", (255, 200, 100))
                return
            if len(self.player.team.pokemon) == 0:
                return
            team_pokemon = self.player.team.pokemon[self.team_index]
        
        # Pre-check
        if not self.pokemon_center.can_exchange(team_pokemon, storage_pokemon):
            self._show_message(
                "Échange impossible ! L'équipe doit garder 1 Pokémon valide.",
                (255, 100, 100)
            )
            self.mode = MODE_NORMAL
            self.exchange_source_panel = None
            return
        
        # Perform exchange
        result = self.pokemon_center.exchange(team_pokemon, storage_pokemon)
        
        if result["success"]:
            self._show_message(
                f"{team_pokemon.name} et {storage_pokemon.name} ont été échangés !",
                (100, 255, 100)
            )
        else:
            self._show_message(result["reason"], (255, 100, 100))
        
        # Back to normal mode
        self.mode = MODE_NORMAL
        self.exchange_source_panel = None
        self.exchange_source_index = None
    
    
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
        """Draw the Pokemon Center screen."""
        screen.fill((25, 30, 45))
        
        self._draw_title(screen)
        self._draw_team_panel(screen)
        self._draw_storage_panel(screen)
        self._draw_separator(screen)
        self._draw_selected_info(screen)
        self._draw_controls(screen)
        
        if self.temp_message is not None:
            self._draw_message(screen)
    
    
    def _draw_title(self, screen):
        """Draw screen title."""
        surface = self.font_title.render("Centre Pokémon — Gestion", True, (255, 255, 255))
        x = (SCREEN_WIDTH - surface.get_width()) // 2
        screen.blit(surface, (x, 15))
    
    
    def _draw_team_panel(self, screen):
        """Draw left panel (team)."""
        # Header
        title_color = (255, 220, 50) if self.active_panel == PANEL_TEAM else (150, 150, 150)
        title_text = f"Équipe ({len(self.player.team.pokemon)}/6)"
        title_surface = self.font_pokemon.render(title_text, True, title_color)
        screen.blit(title_surface, (30, 55))
        
        panel_x = 20
        panel_y = 80
        line_height = 40
        
        for i in range(6):
            y = panel_y + i * line_height
            
            # Selection highlight
            if self.active_panel == PANEL_TEAM and i == self.team_index:
                bg = pygame.Rect(panel_x, y, SCREEN_WIDTH // 2 - 30, line_height - 4)
                pygame.draw.rect(screen, (50, 50, 80), bg)
            
            # Exchange marker
            if self.mode == MODE_EXCHANGE and self.exchange_source_panel == PANEL_TEAM and i == self.exchange_source_index:
                bg = pygame.Rect(panel_x, y, SCREEN_WIDTH // 2 - 30, line_height - 4)
                pygame.draw.rect(screen, (80, 60, 30), bg)
            
            if i < len(self.player.team.pokemon):
                pokemon = self.player.team.pokemon[i]
                self._draw_pokemon_line(screen, pokemon, panel_x + 10, y, i + 1)
            else:
                text = f"{i+1}. (vide)"
                surface = self.font_pokemon.render(text, True, (80, 80, 80))
                screen.blit(surface, (panel_x + 10, y + 5))
    
    
    def _draw_storage_panel(self, screen):
        """Draw right panel (storage)."""
        panel_x = SCREEN_WIDTH // 2 + 10
        
        # Header
        title_color = (255, 220, 50) if self.active_panel == PANEL_STORAGE else (150, 150, 150)
        title_text = f"Stockage ({len(self.player.storage.pokemon)})"
        title_surface = self.font_pokemon.render(title_text, True, title_color)
        screen.blit(title_surface, (panel_x + 10, 55))
        
        panel_y = 80
        line_height = 40
        storage_list = self.player.storage.pokemon
        
        if len(storage_list) == 0:
            surface = self.font_pokemon.render("(vide)", True, (80, 80, 80))
            screen.blit(surface, (panel_x + 20, panel_y + 10))
            return
        
        start = self.storage_scroll
        end = min(start + POKEMON_PER_PAGE, len(storage_list))
        
        for i in range(start, end):
            pokemon = storage_list[i]
            y = panel_y + (i - start) * line_height
            
            # Selection highlight
            if self.active_panel == PANEL_STORAGE and i == self.storage_index:
                bg = pygame.Rect(panel_x, y, SCREEN_WIDTH // 2 - 30, line_height - 4)
                pygame.draw.rect(screen, (50, 50, 80), bg)
            
            # Exchange marker
            if self.mode == MODE_EXCHANGE and self.exchange_source_panel == PANEL_STORAGE and i == self.exchange_source_index:
                bg = pygame.Rect(panel_x, y, SCREEN_WIDTH // 2 - 30, line_height - 4)
                pygame.draw.rect(screen, (80, 60, 30), bg)
            
            self._draw_pokemon_line(screen, pokemon, panel_x + 10, y, i + 1)
        
        # Scroll indicators
        if start > 0:
            surface = self.font_info.render("▲ ...", True, (150, 150, 150))
            screen.blit(surface, (panel_x + 10, panel_y - 18))
        if end < len(storage_list):
            surface = self.font_info.render("▼ ...", True, (150, 150, 150))
            screen.blit(surface, (panel_x + 10, panel_y + POKEMON_PER_PAGE * line_height))
    
    
    def _draw_pokemon_line(self, screen, pokemon, x, y, number):
        """Draw a single line summarizing a Pokemon."""
        # Name and level
        text = f"{number}. {pokemon.name} Nv.{pokemon.level}"
        name_surface = self.font_pokemon.render(text, True, (255, 255, 255))
        screen.blit(name_surface, (x, y + 5))
        
        # Mini HP bar
        bar_x = x + 250
        bar_y = y + 10
        bar_width = 80
        bar_height = 10
        
        hp_ratio = pokemon.current_hp / pokemon.max_hp if pokemon.max_hp > 0 else 0
        
        # Bar color
        if pokemon.is_ko():
            hp_color = (100, 100, 100)
        elif hp_ratio > 0.5:
            hp_color = (100, 255, 100)
        elif hp_ratio > 0.2:
            hp_color = (255, 255, 50)
        else:
            hp_color = (255, 50, 50)
        
        # Bar background
        pygame.draw.rect(screen, (60, 60, 60),
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Fill
        fill_width = int(bar_width * hp_ratio)
        if fill_width > 0:
            pygame.draw.rect(screen, hp_color,
                            (bar_x, bar_y, fill_width, bar_height))
        
        # HP text
        hp_text = f"{pokemon.current_hp}/{pokemon.max_hp}"
        hp_surface = self.font_info.render(hp_text, True, (200, 200, 200))
        screen.blit(hp_surface, (bar_x + bar_width + 5, y + 7))
        
        # KO tag
        if pokemon.is_ko():
            ko_surface = self.font_info.render("[KO]", True, (255, 80, 80))
            screen.blit(ko_surface, (bar_x + bar_width + 60, y + 7))
    
    
    def _draw_separator(self, screen):
        """Draw vertical separator between panels."""
        x = SCREEN_WIDTH // 2
        pygame.draw.line(screen, (80, 80, 120), (x, 50), (x, 330), 2)
    
    
    def _draw_selected_info(self, screen):
        """Draw detailed info panel for selected Pokemon."""
        # Find selected Pokemon
        pokemon = None
        
        if self.active_panel == PANEL_TEAM:
            if self.team_index < len(self.player.team.pokemon):
                pokemon = self.player.team.pokemon[self.team_index]
        else:
            if self.storage_index < len(self.player.storage.pokemon):
                pokemon = self.player.storage.pokemon[self.storage_index]
        
        # Info panel frame
        info_y = 345
        info_rect = pygame.Rect(20, info_y, SCREEN_WIDTH - 40, 130)
        pygame.draw.rect(screen, (35, 40, 55), info_rect)
        pygame.draw.rect(screen, (80, 80, 120), info_rect, 2)
        
        if pokemon is None:
            surface = self.font_pokemon.render("Aucun Pokémon sélectionné", True, (100, 100, 100))
            screen.blit(surface, (40, info_y + 50))
            return
        
        # Name, level, type
        types_str = "/".join(pokemon.types)
        name_text = f"{pokemon.name} — Nv.{pokemon.level} — Type: {types_str}"
        name_surface = self.font_pokemon.render(name_text, True, (255, 255, 255))
        screen.blit(name_surface, (40, info_y + 10))
        
        # Stats
        stats_text = f"PV: {pokemon.current_hp}/{pokemon.max_hp}  |  ATK: {pokemon.attack}  |  DEF: {pokemon.defense}  |  VIT: {pokemon.speed}"
        stats_surface = self.font_info.render(stats_text, True, (200, 200, 200))
        screen.blit(stats_surface, (40, info_y + 40))
        
        # Attacks
        attack_names = [a.name for a in pokemon.attacks]
        attacks_text = "Attaques: " + ", ".join(attack_names)
        attacks_surface = self.font_info.render(attacks_text, True, (180, 180, 220))
        screen.blit(attacks_surface, (40, info_y + 65))
        
        # XP (if in team)
        if self.active_panel == PANEL_TEAM:
            xp_text = f"XP: {pokemon.current_xp}/{pokemon.xp_for_next_level}"
            xp_surface = self.font_info.render(xp_text, True, (150, 200, 255))
            screen.blit(xp_surface, (40, info_y + 90))
    
    
    def _draw_controls(self, screen):
        """Draw controls hint at bottom."""
        if self.mode == MODE_NORMAL:
            text = "[←→] Panneau  [↑↓] Naviguer  [D] Déposer  [R] Retirer  [E] Échanger  [Échap] Quitter"
        else:
            text = "[←→] Panneau  [↑↓] Naviguer  [E/Entrée] Confirmer  [Échap] Annuler"
        
        surface = self.font_info.render(text, True, (120, 120, 120))
        x = (SCREEN_WIDTH - surface.get_width()) // 2
        screen.blit(surface, (x, SCREEN_HEIGHT - 35))
    
    
    def _draw_message(self, screen):
        """Draw temporary message (same pattern as shop)."""
        text_surface = self.font_message.render(
            self.temp_message, True, self.message_color)
        
        padding = 20
        bg_width = text_surface.get_width() + padding * 2
        bg_height = text_surface.get_height() + padding
        bg = pygame.Surface((bg_width, bg_height))
        bg.fill((0, 0, 0))
        bg.set_alpha(200)
        
        center_x = (SCREEN_WIDTH - bg_width) // 2
        center_y = 300
        
        screen.blit(bg, (center_x, center_y))
        screen.blit(text_surface, (center_x + padding, center_y + padding // 2))