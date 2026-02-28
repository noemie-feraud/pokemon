# =============================================================================
# STATE_GAME_OVER.PY - GAME OVER STATE
# =============================================================================
#
# This is the tournament victory screen.
# Pushed by state_tournament when player wins the tournament.

import pygame
from states.state import State
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TOTAL_POKEMON


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

MODE_SCREEN = "screen"
MODE_CONFIRM_MENU = "confirm_menu"


# =============================================================================
# STATE GAME OVER CLASS
# =============================================================================

class StateGameOver(State):
    """
    Tournament victory screen. Player can continue adventure
    or return to main menu.
    """
    
    transparent = False
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager):
        """Initialize game over state."""
        super().__init__(game_manager)
        
        self.player = game_manager.player
        
        # --- FONTS ---
        self.font_title = pygame.font.Font(None, 46)
        self.font_subtitle = pygame.font.Font(None, 30)
        self.font_stat = pygame.font.Font(None, 24)
        self.font_leaderboard = pygame.font.Font(None, 22)
        self.font_info = pygame.font.Font(None, 20)
        self.font_choice = pygame.font.Font(None, 28)
        self.font_confirm = pygame.font.Font(None, 26)
        
        # --- GAME STATS ---
        self.game_stats = self._compute_stats()
        
        # --- LEADERBOARD ---
        self.leaderboard_entries = self._load_leaderboard()
        
        # --- CHOICE ---
        self.mode = MODE_SCREEN
        self.choice_index = 0          # 0 = Continue, 1 = Main menu
        self.confirm_index = 1        # default to No (safety)
        
        # --- AUTO SAVE ---
        self._save_game()
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _compute_stats(self):
        """Compute game completion stats."""
        player = self.player
        
        if player is None:
            return {
                "name": "???",
                "time": "00h00",
                "time_seconds": 0,
                "pokemon_captured": 0,
                "pokedex_seen": 0,
                "pokedex_percent": 0,
                "credits": 0,
                "trainers_defeated": 0,
                "team_size": 0,
                "storage_size": 0
            }
        
        time_seconds = int(player.play_time)
        hours = time_seconds // 3600
        minutes = (time_seconds % 3600) // 60
        
        pokedex_seen = player.pokedex.get_total_seen()
        pokedex_percent = int((pokedex_seen / TOTAL_POKEMON) * 100) if TOTAL_POKEMON > 0 else 0
        
        return {
            "name": player.name,
            "time": f"{hours:02d}h{minutes:02d}",
            "time_seconds": time_seconds,
            "pokemon_captured": player.pokedex.get_total_captured(),
            "pokedex_seen": pokedex_seen,
            "pokedex_percent": pokedex_percent,
            "credits": player.credits,
            "trainers_defeated": len(player.trainers_beaten),
            "team_size": len(player.team.pokemon),
            "storage_size": len(player.storage.pokemon)
        }
    
    
    def _load_leaderboard(self):
        """Load leaderboard entries."""
        try:
            from endgame.leaderboard import Leaderboard
            leaderboard = Leaderboard()
            entries = leaderboard.get_rankings()
            return entries
        except Exception:
            return []
    
    
    def _save_game(self):
        """Auto-save after victory."""
        try:
            from core.save_manager import SaveManager
            if self.game_manager.current_save_slot is not None:
                player = self.game_manager.player
                player.tournament_won = True
                save_manager = SaveManager()
                save_manager.save(
                    self.game_manager,
                    self.game_manager.current_save_slot
                )
        except Exception:
            pass
    
    
    # -------------------------------------------------------------------------
    # LIFECYCLE METHODS
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """Called when state becomes active."""
        self.game_manager.audio_manager.play_music("victory")
    
    
    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """Handle player input."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            if self.mode == MODE_SCREEN:
                self._handle_screen(event)
            elif self.mode == MODE_CONFIRM_MENU:
                self._handle_confirm_menu(event)
    
    
    def _handle_screen(self, event):
        """Handle inputs in main screen mode."""
        
        # --- NAVIGATE BETWEEN THE TWO CHOICES ---
        if event.key == pygame.K_LEFT:
            if self.choice_index != 0:
                self.choice_index = 0
                self.game_manager.audio_manager.play_sfx("menu_select")
        
        elif event.key == pygame.K_RIGHT:
            if self.choice_index != 1:
                self.choice_index = 1
                self.game_manager.audio_manager.play_sfx("menu_select")
        
        # --- CONFIRM ---
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            if self.choice_index == 0:
                # Continue adventure
                self._continue_adventure()
            else:
                # Main menu → ask confirmation
                self.mode = MODE_CONFIRM_MENU
                self.confirm_index = 1    # default to No
    
    
    def _continue_adventure(self):
        """
        Player continues exploration.
        Pop GameOver AND Tournament to return to exploration.
        
        Before stack: [exploration, tournament, game_over]
        After stack: [exploration]
        """
        state_manager = self.game_manager.state_manager
        
        # Pop GameOver (ourselves)
        state_manager.pop()
        
        # Pop Tournament
        state_manager.pop()
        
        # Exploration becomes active → on_enter() is called
    
    
    def _handle_confirm_menu(self, event):
        """Handle confirmation for returning to main menu."""
        
        # --- CANCEL ---
        if event.key == pygame.K_ESCAPE:
            self.mode = MODE_SCREEN
            return
        
        # --- NAVIGATE ---
        if event.key == pygame.K_LEFT:
            self.confirm_index = 0
        elif event.key == pygame.K_RIGHT:
            self.confirm_index = 1
        
        # --- CONFIRM ---
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            if self.confirm_index == 0:
                # YES → return to main menu
                self._return_to_menu()
            else:
                # NO → back to victory screen
                self.mode = MODE_SCREEN
    
    
    def _return_to_menu(self):
        """Return to main menu. Clear stack and push new StateMenu."""
        from states.state_menu import StateMenu
        
        # Clear game data
        self.game_manager.player = None
        self.game_manager.quest_manager = None
        self.game_manager.current_save_slot = None
        
        # Clear the stack
        self.game_manager.state_manager.clear()
        
        # New main menu
        menu = StateMenu(self.game_manager)
        self.game_manager.state_manager.push(menu)
    
    
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
        """Draw game over screen."""
        screen.fill((10, 10, 25))
        
        self._draw_title(screen)
        self._draw_stats(screen)
        self._draw_leaderboard(screen)
        self._draw_choices(screen)
        
        if self.mode == MODE_CONFIRM_MENU:
            self._draw_confirmation(screen)
    
    
    def _draw_title(self, screen):
        """Draw title and stars."""
        stars_text = "★  ★  ★"
        stars_surface = self.font_subtitle.render(stars_text, True, (255, 220, 50))
        stars_x = (SCREEN_WIDTH - stars_surface.get_width()) // 2
        screen.blit(stars_surface, (stars_x, 25))
        
        title_text = "FÉLICITATIONS !"
        title_surface = self.font_title.render(title_text, True, (255, 220, 50))
        title_x = (SCREEN_WIDTH - title_surface.get_width()) // 2
        screen.blit(title_surface, (title_x, 55))
        
        subtitle_text = "Tu as remporté le Tournoi de La Plateforme !"
        subtitle_surface = self.font_subtitle.render(subtitle_text, True, (220, 220, 255))
        subtitle_x = (SCREEN_WIDTH - subtitle_surface.get_width()) // 2
        screen.blit(subtitle_surface, (subtitle_x, 105))
    
    
    def _draw_stats(self, screen):
        """Draw game completion stats."""
        stats = self.game_stats
        
        # Frame
        frame_x = 100
        frame_y = 155
        frame_width = SCREEN_WIDTH - 200
        frame_height = 220
        
        pygame.draw.rect(screen, (25, 30, 50),
                        (frame_x, frame_y, frame_width, frame_height))
        pygame.draw.rect(screen, (80, 100, 160),
                        (frame_x, frame_y, frame_width, frame_height), 2)
        
        # Frame title
        title_surface = self.font_stat.render("Résumé de la partie", True, (180, 200, 255))
        screen.blit(title_surface, (frame_x + 20, frame_y + 12))
        
        # Stats in two columns
        col1_x = frame_x + 30
        col2_x = frame_x + frame_width // 2 + 20
        line_y = frame_y + 45
        spacing = 28
        
        # Column 1
        col1_stats = [
            ("Dresseur", stats["name"]),
            ("Temps de jeu", stats["time"]),
            ("Pokémon capturés", str(stats["pokemon_captured"])),
            ("Équipe", f"{stats['team_size']} Pokémon"),
            ("Stockage", f"{stats['storage_size']} Pokémon")
        ]
        
        for i, (label, value) in enumerate(col1_stats):
            y = line_y + i * spacing
            label_surface = self.font_stat.render(label + " :", True, (150, 160, 200))
            screen.blit(label_surface, (col1_x, y))
            value_surface = self.font_stat.render(value, True, (255, 255, 255))
            screen.blit(value_surface, (col1_x + 200, y))
        
        # Column 2
        col2_stats = [
            ("Pokédex", f"{stats['pokedex_seen']}/{TOTAL_POKEMON} ({stats['pokedex_percent']}%)"),
            ("Dresseurs battus", str(stats['trainers_defeated'])),
            ("Crédits totaux", str(stats['credits']))
        ]
        
        for i, (label, value) in enumerate(col2_stats):
            y = line_y + i * spacing
            label_surface = self.font_stat.render(label + " :", True, (150, 160, 200))
            screen.blit(label_surface, (col2_x, y))
            value_surface = self.font_stat.render(value, True, (255, 255, 255))
            screen.blit(value_surface, (col2_x + 200, y))
        
        # Pokedex progress bar
        bar_y = line_y + 3 * spacing + 5
        bar_x = col2_x
        bar_width = 200
        bar_height = 10
        ratio = stats["pokedex_seen"] / TOTAL_POKEMON if TOTAL_POKEMON > 0 else 0
        
        pygame.draw.rect(screen, (40, 40, 60),
                        (bar_x, bar_y, bar_width, bar_height))
        fill_width = int(bar_width * ratio)
        if fill_width > 0:
            if ratio >= 1.0:
                bar_color = (255, 220, 50)
            elif ratio >= 0.75:
                bar_color = (100, 255, 100)
            else:
                bar_color = (100, 180, 255)
            
            pygame.draw.rect(screen, bar_color,
                            (bar_x, bar_y, fill_width, bar_height))
        
        # Special message if Pokedex complete
        if stats["pokedex_percent"] >= 100:
            complete_text = "★ Pokédex complet ! Maître Pokémon ! ★"
            complete_surface = self.font_stat.render(complete_text, True, (255, 220, 50))
            cx = (SCREEN_WIDTH - complete_surface.get_width()) // 2
            screen.blit(complete_surface, (cx, frame_y + frame_height - 28))
    
    
    def _draw_leaderboard(self, screen):
        """Draw leaderboard rankings."""
        frame_x = 100
        frame_y = 390
        frame_width = SCREEN_WIDTH - 200
        frame_height = 175
        
        pygame.draw.rect(screen, (25, 25, 45),
                        (frame_x, frame_y, frame_width, frame_height))
        pygame.draw.rect(screen, (80, 80, 130),
                        (frame_x, frame_y, frame_width, frame_height), 2)
        
        # Title
        title_surface = self.font_stat.render("Classement", True, (255, 220, 50))
        screen.blit(title_surface, (frame_x + 20, frame_y + 10))
        
        # Headers
        header_y = frame_y + 38
        headers = ["#", "Dresseur", "Temps", "Pokédex", "Capturés"]
        header_positions = [frame_x + 20, frame_x + 55, frame_x + 220, frame_x + 340, frame_x + 480]
        
        for i, header in enumerate(headers):
            surface = self.font_info.render(header, True, (140, 150, 190))
            screen.blit(surface, (header_positions[i], header_y))
        
        pygame.draw.line(screen, (60, 60, 90),
                        (frame_x + 15, header_y + 22),
                        (frame_x + frame_width - 15, header_y + 22), 1)
        
        # Entries (max 5)
        if len(self.leaderboard_entries) == 0:
            empty_surface = self.font_leaderboard.render(
                "Aucune entrée", True, (100, 100, 100))
            screen.blit(empty_surface, (frame_x + 30, header_y + 35))
            return
        
        num_display = min(5, len(self.leaderboard_entries))
        
        for i in range(num_display):
            entry = self.leaderboard_entries[i]
            y = header_y + 30 + i * 24
            
            # Highlight if current game
            is_current = (
                entry.get("name") == self.game_stats["name"] and
                entry.get("time_seconds") == self.game_stats.get("time_seconds", -1)
            )
            
            if is_current:
                bg_rect = pygame.Rect(frame_x + 10, y - 2, frame_width - 20, 22)
                pygame.draw.rect(screen, (40, 45, 70), bg_rect)
                color = (255, 220, 100)
            else:
                color = (200, 200, 220)
            
            # Rank
            rank_surface = self.font_leaderboard.render(str(i + 1), True, color)
            screen.blit(rank_surface, (header_positions[0], y))
            
            # Name
            name_surface = self.font_leaderboard.render(
                entry.get("name", "???"), True, color)
            screen.blit(name_surface, (header_positions[1], y))
            
            # Time
            time_surface = self.font_leaderboard.render(
                entry.get("time_formatted", "??h??"), True, color)
            screen.blit(time_surface, (header_positions[2], y))
            
            # Pokedex
            dex_text = f"{entry.get('pokedex_count', 0)}/54"
            dex_surface = self.font_leaderboard.render(dex_text, True, color)
            screen.blit(dex_surface, (header_positions[3], y))
            
            # Captured
            cap_surface = self.font_leaderboard.render(
                str(entry.get("pokemon_count", 0)), True, color)
            screen.blit(cap_surface, (header_positions[4], y))
    
    
    def _draw_choices(self, screen):
        """Draw the two choices at bottom."""
        choice_y = SCREEN_HEIGHT - 65
        
        options = ["Continuer l'aventure", "Menu principal"]
        
        # Center both options
        total_width = 450
        start_x = (SCREEN_WIDTH - total_width) // 2
        
        for i, option in enumerate(options):
            if i == self.choice_index:
                color = (255, 255, 255)
                prefix = "> "
                # Selection background
                opt_x = start_x + i * 280
                bg_rect = pygame.Rect(opt_x - 10, choice_y - 5, 260, 35)
                pygame.draw.rect(screen, (50, 50, 80), bg_rect)
                pygame.draw.rect(screen, (255, 220, 50), bg_rect, 2)
            else:
                color = (140, 140, 160)
                prefix = "  "
            
            surface = self.font_choice.render(prefix + option, True, color)
            opt_x = start_x + i * 280
            screen.blit(surface, (opt_x, choice_y))
        
        # Hint
        hint_surface = self.font_info.render(
            "[←→] Choisir  [Entrée] Valider", True, (90, 90, 110))
        hint_x = (SCREEN_WIDTH - hint_surface.get_width()) // 2
        screen.blit(hint_surface, (hint_x, SCREEN_HEIGHT - 25))
    
    
    def _draw_confirmation(self, screen):
        """Draw confirmation dialog for main menu return."""
        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        screen.blit(overlay, (0, 0))
        
        # Frame
        frame_width = 500
        frame_height = 140
        frame_x = (SCREEN_WIDTH - frame_width) // 2
        frame_y = (SCREEN_HEIGHT - frame_height) // 2
        
        bg = pygame.Surface((frame_width, frame_height))
        bg.fill((35, 30, 55))
        screen.blit(bg, (frame_x, frame_y))
        pygame.draw.rect(screen, (255, 150, 100),
                        (frame_x, frame_y, frame_width, frame_height), 3)
        
        # Question
        q_surface = self.font_confirm.render(
            "Retour au menu principal ?", True, (255, 255, 255))
        q_x = frame_x + (frame_width - q_surface.get_width()) // 2
        screen.blit(q_surface, (q_x, frame_y + 18))
        
        # Warning
        warn_surface = self.font_info.render(
            "La progression non sauvegardée sera perdue.", True, (255, 180, 130))
        w_x = frame_x + (frame_width - warn_surface.get_width()) // 2
        screen.blit(warn_surface, (w_x, frame_y + 50))
        
        # Yes / No
        confirm_options = ["Oui", "Non"]
        for i, option in enumerate(confirm_options):
            if i == self.confirm_index:
                color = (255, 220, 50)
                prefix = "> "
            else:
                color = (180, 180, 180)
                prefix = "  "
            
            opt_surface = self.font_confirm.render(prefix + option, True, color)
            opt_x = frame_x + 150 + i * 160
            screen.blit(opt_surface, (opt_x, frame_y + 90))