# =============================================================================
# HUD.PY - HEAD-UP DISPLAY
# =============================================================================
#
# This is the HUD - information displayed permanently over the exploration screen.
# Shows game time, player credits, and temporary zone name.

import pygame
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

HUD_HEIGHT = 32                   # height of top bar
MARGIN = 10                        # inner margin
HUD_FONT_SIZE = 20                 # HUD text size
ZONE_FONT_SIZE = 40                # zone name text size (big center)
ZONE_DISPLAY_DURATION = 3.0        # seconds to show zone name
ZONE_FADE_DURATION = 1.0           # seconds of fade out
HUD_BG_ALPHA = 60                  # transparency of HUD background


# =============================================================================
# HUD CLASS
# =============================================================================

class HUD:
    """
    Head-Up Display. Shows persistent info on top of exploration screen.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager):
        """
        Initialize HUD.
        
        Args:
            game_manager: to access player and day_night_cycle
        """
        self.game_manager = game_manager
        
        # --- FONTS ---
        self.font_hud = pygame.font.Font(None, HUD_FONT_SIZE)
        self.font_zone = pygame.font.Font(None, ZONE_FONT_SIZE)
        
        # --- HUD BACKGROUND ---
        # Semi-transparent surface across full width
        self.bg_surface = pygame.Surface((SCREEN_WIDTH, HUD_HEIGHT))
        self.bg_surface.fill((0, 0, 0))
        self.bg_surface.set_alpha(HUD_BG_ALPHA)
        
        # --- ZONE NAME (temporary) ---
        self.zone_name_active = False
        self.zone_name_text = ""
        self.zone_name_timer = 0
        self.zone_name_alpha = 255
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def show_zone_name(self, name):
        """
        Trigger temporary display of zone name.
        Called by state_exploration.py when player changes zone.
        
        Args:
            name: zone name ("Campus", "Alentours", "Arena")
        """
        self.zone_name_active = True
        self.zone_name_text = name
        self.zone_name_timer = 0
        self.zone_name_alpha = 255
    
    
    def update(self, dt):
        """
        Update animated HUD elements.
        Currently just zone name timer.
        
        Args:
            dt: delta time in seconds
        """
        # --- ZONE NAME ---
        if self.zone_name_active:
            self.zone_name_timer += dt
            
            if self.zone_name_timer < ZONE_DISPLAY_DURATION:
                # Display phase: full opacity
                self.zone_name_alpha = 255
            
            elif self.zone_name_timer < ZONE_DISPLAY_DURATION + ZONE_FADE_DURATION:
                # Fade phase: opacity decreases
                fade_progress = (self.zone_name_timer - ZONE_DISPLAY_DURATION) / ZONE_FADE_DURATION
                self.zone_name_alpha = int(255 * (1 - fade_progress))
            
            else:
                # Finished
                self.zone_name_active = False
                self.zone_name_alpha = 0
    
    
    def draw(self, screen):
        """
        Draw HUD on top of game screen.
        Called LAST by state_exploration.py in render(),
        after map, NPCs, player, and night filter.
        
        Args:
            screen: Pygame surface
        """
        # --- TOP BAR BACKGROUND ---
        screen.blit(self.bg_surface, (0, 0))
        
        # --- CLOCK ---
        self._draw_clock(screen)
        
        # --- CREDITS ---
        self._draw_credits(screen)
        
        # --- ZONE NAME (temporary, centered) ---
        if self.zone_name_active:
            self._draw_zone_name(screen)
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _draw_clock(self, screen):
        """
        Draw clock on left side of HUD.
        Reads time from day/night cycle.
        
        Format: "🕐 HH:MM" (using text, no emoji)
        Shows day/night indicator as text or colored rectangle.
        """
        day_night = self.game_manager.day_night_cycle
        
        if day_night is None:
            return
        
        time_str = day_night.get_formatted_time()
        
        # Day/night indicator
        if day_night.is_day():
            indicator = "[J]"
            indicator_color = (255, 220, 50)    # yellow
        else:
            indicator = "[N]"
            indicator_color = (100, 100, 255)    # blue
        
        # Draw time
        display_text = f"{indicator} {time_str}"
        surface = self.font_hud.render(display_text, True, (255, 255, 255))
        screen.blit(surface, (MARGIN, (HUD_HEIGHT - surface.get_height()) // 2))
    
    
    def _draw_credits(self, screen):
        """
        Draw credits on right side of HUD.
        Reads amount from player.
        """
        player = self.game_manager.player
        
        if player is None:
            return
        
        text = f"{player.credits} crédits"
        surface = self.font_hud.render(text, True, (255, 255, 255))
        
        # Align right
        pos_x = SCREEN_WIDTH - surface.get_width() - MARGIN
        pos_y = (HUD_HEIGHT - surface.get_height()) // 2
        screen.blit(surface, (pos_x, pos_y))
    
    
    def _draw_zone_name(self, screen):
        """
        Draw zone name in center of screen.
        Large text with semi-transparent background.
        Opacity controlled by zone_name_alpha (fade out).
        
        Text is centered horizontally and placed in upper third
        of screen (not exactly center, to avoid hiding player).
        """
        if self.zone_name_alpha <= 0:
            return
        
        # Render text
        text_surface = self.font_zone.render(self.zone_name_text, True, (255, 255, 255))
        
        # Apply alpha
        text_surface.set_alpha(self.zone_name_alpha)
        
        # Semi-transparent background behind text
        padding = 20
        bg_width = text_surface.get_width() + padding * 2
        bg_height = text_surface.get_height() + padding
        bg = pygame.Surface((bg_width, bg_height))
        bg.fill((0, 0, 0))
        bg.set_alpha(int(self.zone_name_alpha * 0.5))    # background more transparent than text
        
        # Center horizontally, upper third vertically
        center_x = (SCREEN_WIDTH - bg_width) // 2
        center_y = SCREEN_HEIGHT // 3 - bg_height // 2
        
        screen.blit(bg, (center_x, center_y))
        screen.blit(text_surface, (
            center_x + padding,
            center_y + padding // 2
        ))