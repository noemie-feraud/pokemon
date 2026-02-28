# =============================================================================
# CAMERA.PY - GAME CAMERA
# =============================================================================
#
# In a top-down game, the map is often larger than the screen.
# The camera decides which portion of the map is shown, and follows the player.

from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE


# =============================================================================
# CAMERA CLASS
# =============================================================================

class Camera:
    """
    Camera follows the player and calculates the offset to apply
    to everything drawn, so the player stays centered.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self):
        """
        Initialize camera.
        
        offset_x, offset_y: pixel offset.
            This is the distance between map top-left and screen top-left.
            Initially (0,0) means we see the top-left corner of the map.
        
        map_width, map_height: total map size in pixels.
            Initialized to screen size by default.
            Updated when loading a new map via set_map_size().
            Used for clamping (prevent camera from going out of bounds).
        """
        self.offset_x = 0
        self.offset_y = 0
        self.map_width = SCREEN_WIDTH
        self.map_height = SCREEN_HEIGHT
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def set_map_size(self, width_in_tiles, height_in_tiles):
        """
        Called by map_manager.py when loading a new map.
        Receives map size in tiles, converts to pixels by multiplying by TILE_SIZE.
        
        Args:
            width_in_tiles: map width in tiles
            height_in_tiles: map height in tiles
        """
        self.map_width = width_in_tiles * TILE_SIZE
        self.map_height = height_in_tiles * TILE_SIZE
    
    
    def update(self, target_x, target_y):
        """
        Called every frame by state_exploration.py.
        Receives player position in pixels (sprite center).
        
        Step 1: calculate offset to center player
            offset = player_position - half_screen
        
        Step 2: clamp offset to map bounds
            offset_x between 0 and (map_width - screen_width)
            offset_y between 0 and (map_height - screen_height)
        
        If map is smaller than screen on one axis, center the map on that axis.
        
        Args:
            target_x, target_y: target position to center on (player)
        """
        # Center camera on target
        self.offset_x = target_x - SCREEN_WIDTH // 2
        self.offset_y = target_y - SCREEN_HEIGHT // 2
        
        # Clamp to map bounds
        # Normal case: map larger than screen
        if self.map_width > SCREEN_WIDTH:
            if self.offset_x < 0:
                self.offset_x = 0
            if self.offset_x > self.map_width - SCREEN_WIDTH:
                self.offset_x = self.map_width - SCREEN_WIDTH
        else:
            # Map smaller than screen → center it
            self.offset_x = -(SCREEN_WIDTH - self.map_width) // 2
        
        if self.map_height > SCREEN_HEIGHT:
            if self.offset_y < 0:
                self.offset_y = 0
            if self.offset_y > self.map_height - SCREEN_HEIGHT:
                self.offset_y = self.map_height - SCREEN_HEIGHT
        else:
            self.offset_y = -(SCREEN_HEIGHT - self.map_height) // 2
    
    
    def apply(self, x, y):
        """
        Convert world position (on map) to screen position (where to draw).
        
        Example:
            Tree at (600, 300) on map.
            Camera offset is (100, 50).
            apply(600, 300) returns (500, 250).
            → Draw tree at (500, 250) on screen.
        
        Args:
            x, y: world coordinates in pixels
        
        Returns:
            (screen_x, screen_y) coordinates in pixels
        """
        return (x - self.offset_x, y - self.offset_y)
    
    
    def apply_rect(self, rect):
        """
        Same as apply() but for a pygame.Rect.
        Useful because sprites often have a .rect for their position.
        
        Creates a new shifted rect instead of modifying the original,
        so the real map position is preserved.
        
        Args:
            rect: pygame.Rect in world coordinates
        
        Returns:
            new pygame.Rect in screen coordinates
        """
        import pygame
        return pygame.Rect(
            rect.x - self.offset_x,
            rect.y - self.offset_y,
            rect.width,
            rect.height
        )
    
    
    def get_visible_area(self):
        """
        Return visible area rectangle in map coordinates (tiles).
        Used for rendering optimization: only draw tiles in visible area.
        
        Returns:
            (tile_start_x, tile_start_y, tile_end_x, tile_end_y)
        """
        tile_start_x = int(self.offset_x // TILE_SIZE)
        tile_start_y = int(self.offset_y // TILE_SIZE)
        tile_end_x = tile_start_x + (SCREEN_WIDTH // TILE_SIZE) + 1
        tile_end_y = tile_start_y + (SCREEN_HEIGHT // TILE_SIZE) + 1
        
        # Clamp to map bounds
        if tile_start_x < 0:
            tile_start_x = 0
        if tile_start_y < 0:
            tile_start_y = 0
        if tile_end_x > self.map_width // TILE_SIZE:
            tile_end_x = self.map_width // TILE_SIZE
        if tile_end_y > self.map_height // TILE_SIZE:
            tile_end_y = self.map_height // TILE_SIZE
        
        return (tile_start_x, tile_start_y, tile_end_x, tile_end_y)
    
    
    def get_offset(self):
        """Return current offset (for drawing)."""
        return (self.offset_x, self.offset_y)