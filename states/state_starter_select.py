# =============================================================================
# STATE_STARTER_SELECT.PY - STARTER SELECTION STATE
# =============================================================================
#
# This is the starter selection screen.
# Pushed by NpcProfessor callback after intro dialogue.

import pygame
from states.state import State
from entities.pokemon import Pokemon
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

MODE_CHOICE = "choice"
MODE_CONFIRMATION = "confirmation"
STARTER_LEVEL = 5

# Starter IDs (Bulbasaur, Charmander, Squirtle)
STARTER_IDS = [1, 4, 7]


# =============================================================================
# STATE STARTER SELECT CLASS
# =============================================================================

class StateStarterSelect(State):
    """
    Starter selection screen. Non-transparent, dedicated screen.
    Pushed by NpcProfessor callback.
    """
    
    transparent = False
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager, npc_professor=None):
        """
        Initialize starter selection state.
        
        Args:
            game_manager: reference to Game
            npc_professor: reference to professor (to set flag)
        """
        super().__init__(game_manager)
        
        self.npc_professor = npc_professor
        
        # --- FONTS ---
        self.font_title = pygame.font.Font(None, 38)
        self.font_name = pygame.font.Font(None, 28)
        self.font_stats = pygame.font.Font(None, 22)
        self.font_info = pygame.font.Font(None, 20)
        self.font_confirm = pygame.font.Font(None, 30)
        
        # --- CREATE THE 3 STARTERS ---
        self.starters = []
        for pokemon_id in STARTER_IDS:
            pokemon = Pokemon.from_data(pokemon_id, STARTER_LEVEL)
            self.starters.append(pokemon)
        
        # --- NAVIGATION ---
        self.selection_index = 0
        
        # --- MODE ---
        self.mode = MODE_CHOICE
        self.confirm_index = 0    # 0 = Yes, 1 = No
    
    
    # -------------------------------------------------------------------------
    # LIFECYCLE METHODS
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """Called when state becomes active."""
        self.game_manager.audio_manager.play_music("menu")
    
    
    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """Handle player input based on current mode."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            if self.mode == MODE_CHOICE:
                self._handle_choice(event)
            elif self.mode == MODE_CONFIRMATION:
                self._handle_confirmation(event)
    
    
    def _handle_choice(self, event):
        """Handle inputs in choice mode."""
        
        # --- NAVIGATE ---
        if event.key == pygame.K_LEFT:
            old = self.selection_index
            self.selection_index = max(0, self.selection_index - 1)
            if self.selection_index != old:
                self.game_manager.audio_manager.play_sfx("menu_select")
        
        elif event.key == pygame.K_RIGHT:
            old = self.selection_index
            self.selection_index = min(2, self.selection_index + 1)
            if self.selection_index != old:
                self.game_manager.audio_manager.play_sfx("menu_select")
        
        # --- CONFIRM ---
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            self.mode = MODE_CONFIRMATION
            self.confirm_index = 0    # default to "Yes"
    
    
    def _handle_confirmation(self, event):
        """Handle inputs in confirmation mode."""
        
        # --- NAVIGATE YES/NO ---
        if event.key == pygame.K_LEFT:
            self.confirm_index = 0
        elif event.key == pygame.K_RIGHT:
            self.confirm_index = 1
        
        # --- CANCEL ---
        elif event.key == pygame.K_ESCAPE:
            self.mode = MODE_CHOICE
        
        # --- CONFIRM ---
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            if self.confirm_index == 0:
                # YES → give starter
                self._give_starter()
            else:
                # NO → back to choice
                self.mode = MODE_CHOICE
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _give_starter(self):
        """Add chosen Pokemon to player's team."""
        player = self.game_manager.player
        chosen_pokemon = self.starters[self.selection_index]
        
        # Add to team
        player.team.add(chosen_pokemon)
        
        # Mark starter as received
        player.starter_received = True
        if self.npc_professor is not None:
            self.npc_professor.starter_given = True
        
        # Register in Pokedex
        player.pokedex.register_seen(chosen_pokemon)
        player.pokedex.register_captured(chosen_pokemon)
        
        # SFX
        self.game_manager.audio_manager.play_sfx("levelup")
        
        # Pop
        self.game_manager.state_manager.pop()
    
    
    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    
    def update(self, dt):
        """No animation."""
        pass
    
    
    # -------------------------------------------------------------------------
    # RENDERING
    # -------------------------------------------------------------------------
    
    def render(self, screen):
        """Draw starter selection screen."""
        # --- BACKGROUND ---
        screen.fill((30, 35, 55))
        
        # --- TITLE ---
        self._draw_title(screen)
        
        # --- THE 3 STARTER CARDS ---
        self._draw_starters(screen)
        
        # --- CONFIRMATION (if confirmation mode) ---
        if self.mode == MODE_CONFIRMATION:
            self._draw_confirmation(screen)
        
        # --- CONTROLS ---
        self._draw_controls(screen)
    
    
    def _draw_title(self, screen):
        """Draw screen title."""
        text = "Choisis ton premier Pokémon !"
        surface = self.font_title.render(text, True, (255, 255, 255))
        x = (SCREEN_WIDTH - surface.get_width()) // 2
        screen.blit(surface, (x, 40))
    
    
    def _draw_starters(self, screen):
        """Draw the 3 starter cards side by side."""
        card_width = 240
        card_height = 380
        spacing = 40
        
        # Center the 3 cards
        total_width = 3 * card_width + 2 * spacing
        start_x = (SCREEN_WIDTH - total_width) // 2
        start_y = 100
        
        for i, pokemon in enumerate(self.starters):
            x = start_x + i * (card_width + spacing)
            y = start_y
            
            # --- CARD FRAME ---
            if i == self.selection_index:
                border_color = (255, 220, 50)    # gold
                border_width = 4
            else:
                border_color = (80, 80, 120)
                border_width = 2
            
            # Card background
            card_bg = pygame.Surface((card_width, card_height))
            card_bg.fill((40, 40, 65))
            screen.blit(card_bg, (x, y))
            pygame.draw.rect(screen, border_color,
                            (x, y, card_width, card_height), border_width)
            
            # --- SPRITE (placeholder) ---
            sprite_rect = pygame.Rect(x + 60, y + 20, 120, 120)
            pygame.draw.rect(screen, (80, 80, 120), sprite_rect)
            
            # Try to load real sprite
            try:
                sprite = pokemon.get_front_sprite()
                if sprite is not None:
                    sprite_scaled = pygame.transform.scale(sprite, (120, 120))
                    screen.blit(sprite_scaled, (x + 60, y + 20))
            except Exception:
                # Placeholder remains
                text_ph = "?"
                ph_surface = self.font_title.render(text_ph, True, (150, 150, 150))
                screen.blit(ph_surface, (x + 108, y + 55))
            
            # --- NAME ---
            name_surface = self.font_name.render(pokemon.name, True, (255, 255, 255))
            name_x = x + (card_width - name_surface.get_width()) // 2
            screen.blit(name_surface, (name_x, y + 155))
            
            # --- TYPE ---
            types_text = "Type: " + " / ".join(pokemon.types)
            type_surface = self.font_stats.render(types_text, True, (180, 200, 255))
            type_x = x + (card_width - type_surface.get_width()) // 2
            screen.blit(type_surface, (type_x, y + 185))
            
            # --- STATS ---
            stats = [
                ("PV", pokemon.max_hp),
                ("ATK", pokemon.attack),
                ("DEF", pokemon.defense),
                ("VIT", pokemon.speed)
            ]
            
            for j, (label, value) in enumerate(stats):
                stat_y = y + 220 + j * 28
                
                # Label
                label_surface = self.font_stats.render(label, True, (180, 180, 180))
                screen.blit(label_surface, (x + 25, stat_y))
                
                # Value
                value_surface = self.font_stats.render(str(value), True, (255, 255, 255))
                screen.blit(value_surface, (x + 80, stat_y))
                
                # Visual bar (proportional, max ~80)
                bar_x = x + 115
                bar_max_width = 100
                ratio = min(1.0, value / 80)
                fill_width = int(bar_max_width * ratio)
                
                pygame.draw.rect(screen, (50, 50, 50),
                                (bar_x, stat_y + 4, bar_max_width, 10))
                if fill_width > 0:
                    if ratio > 0.7:
                        stat_color = (100, 255, 100)
                    elif ratio > 0.4:
                        stat_color = (255, 255, 100)
                    else:
                        stat_color = (255, 100, 100)
                    pygame.draw.rect(screen, stat_color,
                                    (bar_x, stat_y + 4, fill_width, 10))
            
            # --- ATTACKS ---
            atk_y = y + 340
            for k, attack in enumerate(pokemon.attacks):
                atk_text = f"• {attack.name} ({attack.type})"
                atk_surface = self.font_info.render(atk_text, True, (170, 170, 200))
                screen.blit(atk_surface, (x + 20, atk_y + k * 18))
    
    
    def _draw_confirmation(self, screen):
        """Draw confirmation overlay."""
        pokemon = self.starters[self.selection_index]
        
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        screen.blit(overlay, (0, 0))
        
        # Confirmation frame
        frame_width = 450
        frame_height = 120
        frame_x = (SCREEN_WIDTH - frame_width) // 2
        frame_y = (SCREEN_HEIGHT - frame_height) // 2
        
        bg = pygame.Surface((frame_width, frame_height))
        bg.fill((35, 35, 60))
        screen.blit(bg, (frame_x, frame_y))
        pygame.draw.rect(screen, (255, 220, 50),
                        (frame_x, frame_y, frame_width, frame_height), 3)
        
        # Question
        text = f"Tu choisis {pokemon.name} ?"
        q_surface = self.font_confirm.render(text, True, (255, 255, 255))
        q_x = frame_x + (frame_width - q_surface.get_width()) // 2
        screen.blit(q_surface, (q_x, frame_y + 20))
        
        # Yes / No
        options = ["Oui", "Non"]
        for i, option in enumerate(options):
            if i == self.confirm_index:
                color = (255, 220, 50)
                prefix = "> "
            else:
                color = (180, 180, 180)
                prefix = "  "
            
            opt_surface = self.font_confirm.render(
                prefix + option, True, color)
            
            opt_x = frame_x + 120 + i * 150
            screen.blit(opt_surface, (opt_x, frame_y + 70))
    
    
    def _draw_controls(self, screen):
        """Draw controls hint."""
        if self.mode == MODE_CHOICE:
            text = "[←→] Choisir  [Entrée] Confirmer"
        else:
            text = "[←→] Oui/Non  [Entrée] Valider  [Échap] Retour"
        
        surface = self.font_info.render(text, True, (120, 120, 120))
        x = (SCREEN_WIDTH - surface.get_width()) // 2
        screen.blit(surface, (x, SCREEN_HEIGHT - 40))