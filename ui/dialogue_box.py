# =============================================================================
# DIALOGUE_BOX.PY - DIALOGUE BOX UI COMPONENT
# =============================================================================
#
# This component displays dialogue boxes at the bottom of the screen.
# Text appears with typewriter effect (letter by letter) with a "bip" sound.

import pygame
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    DIALOG_BG, DIALOG_BORDER, DIALOG_TEXT
)


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

BOX_HEIGHT = 96                  # 3 tiles high
MARGIN_X = 16                    # horizontal inner margin
MARGIN_Y = 12                    # vertical inner margin
FONT_SIZE = 22                   # text size in pixels
MAX_LINES = 2                    # number of visible lines in box
BORDER_WIDTH = 3                 # box border thickness
TYPEWRITER_SPEED = 30            # characters per second


# =============================================================================
# DIALOGUE BOX CLASS
# =============================================================================

class DialogueBox:
    """
    Dialogue box component.
    Handles typewriter effect, word wrap, and navigation.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, lines, audio_manager=None):
        """
        Initialize dialogue box.
        
        Args:
            lines: list of strings, dialogue lines to display
            audio_manager: for bip sound (can be None)
        """
        
        # --- DATA ---
        self.original_lines = lines
        self.audio_manager = audio_manager
        
        # --- FONT ---
        # Using default Pygame font for now
        self.font = pygame.font.Font(None, FONT_SIZE)
        
        # --- BOX GEOMETRY ---
        self.box_x = 0
        self.box_y = SCREEN_HEIGHT - BOX_HEIGHT
        self.box_width = SCREEN_WIDTH
        self.box_height = BOX_HEIGHT
        self.box_rect = pygame.Rect(
            self.box_x, self.box_y,
            self.box_width, self.box_height
        )
        
        # --- MAX TEXT WIDTH ---
        # Available width for text, accounting for margins
        self.max_text_width = self.box_width - (MARGIN_X * 2)
        
        # --- WORD WRAP ---
        # Pre-calculate word wrap for all lines.
        # Each original line may become 1 or 2 wrapped lines.
        # self.pages is a list of "pages".
        # Each page is a list of 1 or 2 lines (what's displayed at once).
        self.pages = self._compute_pages()
        
        # --- DISPLAY STATE ---
        self.current_page = 0
        self.displayed_chars = 0          # number of visible characters
        self.typewriter_timer = 0          # counter for typewriter
        self.text_complete = False         # True when whole page is displayed
        self.dialogue_finished = False     # True when all pages are done
        
        # --- NEXT INDICATOR ---
        # Small triangle that pulses at bottom right when text is complete
        # and waiting for player input.
        self.indicator_timer = 0
        self.indicator_visible = True
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _compute_pages(self):
        """
        Split original lines into pages.
        Each page contains at most MAX_LINES (2) lines that fit in the box.
        
        Process:
        1. For each original line, do word wrap
        2. Word wrap may produce 1, 2 or more wrapped lines
        3. Group wrapped lines into pages of 2
        
        Returns:
            list of pages, each page is a list of strings
        """
        all_wrapped_lines = []
        
        for line in self.original_lines:
            wrapped = self._word_wrap(line)
            all_wrapped_lines.extend(wrapped)
        
        # Group into pages of MAX_LINES lines
        pages = []
        current_page = []
        
        for line in all_wrapped_lines:
            current_page.append(line)
            
            if len(current_page) >= MAX_LINES:
                pages.append(current_page)
                current_page = []
        
        # Add last page if not empty
        if current_page:
            pages.append(current_page)
        
        # Safety: at least one empty page if nothing
        if not pages:
            pages.append([""])
        
        return pages
    
    
    def _word_wrap(self, line):
        """
        Split a line of text into sub-lines that fit in available width.
        Cut at last space before limit.
        
        Args:
            line: text to wrap
            
        Returns:
            list of strings (sub-lines)
        """
        words = line.split()
        result_lines = []
        current_line = ""
        
        for word in words:
            # Test if word fits on current line
            test = current_line + " " + word if current_line else word
            test_width = self.font.size(test)[0]
            
            if test_width <= self.max_text_width:
                # Fits, add the word
                current_line = test
            else:
                # Doesn't fit, start new line
                if current_line:
                    result_lines.append(current_line)
                current_line = word
        
        # Add last line
        if current_line:
            result_lines.append(current_line)
        
        if not result_lines:
            return [""]
        
        return result_lines
    
    
    def _get_full_page_text(self):
        """
        Return full text of current page concatenated.
        Used to count characters and know when typewriter is finished.
        
        Returns:
            string with "\n" as line separator
        """
        page = self.pages[self.current_page]
        return "\n".join(page)
    
    
    def _draw_indicator(self, screen):
        """Draw the small pulsing triangle at bottom right."""
        center_x = self.box_x + self.box_width - MARGIN_X - 10
        center_y = self.box_y + self.box_height - MARGIN_Y - 5
        
        points = [
            (center_x - 6, center_y - 6),
            (center_x + 6, center_y - 6),
            (center_x, center_y + 2)
        ]
        
        pygame.draw.polygon(screen, DIALOG_TEXT, points)
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def update(self, dt):
        """
        Update dialogue box state.
        
        Args:
            dt: delta time in seconds
        """
        if self.dialogue_finished:
            return
        
        if not self.text_complete:
            # Advance typewriter
            self.typewriter_timer += dt
            
            # Calculate how many characters to display
            target_chars = int(self.typewriter_timer * TYPEWRITER_SPEED)
            
            # Total characters in current page
            full_text = self._get_full_page_text()
            total_chars = len(full_text)
            
            # Play bip for each new character
            if target_chars > self.displayed_chars and self.audio_manager:
                self.audio_manager.play_sfx("dialogue_bip")
            
            self.displayed_chars = target_chars
            
            # Check if whole page is displayed
            if self.displayed_chars >= total_chars:
                self.displayed_chars = total_chars
                self.text_complete = True
        
        else:
            # Next indicator pulses
            self.indicator_timer += dt
            if self.indicator_timer >= 0.5:
                self.indicator_timer = 0
                self.indicator_visible = not self.indicator_visible
    
    
    def advance(self):
        """
        Called when player presses Space/Enter.
        
        Two behaviors:
        1. If text is still typing → display all text immediately (skip)
        2. If text is complete → go to next page
        
        If last page and text complete → dialogue finished.
        
        Returns:
            True if dialogue finished, False otherwise
        """
        if self.dialogue_finished:
            return True
        
        if not self.text_complete:
            # Skip: display all text of current page at once
            full_text = self._get_full_page_text()
            self.displayed_chars = len(full_text)
            self.text_complete = True
            return False
        
        # Text is complete → go to next page
        self.current_page += 1
        
        if self.current_page >= len(self.pages):
            # No more pages → dialogue finished
            self.dialogue_finished = True
            return True
        
        # Reset for new page
        self.displayed_chars = 0
        self.typewriter_timer = 0
        self.text_complete = False
        self.indicator_visible = True
        self.indicator_timer = 0
        
        return False
    
    
    def draw(self, screen):
        """
        Draw dialogue box on screen.
        
        Args:
            screen: Pygame surface
        """
        if self.dialogue_finished:
            return
        
        # --- BACKGROUND ---
        bg_surface = pygame.Surface((self.box_width, self.box_height))
        bg_surface.fill(DIALOG_BG)
        bg_surface.set_alpha(230)    # slightly transparent
        screen.blit(bg_surface, (self.box_x, self.box_y))
        
        # --- BORDER ---
        pygame.draw.rect(screen, DIALOG_BORDER, self.box_rect, BORDER_WIDTH)
        
        # --- TEXT ---
        page = self.pages[self.current_page]
        full_text = self._get_full_page_text()
        
        # Extract visible characters
        visible_text = full_text[:self.displayed_chars]
        
        # Split into lines for display
        visible_lines = visible_text.split("\n")
        
        for i, line in enumerate(visible_lines):
            if line:
                text_surface = self.font.render(line, True, DIALOG_TEXT)
                pos_x = self.box_x + MARGIN_X
                pos_y = self.box_y + MARGIN_Y + (i * (FONT_SIZE + 4))
                screen.blit(text_surface, (pos_x, pos_y))
        
        # --- NEXT INDICATOR ---
        if self.text_complete and self.indicator_visible:
            if self.current_page < len(self.pages) - 1:
                # Not last page → "next" triangle
                self._draw_indicator(screen)
    
    
    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------
    
    @property
    def is_finished(self):
        """Return True if dialogue is finished."""
        return self.dialogue_finished