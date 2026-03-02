# =============================================================================
# CAMERA.PY - GAME CAMERA
# =============================================================================
#
# In a top-down game, the map is often larger than the screen.
# The camera decides which portion of the map is shown, and follows the player.

from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE


class Camera:
    """
    Camera follows the player and calculates the offset to apply
    to everything drawn, so the player stays centered.
    """

    def __init__(self, viewport_width=None, viewport_height=None):
        self.offset_x = 0
        self.offset_y = 0
        self.map_width = SCREEN_WIDTH
        self.map_height = SCREEN_HEIGHT
        self.viewport_width = viewport_width or SCREEN_WIDTH
        self.viewport_height = viewport_height or SCREEN_HEIGHT

    def set_map_size(self, width_in_tiles, height_in_tiles):
        self.map_width = width_in_tiles * TILE_SIZE
        self.map_height = height_in_tiles * TILE_SIZE

    def update(self, target_x, target_y):
        # Center camera on target
        self.offset_x = target_x - self.viewport_width // 2
        self.offset_y = target_y - self.viewport_height // 2

        # Clamp to map bounds (or center if map smaller)
        if self.map_width > self.viewport_width:
            self.offset_x = max(0, min(self.offset_x, self.map_width - self.viewport_width))
        else:
            self.offset_x = (self.map_width - self.viewport_width) // 2

        if self.map_height > self.viewport_height:
            self.offset_y = max(0, min(self.offset_y, self.map_height - self.viewport_height))
        else:
            self.offset_y = (self.map_height - self.viewport_height) // 2

    def apply(self, x, y):
        return (x - self.offset_x, y - self.offset_y)

    def apply_rect(self, rect):
        import pygame
        return pygame.Rect(rect.x - self.offset_x, rect.y - self.offset_y, rect.width, rect.height)

    def get_visible_area(self):
        tile_start_x = int(self.offset_x // TILE_SIZE)
        tile_start_y = int(self.offset_y // TILE_SIZE)
        tile_end_x = tile_start_x + (self.viewport_width // TILE_SIZE) + 1
        tile_end_y = tile_start_y + (self.viewport_height // TILE_SIZE) + 1

        # Clamp to map bounds
        max_tile_x = self.map_width // TILE_SIZE
        max_tile_y = self.map_height // TILE_SIZE
        tile_start_x = max(0, tile_start_x)
        tile_start_y = max(0, tile_start_y)
        tile_end_x = min(max_tile_x, tile_end_x)
        tile_end_y = min(max_tile_y, tile_end_y)

        return (tile_start_x, tile_start_y, tile_end_x, tile_end_y)

    def get_offset(self):
        return (self.offset_x, self.offset_y)