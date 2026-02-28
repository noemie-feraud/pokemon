# =============================================================================
# STATE_MENU_PAUSE.PY - PAUSE MENU STATE
# =============================================================================
#
# This is the pause menu - appears when player presses Escape during exploration.
# Allows saving, accessing Pokedex, quests, and returning to main menu.

import pygame
from states.state import State
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

MODE_MENU = "menu"
MODE_SAVE = "save"
MODE_CONFIRM_QUIT = "confirm_quit"
MODE_CONFIRM_MENU = "confirm_menu"
MESSAGE_DURATION = 2.0


# =============================================================================
# STATE PAUSE MENU CLASS
# =============================================================================

class StateMenuPause(State):
    """
    Transparent pause menu. Pushed over exploration.
    Access to save, Pokedex, quests, and menu return.
    """
    
    transparent = True
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager):
        """Initialize pause menu state."""
        super().__init__(game_manager)
        
        # --- FONTS ---
        self.font_title = pygame.font.Font(None, 38)
        self.font_option = pygame.font.Font(None, 28)
        self.font_info = pygame.font.Font(None, 20)
        self.font_message = pygame.font.Font(None, 26)
        self.font_confirm = pygame.font.Font(None, 26)
        
        # --- OPTIONS ---
        self.options = [
            "Reprendre",
            "Pokédex",
            "Quêtes",
            "Sauvegarder",
            "Menu principal",
            "Quitter le jeu"
        ]
        
        # --- NAVIGATION ---
        self.selection_index = 0
        
        # --- MODE ---
        self.mode = MODE_MENU
        self.confirm_index = 0    # 0 = Yes, 1 = No
        
        # --- SAVE ---
        self.slot_selection = 0
        self.slots_info = None
        
        # --- MESSAGE ---
        self.temp_message = None
        self.message_timer = 0
        self.message_color = (255, 255, 255)
    
    
    # -------------------------------------------------------------------------
    # LIFECYCLE METHODS
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """No music change - zone music continues."""
        pass
    
    
    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """Handle player input based on current mode."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            if self.mode == MODE_MENU:
                self._handle_menu(event)
            elif self.mode == MODE_SAVE:
                self._handle_save(event)
            elif self.mode == MODE_CONFIRM_QUIT:
                self._handle_confirm(event, "quit")
            elif self.mode == MODE_CONFIRM_MENU:
                self._handle_confirm(event, "menu")
    
    
    def _handle_menu(self, event):
        """Handle inputs in main menu mode."""
        
        # --- CLOSE MENU (Escape) ---
        if event.key == pygame.K_ESCAPE:
            self.game_manager.state_manager.pop()
            return
        
        # --- NAVIGATE ---
        if event.key == pygame.K_UP:
            old = self.selection_index
            self.selection_index = max(0, self.selection_index - 1)
            if self.selection_index != old:
                self.game_manager.audio_manager.play_sfx("menu_select")
        
        elif event.key == pygame.K_DOWN:
            old = self.selection_index
            self.selection_index = min(len(self.options) - 1, self.selection_index + 1)
            if self.selection_index != old:
                self.game_manager.audio_manager.play_sfx("menu_select")
        
        # --- CONFIRM ---
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            self._execute_option()
    
    
    def _execute_option(self):
        """Execute selected menu option."""
        option = self.options[self.selection_index]
        
        # --- RESUME ---
        if option == "Reprendre":
            self.game_manager.state_manager.pop()
        
        # --- POKEDEX ---
        elif option == "Pokédex":
            from states.state_pokedex import StatePokedex
            pokedex = StatePokedex(self.game_manager)
            self.game_manager.state_manager.push(pokedex)
        
        # --- QUESTS ---
        elif option == "Quêtes":
            self._open_quests()
        
        # --- SAVE ---
        elif option == "Sauvegarder":
            self._begin_save()
        
        # --- MAIN MENU ---
        elif option == "Menu principal":
            self.mode = MODE_CONFIRM_MENU
            self.confirm_index = 1    # default to No (safety)
        
        # --- QUIT GAME ---
        elif option == "Quitter le jeu":
            self.mode = MODE_CONFIRM_QUIT
            self.confirm_index = 1    # default to No
    
    
    def _open_quests(self):
        """Open quests screen (simplified for now)."""
        quest_manager = self.game_manager.quest_manager
        player = self.game_manager.player
        
        if quest_manager is None:
            self._show_message("Aucune quête disponible", (150, 150, 150))
            return
        
        active = player.active_quests
        if len(active) == 0:
            self._show_message("Aucune quête en cours", (150, 150, 150))
        else:
            count = len(active)
            self._show_message(f"{count} quête(s) en cours", (180, 220, 255))
    
    
    def _begin_save(self):
        """Start save process."""
        if self.game_manager.current_save_slot is not None:
            # Slot already assigned → save directly
            self._perform_save(self.game_manager.current_save_slot)
        else:
            # No slot → show slot selection
            self._load_slot_info()
            self.mode = MODE_SAVE
            self.slot_selection = 0
    
    
    def _load_slot_info(self):
        """Load save slot information."""
        try:
            from core.save_manager import SaveManager
            save_manager = SaveManager()
            self.slots_info = save_manager.get_all_slots_info()
        except Exception:
            self.slots_info = [None, None, None]
    
    
    def _perform_save(self, slot_index):
        """Perform actual save to selected slot."""
        try:
            from core.save_manager import SaveManager
            save_manager = SaveManager()
            save_manager.save(self.game_manager, slot_index)
            self.game_manager.current_save_slot = slot_index
            self._show_message("Partie sauvegardée !", (100, 255, 100))
            self.mode = MODE_MENU
        except Exception as e:
            self._show_message("Erreur de sauvegarde", (255, 100, 100))
            self.mode = MODE_MENU
    
    
    def _handle_save(self, event):
        """Handle save slot selection."""
        
        # --- CANCEL ---
        if event.key == pygame.K_ESCAPE:
            self.mode = MODE_MENU
            return
        
        # --- NAVIGATE ---
        if event.key == pygame.K_UP:
            self.slot_selection = max(0, self.slot_selection - 1)
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        elif event.key == pygame.K_DOWN:
            self.slot_selection = min(2, self.slot_selection + 1)
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        # --- CONFIRM ---
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            self._perform_save(self.slot_selection)
    
    
    def _handle_confirm(self, event, action):
        """Handle confirmation dialogs (quit/main menu)."""
        
        # --- CANCEL ---
        if event.key == pygame.K_ESCAPE:
            self.mode = MODE_MENU
            return
        
        # --- NAVIGATE YES/NO ---
        if event.key == pygame.K_LEFT:
            self.confirm_index = 0
        elif event.key == pygame.K_RIGHT:
            self.confirm_index = 1
        
        # --- CONFIRM ---
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            if self.confirm_index == 0:
                # YES
                if action == "quit":
                    self.game_manager.running = False
                elif action == "menu":
                    self._return_to_main_menu()
            else:
                # NO → back to pause menu
                self.mode = MODE_MENU
    
    
    def _return_to_main_menu(self):
        """Return to main menu. Clear stack and push new StateMenu."""
        from states.state_menu import StateMenu
        
        # Clear the whole stack
        self.game_manager.state_manager.clear()
        
        # Clear game data
        self.game_manager.player = None
        self.game_manager.quest_manager = None
        self.game_manager.current_save_slot = None
        
        # Push main menu
        menu = StateMenu(self.game_manager)
        self.game_manager.state_manager.push(menu)
    
    
    # -------------------------------------------------------------------------
    # UTILITY
    # -------------------------------------------------------------------------
    
    def _show_message(self, text, color):
        """Display a temporary message."""
        self.temp_message = text
        self.message_color = color
        self.message_timer = MESSAGE_DURATION
    
    
    def _format_play_time(self):
        """Format play time as HH:MM:SS."""
        if self.game_manager.player is None:
            return "00:00:00"
        
        total_seconds = int(self.game_manager.player.play_time)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    
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
        """Draw pause menu."""
        # --- DARK OVERLAY ---
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(140)
        screen.blit(overlay, (0, 0))
        
        if self.mode == MODE_MENU:
            self._draw_menu(screen)
        
        elif self.mode == MODE_SAVE:
            self._draw_save(screen)
        
        elif self.mode == MODE_CONFIRM_QUIT:
            self._draw_confirmation(screen, "Quitter le jeu ?",
                                   "La progression non sauvegardée sera perdue.")
        
        elif self.mode == MODE_CONFIRM_MENU:
            self._draw_confirmation(screen, "Retour au menu principal ?",
                                   "La progression non sauvegardée sera perdue.")
        
        # --- MESSAGE ---
        if self.temp_message is not None:
            self._draw_message(screen)
    
    
    def _draw_menu(self, screen):
        """Draw main pause menu."""
        # Central frame
        frame_width = 300
        frame_height = 380
        frame_x = (SCREEN_WIDTH - frame_width) // 2
        frame_y = (SCREEN_HEIGHT - frame_height) // 2
        
        bg = pygame.Surface((frame_width, frame_height))
        bg.fill((30, 30, 55))
        screen.blit(bg, (frame_x, frame_y))
        pygame.draw.rect(screen, (100, 100, 150),
                        (frame_x, frame_y, frame_width, frame_height), 2)
        
        # --- TITLE ---
        title_surface = self.font_title.render("Pause", True, (255, 255, 255))
        title_x = frame_x + (frame_width - title_surface.get_width()) // 2
        screen.blit(title_surface, (title_x, frame_y + 15))
        
        # --- PLAY TIME ---
        time_text = self._format_play_time()
        time_surface = self.font_info.render(
            f"Temps de jeu: {time_text}", True, (150, 180, 220))
        time_x = frame_x + (frame_width - time_surface.get_width()) // 2
        screen.blit(time_surface, (time_x, frame_y + 50))
        
        # --- OPTIONS ---
        for i, option in enumerate(self.options):
            y = frame_y + 90 + i * 42
            
            # Highlight
            if i == self.selection_index:
                bg_opt = pygame.Rect(frame_x + 15, y - 3, frame_width - 30, 36)
                pygame.draw.rect(screen, (50, 50, 80), bg_opt)
            
            # Color
            if i == self.selection_index:
                color = (255, 255, 255)
                prefix = "> "
            else:
                color = (180, 180, 180)
                prefix = "  "
            
            # Special color for Quit (red)
            if option == "Quitter le jeu" and i == self.selection_index:
                color = (255, 120, 120)
            
            opt_surface = self.font_option.render(prefix + option, True, color)
            screen.blit(opt_surface, (frame_x + 25, y + 5))
        
        # --- HINT ---
        hint_surface = self.font_info.render("[Échap] Reprendre", True, (100, 100, 100))
        hint_x = frame_x + (frame_width - hint_surface.get_width()) // 2
        screen.blit(hint_surface, (hint_x, frame_y + frame_height - 28))
    
    
    def _draw_save(self, screen):
        """Draw save slot selection screen."""
        frame_width = 450
        frame_height = 280
        frame_x = (SCREEN_WIDTH - frame_width) // 2
        frame_y = (SCREEN_HEIGHT - frame_height) // 2
        
        bg = pygame.Surface((frame_width, frame_height))
        bg.fill((30, 30, 55))
        screen.blit(bg, (frame_x, frame_y))
        pygame.draw.rect(screen, (100, 100, 150),
                        (frame_x, frame_y, frame_width, frame_height), 2)
        
        # Title
        title_surface = self.font_option.render("Choisir un slot", True, (255, 255, 255))
        title_x = frame_x + (frame_width - title_surface.get_width()) // 2
        screen.blit(title_surface, (title_x, frame_y + 15))
        
        # 3 slots
        for i in range(3):
            y = frame_y + 60 + i * 65
            slot_rect = pygame.Rect(frame_x + 20, y, frame_width - 40, 55)
            
            # Highlight
            if i == self.slot_selection:
                pygame.draw.rect(screen, (50, 50, 80), slot_rect)
            
            pygame.draw.rect(screen, (80, 80, 120), slot_rect, 1)
            
            if self.slots_info is not None and self.slots_info[i] is not None and self.slots_info[i].get("occupied", False):
                slot = self.slots_info[i]
                slot_text = f"Slot {i+1} — {slot.get('trainer_name', '???')} (Nv.{slot.get('max_level', '?')}, {slot.get('zone', '?')})"
                slot_color = (255, 200, 100)
                
                # Warning about overwriting
                if i == self.slot_selection:
                    warn_surface = self.font_info.render(
                        "⚠ Écrasera la sauvegarde existante", True, (255, 150, 100))
                    screen.blit(warn_surface, (frame_x + 30, y + 32))
            else:
                slot_text = f"Slot {i+1} — Vide"
                slot_color = (150, 150, 150)
            
            prefix = "> " if i == self.slot_selection else "  "
            slot_surface = self.font_option.render(
                prefix + slot_text, True, slot_color)
            screen.blit(slot_surface, (frame_x + 25, y + 8))
        
        # Hint
        hint_surface = self.font_info.render(
            "[↑↓] Naviguer  [Entrée] Sauvegarder  [Échap] Annuler", True, (100, 100, 100))
        hint_x = frame_x + (frame_width - hint_surface.get_width()) // 2
        screen.blit(hint_surface, (hint_x, frame_y + frame_height - 28))
    
    
    def _draw_confirmation(self, screen, title, subtitle):
        """Draw confirmation dialog (generic)."""
        frame_width = 480
        frame_height = 150
        frame_x = (SCREEN_WIDTH - frame_width) // 2
        frame_y = (SCREEN_HEIGHT - frame_height) // 2
        
        bg = pygame.Surface((frame_width, frame_height))
        bg.fill((35, 30, 50))
        screen.blit(bg, (frame_x, frame_y))
        pygame.draw.rect(screen, (255, 150, 100),
                        (frame_x, frame_y, frame_width, frame_height), 3)
        
        # Question
        q_surface = self.font_confirm.render(title, True, (255, 255, 255))
        q_x = frame_x + (frame_width - q_surface.get_width()) // 2
        screen.blit(q_surface, (q_x, frame_y + 20))
        
        # Subtitle
        st_surface = self.font_info.render(subtitle, True, (255, 180, 130))
        st_x = frame_x + (frame_width - st_surface.get_width()) // 2
        screen.blit(st_surface, (st_x, frame_y + 52))
        
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
            opt_x = frame_x + 140 + i * 150
            screen.blit(opt_surface, (opt_x, frame_y + 95))
    
    
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
        center_y = SCREEN_HEIGHT // 2 + 100
        
        screen.blit(bg, (center_x, center_y))
        screen.blit(text_surface, (center_x + padding, center_y + padding // 2))