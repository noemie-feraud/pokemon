# =============================================================================
# MAP_MANAGER.PY - MAP LOADING AND RENDERING
# =============================================================================
#
# This file loads, interprets and displays game maps.
# It reads .tmx files (created with Tiled), understands layers,
# and draws everything to the screen.

import pygame
import pytmx
from config.settings import TILE_SIZE, MAPS_DIR, ENCOUNTER_RATE


# =============================================================================
# MAP MANAGER CLASS
# =============================================================================

class MapManager:
    """
    Loads Tiled maps, draws them, and provides all necessary info
    for exploration (collisions, grass, transitions, spawns).
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self):
        """Initialize empty structures. Nothing loaded until load_map()."""
        self.tmx_data = None
        self.collision_rects = []
        self.grass_rects = []
        self.transitions = []
        self.spawns = {}
        self.width = 0
        self.height = 0
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def load_map(self, map_name, camera):
        """
        Load a map from a .tmx file.
        Called when player enters a zone (start of game, zone transition).
        
        Args:
            map_name: "campus", "outside", or "arena"
            camera: Camera object to inform about map size
        """
        import os
        filepath = os.path.join(MAPS_DIR, map_name + ".tmx")
        
        try:
            self.tmx_data = pytmx.load_pygame(filepath)
        except Exception:
            print(f"Warning: Could not load map: {filepath}")
            return
        
        # Map size in pixels
        self.width = self.tmx_data.width * TILE_SIZE
        self.height = self.tmx_data.height * TILE_SIZE
        
        # Inform camera
        camera.set_map_size(self.tmx_data.width, self.tmx_data.height)
        
        # Extract layer data
        self._parse_collisions()
        self._parse_grass()
        self._parse_transitions()
        self._parse_spawns()
    
    
    def draw(self, screen, camera):
        """
        Draw visible layers of the map on screen.
        Called every frame by state_exploration.py.
        
        Optimization: use camera.get_visible_area() to only draw
        tiles that are in the camera's view.
        
        Args:
            screen: Pygame surface
            camera: Camera object for offset and visible area
        """
        if self.tmx_data is None:
            return
        
        # Get visible area
        start_x, start_y, end_x, end_y = camera.get_visible_area()
        
        # Layers to draw (in order)
        visible_layers = ["Ground", "Decoration"]
        
        for layer_name in visible_layers:
            # Find layer in tmx_data
            for layer in self.tmx_data.visible_layers:
                if isinstance(layer, pytmx.TiledTileLayer) and layer.name == layer_name:
                    
                    # Draw only visible tiles
                    for x in range(start_x, end_x):
                        for y in range(start_y, end_y):
                            image = self.tmx_data.get_tile_image(x, y, layer)
                            
                            if image:
                                # Convert map position → screen position
                                screen_x, screen_y = camera.apply(x * TILE_SIZE, y * TILE_SIZE)
                                screen.blit(image, (screen_x, screen_y))
    
    
    def is_collision(self, tile_x, tile_y):
        """
        Check if a given tile position has a collision.
        
        Args:
            tile_x, tile_y: tile coordinates
        
        Returns:
            True if collision, False otherwise
        """
        # Check map bounds
        if tile_x < 0 or tile_y < 0:
            return True
        if tile_x >= self.tmx_data.width or tile_y >= self.tmx_data.height:
            return True
        
        # Check collision layer
        for obj in self.collision_rects:
            # Convert tile to pixel rect
            tile_rect = pygame.Rect(tile_x * TILE_SIZE, tile_y * TILE_SIZE,
                                   TILE_SIZE, TILE_SIZE)
            if tile_rect.colliderect(obj):
                return True
        
        return False
    
    
    def is_grass(self, tile_x, tile_y):
        """
        Check if player is on a grass tile (wild encounter possible).
        
        Args:
            tile_x, tile_y: tile coordinates
        
        Returns:
            True if on grass, False otherwise
        """
        tile_rect = pygame.Rect(tile_x * TILE_SIZE, tile_y * TILE_SIZE,
                               TILE_SIZE, TILE_SIZE)
        
        for grass_rect in self.grass_rects:
            if tile_rect.colliderect(grass_rect):
                return True
        
        return False
    
    
    def check_transition(self, tile_x, tile_y):
        """
        Check if player is on a transition tile.
        
        Args:
            tile_x, tile_y: tile coordinates
        
        Returns:
            transition dict if on transition, None otherwise
        """
        tile_rect = pygame.Rect(tile_x * TILE_SIZE, tile_y * TILE_SIZE,
                               TILE_SIZE, TILE_SIZE)
        
        for transition in self.transitions:
            if tile_rect.colliderect(transition["rect"]):
                return transition
        
        return None
    
    
    def get_spawn_position(self, spawn_type="player"):
        """
        Return spawn position for given type in current map.
        
        Args:
            spawn_type: "player", "nurse", "shopkeeper", "trainer", etc.
        
        Returns:
            (x, y) in pixels, or (0,0) if not found
        """
        if spawn_type in self.spawns and len(self.spawns[spawn_type]) > 0:
            spawn = self.spawns[spawn_type][0]
            return (spawn["x"], spawn["y"])
        return (0, 0)
    
    
    def get_spawns_by_type(self, spawn_type):
        """
        Return all spawns of a given type.
        Used by state_exploration.py to place NPCs, trainers, and items.
        
        Args:
            spawn_type: "trainer", "npc", "item", etc.
        
        Returns:
            list of spawn data dicts
        """
        return self.spawns.get(spawn_type, [])
    
    
    def get_map_size(self):
        """Return map size in pixels."""
        return (self.width, self.height)
    
    
    def get_npcs_data(self):
        """
        Return NPC data from spawns.
        Used by state_exploration.py to create NPC instances.
        
        Returns:
            list of dicts with NPC data
        """
        npcs = []
        # Get all NPC-like spawns
        for spawn_type in ["nurse", "shopkeeper", "professor", "quest", "trainer", "ambient"]:
            npcs.extend(self.spawns.get(spawn_type, []))
        return npcs
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _parse_collisions(self):
        """Extract collision rectangles from "Collision" layer."""
        self.collision_rects = []
        
        for layer in self.tmx_data.layers:
            if layer.name == "Collision":
                if isinstance(layer, pytmx.TiledObjectGroup):
                    for obj in layer:
                        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                        self.collision_rects.append(rect)
    
    
    def _parse_grass(self):
        """Extract grass rectangles from "Grass" layer."""
        self.grass_rects = []
        
        for layer in self.tmx_data.layers:
            if layer.name == "Grass":
                if isinstance(layer, pytmx.TiledObjectGroup):
                    for obj in layer:
                        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                        self.grass_rects.append(rect)
    
    
    def _parse_transitions(self):
        """Extract transition rectangles from "Transitions" layer."""
        self.transitions = []
        
        for layer in self.tmx_data.layers:
            if layer.name == "Transitions":
                if isinstance(layer, pytmx.TiledObjectGroup):
                    for obj in layer:
                        transition = {
                            "rect": pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                            "target_zone": obj.properties.get("target_zone", ""),
                            "spawn_x": obj.properties.get("spawn_x", 0),
                            "spawn_y": obj.properties.get("spawn_y", 0)
                        }
                        self.transitions.append(transition)
    
    
    def _parse_spawns(self):
        """Extract spawn points from "Spawns" layer."""
        self.spawns = {}
        
        for layer in self.tmx_data.layers:
            if layer.name == "Spawns":
                if isinstance(layer, pytmx.TiledObjectGroup):
                    for obj in layer:
                        spawn_type = obj.properties.get("type", "unknown")
                        
                        spawn_data = {
                            "x": obj.x,
                            "y": obj.y,
                            "properties": obj.properties
                        }
                        
                        if spawn_type not in self.spawns:
                            self.spawns[spawn_type] = []
                        
                        self.spawns[spawn_type].append(spawn_data)