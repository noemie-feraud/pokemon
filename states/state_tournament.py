# =============================================================================
# STATE_TOURNAMENT.PY - TOURNAMENT STATE
# =============================================================================
#
# This state manages the tournament - the endgame content.
# It handles the bracket display, combat sequence, and final victory.
# Uses Tournament class for logic and opponents.

import pygame
from states.state import State
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from endgame.tournament import Tournament


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

PHASE_BRACKET = "bracket"
PHASE_COMBAT = "combat"
PHASE_ROUND_RESULT = "round_result"
PHASE_FINAL_VICTORY = "final_victory"
PHASE_DEFEAT = "defeat"

ROUND_NAMES = ["Quart de finale", "Demi-finale", "Finale"]
NUM_ROUNDS = 3


# =============================================================================
# STATE TOURNAMENT CLASS
# =============================================================================

class StateTournament(State):
    """
    Manages tournament combat sequence.
    Pushed by tournament NPC in Arena after paying entry fee.
    Pushes StateCombat for each round.
    """
    
    transparent = False
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager, tournament):
        """
        Initialize tournament state.
        
        Args:
            game_manager: reference to Game
            tournament: Tournament instance (already registered)
        """
        super().__init__(game_manager)
        
        # --- TOURNAMENT LOGIC ---
        self.tournament = tournament
        self.opponents = tournament.get_all_opponents()
        
        # --- FONTS ---
        self.font_title = pygame.font.Font(None, 40)
        self.font_round = pygame.font.Font(None, 30)
        self.font_info = pygame.font.Font(None, 24)
        self.font_detail = pygame.font.Font(None, 20)
        self.font_message = pygame.font.Font(None, 34)
        
        # --- PROGRESSION ---
        self.current_round = 0          # 0, 1, 2
        self.phase = PHASE_BRACKET
        
        # --- COMBAT FLAG ---
        self.combat_launched = False
    
    
    # -------------------------------------------------------------------------
    # LIFECYCLE METHODS
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """Called when tournament (re)becomes active."""
        if self.phase == PHASE_BRACKET and self.current_round == 0:
            # First launch → tournament music
            self.game_manager.audio_manager.play_music("tournament")
        
        if self.combat_launched:
            # Returning from combat → check result
            self.combat_launched = False
            self._check_combat_result()
    
    
    def _check_combat_result(self):
        """After returning from combat, check if player won or lost."""
        player = self.game_manager.player
        opponent = self.opponents[self.current_round]
        
        # Check if trainer is defeated (ID added to trainers_beaten)
        if opponent.id in player.trainers_beaten:
            # Victory - register with tournament logic
            result = self.tournament.register_result(True)
            self.current_round = self.tournament.current_round
            
            if result.get("final_victory"):
                self.phase = PHASE_FINAL_VICTORY
                self.game_manager.audio_manager.play_music("victory")
            else:
                self.phase = PHASE_ROUND_RESULT
        else:
            # Defeat
            self.tournament.register_result(False)
            self.phase = PHASE_DEFEAT
    
    
    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """Handle player input based on current phase."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            if self.phase == PHASE_BRACKET:
                self._handle_bracket(event)
            
            elif self.phase == PHASE_ROUND_RESULT:
                self._handle_round_result(event)
            
            elif self.phase == PHASE_FINAL_VICTORY:
                self._handle_final_victory(event)
            
            elif self.phase == PHASE_DEFEAT:
                self._handle_defeat(event)
    
    
    def _handle_bracket(self, event):
        """Handle bracket display phase."""
        if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            self._launch_round_combat()
    
    
    def _launch_round_combat(self):
        """Launch combat for current round."""
        from states.state_combat import StateCombat
        
        opponent = self.opponents[self.current_round]
        
        # Get first valid Pokemon from opponent's team
        first_pokemon = None
        for pokemon in opponent.team.pokemon:
            if not pokemon.is_ko:
                first_pokemon = pokemon
                break
        
        if first_pokemon is None:
            # Should not happen, but just in case
            print("Warning: Opponent has no valid Pokemon!")
            return
        
        combat = StateCombat(
            self.game_manager,
            opponent_pokemon=first_pokemon,
            combat_type="trainer",
            trainer=opponent
        )
        
        self.combat_launched = True
        self.game_manager.state_manager.push(combat)
    
    
    def _handle_round_result(self, event):
        """Handle round result display."""
        if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            # Next round (already updated in tournament)
            self.phase = PHASE_BRACKET
            self.game_manager.audio_manager.play_music("tournament")
    
    
    def _handle_final_victory(self, event):
        """Handle final victory phase."""
        if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            self._end_tournament_victory()
    
    
    def _end_tournament_victory(self):
        """Player won the tournament. Register in leaderboard and go to GameOver."""
        player = self.game_manager.player
        
        # Register in leaderboard
        try:
            from endgame.leaderboard import Leaderboard
            leaderboard = Leaderboard()
            leaderboard.register(
                name=player.name,
                play_time=player.play_time,
                pokemon_count=len(player.team.pokemon) + len(player.storage.pokemon),
                pokedex_count=player.pokedex.get_total_seen()
            )
        except Exception as e:
            print(f"Leaderboard error: {e}")
        
        # Go to GameOver (victory)
        from states.state_game_over import StateGameOver
        game_over = StateGameOver(self.game_manager, victory=True)
        self.game_manager.state_manager.change(game_over)
    
    
    def _handle_defeat(self, event):
        """Handle defeat phase."""
        if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            self._end_tournament_defeat()
    
    
    def _end_tournament_defeat(self):
        """Player lost. Heal team and return to exploration."""
        player = self.game_manager.player
        
        # Heal team
        player.team.heal_all()
        
        # Return to exploration (pop tournament)
        self.game_manager.state_manager.pop()
    
    
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
        """Draw tournament screen."""
        screen.fill((20, 15, 35))
        
        if self.phase == PHASE_BRACKET:
            self._draw_bracket(screen)
            self._draw_current_opponent(screen)
        
        elif self.phase == PHASE_ROUND_RESULT:
            self._draw_bracket(screen)
            self._draw_round_result(screen)
        
        elif self.phase == PHASE_FINAL_VICTORY:
            self._draw_final_victory(screen)
        
        elif self.phase == PHASE_DEFEAT:
            self._draw_bracket(screen)
            self._draw_defeat(screen)
    
    
    def _draw_bracket(self, screen):
        """Draw tournament bracket tree."""
        # Title
        title_surface = self.font_title.render("Tournoi de l'Arena", True, (255, 220, 50))
        title_x = (SCREEN_WIDTH - title_surface.get_width()) // 2
        screen.blit(title_surface, (title_x, 20))
        
        # Simple vertical bracket
        bracket_x = 80
        bracket_y = 80
        round_height = 80
        
        results = self.tournament.get_results()
        
        for i in range(NUM_ROUNDS):
            y = bracket_y + i * round_height
            opponent = self.opponents[i] if i < len(self.opponents) else None
            round_name = ROUND_NAMES[i]
            
            # --- ROUND FRAME ---
            frame_rect = pygame.Rect(bracket_x, y, SCREEN_WIDTH - 160, 65)
            
            # Color based on state
            if i < len(results):
                # Round finished
                if results[i] == "victory":
                    bg_color = (30, 60, 30)      # dark green
                    border_color = (100, 255, 100)
                else:
                    bg_color = (60, 30, 30)      # dark red
                    border_color = (255, 100, 100)
            elif i == self.current_round:
                # Current round
                bg_color = (40, 40, 70)
                border_color = (255, 220, 50)
            else:
                # Future round
                bg_color = (30, 30, 45)
                border_color = (70, 70, 90)
            
            pygame.draw.rect(screen, bg_color, frame_rect)
            pygame.draw.rect(screen, border_color, frame_rect, 2)
            
            # --- ROUND NAME ---
            round_surface = self.font_info.render(round_name, True, (180, 180, 220))
            screen.blit(round_surface, (bracket_x + 15, y + 8))
            
            # --- OPPONENT ---
            if opponent is not None and (i < len(results) or i == self.current_round):
                # Past or current round → show name
                adv_text = f"vs {opponent.name}"
                adv_color = (255, 255, 255)
            else:
                adv_text = "vs ???"
                adv_color = (100, 100, 100)
            
            adv_surface = self.font_info.render(adv_text, True, adv_color)
            screen.blit(adv_surface, (bracket_x + 200, y + 8))
            
            # --- POKEMON COUNT ---
            if opponent is not None and (i < len(results) or i == self.current_round):
                team_size = len(opponent.team.pokemon) if hasattr(opponent, 'team') else 0
                team_text = f"{team_size} Pokémon"
                team_surface = self.font_detail.render(team_text, True, (150, 150, 180))
                screen.blit(team_surface, (bracket_x + 200, y + 35))
            
            # --- RESULT ---
            if i < len(results):
                if results[i] == "victory":
                    res_text = "✓ Victoire"
                    res_color = (100, 255, 100)
                else:
                    res_text = "✗ Défaite"
                    res_color = (255, 100, 100)
                
                res_surface = self.font_info.render(res_text, True, res_color)
                screen.blit(res_surface, (SCREEN_WIDTH - 250, y + 8))
            
            elif i == self.current_round:
                res_text = "→ En cours"
                res_surface = self.font_info.render(res_text, True, (255, 220, 50))
                screen.blit(res_surface, (SCREEN_WIDTH - 250, y + 8))
    
    
    def _draw_current_opponent(self, screen):
        """Draw current opponent details and fight button."""
        if self.current_round >= len(self.opponents):
            return
        
        opponent = self.opponents[self.current_round]
        
        # Bottom info frame
        info_y = SCREEN_HEIGHT - 220
        frame_rect = pygame.Rect(80, info_y, SCREEN_WIDTH - 160, 170)
        pygame.draw.rect(screen, (35, 35, 60), frame_rect)
        pygame.draw.rect(screen, (255, 220, 50), frame_rect, 2)
        
        # Round name
        round_text = f"{ROUND_NAMES[self.current_round]}"
        round_surface = self.font_round.render(round_text, True, (255, 220, 50))
        screen.blit(round_surface, (100, info_y + 15))
        
        # Opponent name
        name_text = f"Adversaire : {opponent.name}"
        name_surface = self.font_info.render(name_text, True, (255, 255, 255))
        screen.blit(name_surface, (100, info_y + 50))
        
        # Opponent team (Pokemon names)
        if hasattr(opponent, 'team') and len(opponent.team.pokemon) > 0:
            pokemon_names = [p.name for p in opponent.team.pokemon]
            team_text = f"Pokémon : {', '.join(pokemon_names)}"
            team_surface = self.font_detail.render(team_text, True, (180, 180, 220))
            screen.blit(team_surface, (100, info_y + 80))
        
        # Player team status
        player = self.game_manager.player
        valid_count = player.team.count_valid()
        total_count = len(player.team.pokemon)
        player_text = f"Votre équipe : {valid_count}/{total_count} Pokémon en état de combattre"
        player_surface = self.font_detail.render(player_text, True, (150, 220, 150))
        screen.blit(player_surface, (100, info_y + 105))
        
        # Fight button
        btn_text = "[Espace] Combattre !"
        btn_surface = self.font_round.render(btn_text, True, (255, 255, 255))
        btn_x = (SCREEN_WIDTH - btn_surface.get_width()) // 2
        screen.blit(btn_surface, (btn_x, info_y + 135))
    
    
    def _draw_round_result(self, screen):
        """Draw round victory message."""
        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(120)
        screen.blit(overlay, (0, 0))
        
        # Victory message
        round_name = ROUND_NAMES[self.current_round - 1] if self.current_round > 0 else ROUND_NAMES[0]
        text = f"{round_name} remportée !"
        surface = self.font_title.render(text, True, (100, 255, 100))
        x = (SCREEN_WIDTH - surface.get_width()) // 2
        y = SCREEN_HEIGHT // 2 - 30
        screen.blit(surface, (x, y))
        
        # Next round hint
        if self.current_round < NUM_ROUNDS:
            next_text = f"Prochain round : {ROUND_NAMES[self.current_round]}"
        else:
            next_text = "Vous avez atteint la finale !"
        
        next_surface = self.font_info.render(next_text, True, (200, 200, 255))
        nx = (SCREEN_WIDTH - next_surface.get_width()) // 2
        screen.blit(next_surface, (nx, y + 50))
        
        # Continue hint
        cont_surface = self.font_detail.render("[Espace] Continuer", True, (180, 180, 180))
        cx = (SCREEN_WIDTH - cont_surface.get_width()) // 2
        screen.blit(cont_surface, (cx, y + 90))
    
    
    def _draw_final_victory(self, screen):
        """Draw final victory screen."""
        screen.fill((10, 10, 30))
        
        # Big victory message
        text1 = "CHAMPION DU TOURNOI !"
        surface1 = self.font_title.render(text1, True, (255, 220, 50))
        x1 = (SCREEN_WIDTH - surface1.get_width()) // 2
        screen.blit(surface1, (x1, 200))
        
        player = self.game_manager.player
        text2 = f"{player.name} remporte le Tournoi de La Plateforme !"
        surface2 = self.font_round.render(text2, True, (255, 255, 255))
        x2 = (SCREEN_WIDTH - surface2.get_width()) // 2
        screen.blit(surface2, (x2, 280))
        
        # Game stats
        stats_text = f"Pokédex: {player.pokedex.get_total_seen()}/54   Temps: {self._format_time(player.play_time)}"
        stats_surface = self.font_info.render(stats_text, True, (180, 200, 255))
        sx = (SCREEN_WIDTH - stats_surface.get_width()) // 2
        screen.blit(stats_surface, (sx, 340))
        
        # Continue
        cont_surface = self.font_info.render("[Espace] Continuer", True, (150, 150, 150))
        cx = (SCREEN_WIDTH - cont_surface.get_width()) // 2
        screen.blit(cont_surface, (cx, 450))
    
    
    def _draw_defeat(self, screen):
        """Draw defeat message."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        screen.blit(overlay, (0, 0))
        
        round_name = ROUND_NAMES[self.current_round] if self.current_round < NUM_ROUNDS else ROUND_NAMES[-1]
        text = f"Défaite en {round_name}..."
        surface = self.font_title.render(text, True, (255, 100, 100))
        x = (SCREEN_WIDTH - surface.get_width()) // 2
        screen.blit(surface, (x, SCREEN_HEIGHT // 2 - 40))
        
        text2 = "Votre équipe sera soignée."
        surface2 = self.font_info.render(text2, True, (200, 200, 200))
        x2 = (SCREEN_WIDTH - surface2.get_width()) // 2
        screen.blit(surface2, (x2, SCREEN_HEIGHT // 2 + 10))
        
        text3 = "Vous pouvez retenter le tournoi (150 crédits)"
        surface3 = self.font_detail.render(text3, True, (180, 180, 220))
        x3 = (SCREEN_WIDTH - surface3.get_width()) // 2
        screen.blit(surface3, (x3, SCREEN_HEIGHT // 2 + 45))
        
        cont_surface = self.font_detail.render("[Espace] Quitter le tournoi", True, (150, 150, 150))
        cx = (SCREEN_WIDTH - cont_surface.get_width()) // 2
        screen.blit(cont_surface, (cx, SCREEN_HEIGHT // 2 + 90))
    
    
    def _format_time(self, seconds):
        """Format seconds to HHhMM format."""
        hours = int(seconds) // 3600
        minutes = (int(seconds) % 3600) // 60
        return f"{hours:02d}h{minutes:02d}"