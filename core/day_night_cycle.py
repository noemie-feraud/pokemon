# =============================================================================
# DAY_NIGHT_CYCLE.PY - DAY/NIGHT CYCLE MANAGER
# =============================================================================
#
# Manages the accelerated day/night cycle (24 in-game hours = 1 real hour).
# Handles time tracking, visual filter, and combat penalties.

import pygame
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    DAY_START, NIGHT_START, CYCLE_GAME_DURATION,
    TIME_RATIO, NIGHT_PENALTY,
    NIGHT_FILTER_COLOR, NIGHT_FILTER_ALPHA
)


# =============================================================================
# DAY/NIGHT CYCLE CLASS
# =============================================================================

class DayNightCycle:
    """
    Manages accelerated day/night cycle.
    Time is stored in game minutes (0 to 1439).
    24 in-game hours = 1 real hour.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self):
        """
        Initialize cycle.
        
        current_time: time in game minutes (0 to 1439)
            Default 480 = 8:00 AM (player starts in daytime)
        
        filter_surface: semi-transparent Pygame surface for night effect.
            Created once here, alpha changed each frame for performance.
        
        TWILIGHT_START and DAWN_START: start times for gradual transitions.
            Twilight: 2 hours before night (18:00 if night at 20:00)
            Dawn: 2 hours before day (4:00 if day at 6:00)
            Transition duration: 2 in-game hours = 5 real minutes,
                enough for player to see change without being too long.
        """
        self.current_time = 480      # 8:00 AM
        
        # Transition constants
        self.twilight_start = NIGHT_START - 120    # 1200 - 120 = 1080 (18:00)
        self.twilight_duration = 120                 # 2 hours transition
        self.dawn_start = DAY_START - 120            # 360 - 120 = 240 (4:00)
        self.dawn_duration = 120                      # 2 hours transition
        
        # Night filter surface
        self.filter_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.filter_surface.fill(NIGHT_FILTER_COLOR)
        
        # Current filter alpha (0 = invisible, NIGHT_FILTER_ALPHA = max)
        self.current_alpha = 0
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def update(self, dt):
        """
        Advance clock and recalculate filter alpha.
        Called every frame by game.py.
        
        Args:
            dt: delta time in seconds (real time)
        """
        # Advance clock
        self.current_time += dt * TIME_RATIO
        
        # Loop at midnight
        if self.current_time >= CYCLE_GAME_DURATION:
            self.current_time %= CYCLE_GAME_DURATION
        
        # Recalculate filter alpha
        self._update_alpha()
    
    
    def draw_filter(self, screen):
        """
        Draw night filter over the screen.
        Called by state_exploration.py AFTER drawing map, sprites, NPCs.
        Filter goes on top of everything.
        
        If alpha is 0 (full day), draw nothing (optimization).
        
        Args:
            screen: Pygame surface
        """
        if self.current_alpha > 0:
            self.filter_surface.set_alpha(self.current_alpha)
            screen.blit(self.filter_surface, (0, 0))
    
    
    def is_day(self):
        """
        Return True if daytime, False otherwise.
        Day: from DAY_START (6:00) to NIGHT_START (20:00).
        
        Used by damage_calculator.py for night penalty.
        """
        return DAY_START <= self.current_time < NIGHT_START
    
    
    def is_night(self):
        """Return True if nighttime, False otherwise."""
        return not self.is_day()
    
    
    def get_penalty(self, pokemon_type):
        """
        Get damage penalty for a Pokemon based on time.
        
        Args:
            pokemon_type: "diurne" or "nocturne"
        
        Returns:
            float multiplier (1.0 = no penalty, 0.8 = -20%)
        """
        if self.is_day() and pokemon_type == "nocturne":
            return 1.0 - NIGHT_PENALTY
        elif self.is_night() and pokemon_type == "diurne":
            return 1.0 - NIGHT_PENALTY
        return 1.0
    
    
    def get_formatted_time(self):
        """
        Return current time as formatted string HH:MM.
        Used by HUD for display.
        
        Returns:
            str like "14:35"
        """
        hours = int(self.current_time) // 60
        minutes = int(self.current_time) % 60
        return f"{hours:02d}:{minutes:02d}"
    
    
    def set_time(self, minutes):
        """
        Set current time directly (used when loading save).
        
        Args:
            minutes: game minutes (0 to 1439)
        """
        self.current_time = minutes % CYCLE_GAME_DURATION
        self._update_alpha()
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _update_alpha(self):
        """
        Calculate night filter opacity based on current time.
        
        4 phases in cycle:
        
        1. FULL DAY (6:00 → 18:00): alpha = 0
            Filter invisible, map normally lit.
        
        2. TWILIGHT (18:00 → 20:00): alpha increases 0 → MAX
            Gradual transition. Calculate progress percentage
            and apply to max alpha.
            Example: at 19:00, 50% through twilight → alpha = 60
        
        3. FULL NIGHT (20:00 → 4:00): alpha = MAX
            Filter at max, dark.
        
        4. DAWN (4:00 → 6:00): alpha decreases MAX → 0
            Reverse transition.
        
        Note: full night includes midnight (20:00 → 23:59 then 0:00 → 4:00).
        Code handles both cases.
        """
        t = self.current_time
        
        # Phase 1: Full day
        if DAY_START <= t < self.twilight_start:
            self.current_alpha = 0
        
        # Phase 2: Twilight (day → night transition)
        elif self.twilight_start <= t < NIGHT_START:
            progress = (t - self.twilight_start) / self.twilight_duration
            self.current_alpha = int(NIGHT_FILTER_ALPHA * progress)
        
        # Phase 3: Full night (from NIGHT_START to DAWN_START, across midnight)
        elif t >= NIGHT_START or t < self.dawn_start:
            self.current_alpha = NIGHT_FILTER_ALPHA
        
        # Phase 4: Dawn (night → day transition)
        elif self.dawn_start <= t < DAY_START:
            progress = (t - self.dawn_start) / self.dawn_duration
            self.current_alpha = int(NIGHT_FILTER_ALPHA * (1 - progress))