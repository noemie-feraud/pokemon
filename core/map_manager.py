import pygame
import pytmx
from config.settings import TILE_SIZE, MAPS_DIR, ENCOUNTER_RATE


class MapManager:
    """
    Loads Tiled maps, draws them, and provides all necessary info
    for exploration (collisions, grass, transitions, spawns).
    """
    
    def __init__(self):
        self.tmx_data = None
        self.collision_rects = []
        self.grass_rects = []
        self.transitions = []
        self.spawns = {}
        self.width = 0
        self.height = 0
        self.current_map = ""
    
    
    def load_map(self, map_name, camera, transition_point_size=None):
        import os
        filepath = os.path.join(MAPS_DIR, map_name + ".tmx")

        if not os.path.exists(filepath):
            print(f"Warning: Map file not found: {filepath}")
            return False

        try:
            new_tmx = pytmx.load_pygame(filepath)
        except Exception as e:
            print(f"Warning: Could not load map: {filepath} — {e}")
            return False

        # Only commit the change if loading succeeded
        self.current_map = map_name
        self.tmx_data = new_tmx
        self.width = self.tmx_data.width * TILE_SIZE
        self.height = self.tmx_data.height * TILE_SIZE

        camera.set_map_size(self.tmx_data.width, self.tmx_data.height)

        self._parse_collisions()
        self._parse_grass()
        self._parse_transitions(transition_point_size or TILE_SIZE)
        self._parse_spawns()
        return True
    
    
    def draw(self, screen, camera):
        if self.tmx_data is None:
            return

        start_x, start_y, end_x, end_y = camera.get_visible_area()

        for layer in self.tmx_data.visible_layers:
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue
            for x, y, image in layer.tiles():
                if start_x <= x < end_x and start_y <= y < end_y:
                    screen_x, screen_y = camera.apply(x * TILE_SIZE, y * TILE_SIZE)
                    screen.blit(image, (screen_x, screen_y))
    
    
    def is_collision(self, tile_x, tile_y):
        if tile_x < 0 or tile_y < 0:
            return True
        if tile_x >= self.tmx_data.width or tile_y >= self.tmx_data.height:
            return True
        
        margin = 8 if self.current_map == "campus" else 12
        for obj in self.collision_rects:
            tile_rect = pygame.Rect(
                tile_x * TILE_SIZE + margin,
                tile_y * TILE_SIZE + margin,
                TILE_SIZE - margin * 2,
                TILE_SIZE - margin * 2
            )
            if tile_rect.colliderect(obj):
                return True
        return False
    
    
    def is_grass(self, tile_x, tile_y):
        tile_rect = pygame.Rect(tile_x * TILE_SIZE, tile_y * TILE_SIZE,
                               TILE_SIZE, TILE_SIZE)
        for grass_rect in self.grass_rects:
            if tile_rect.colliderect(grass_rect):
                return True
        return False
    
    
    def check_transition(self, tile_x, tile_y):
        center_x = tile_x * TILE_SIZE + TILE_SIZE // 2
        center_y = tile_y * TILE_SIZE + TILE_SIZE // 2
        for transition in self.transitions:
            if transition["rect"].collidepoint(center_x, center_y):
                return transition
        return None

    def check_transition_at_px(self, px, py):
        """Pixel-precise transition check for sub-tile movement."""
        for transition in self.transitions:
            if transition["rect"].collidepoint(px, py):
                return transition
        return None
    
    
    def get_spawn_position(self, spawn_type="player"):
        if spawn_type in self.spawns and len(self.spawns[spawn_type]) > 0:
            spawn = self.spawns[spawn_type][0]
            return (spawn["x"], spawn["y"])
        return (0, 0)
    
    
    def get_spawns_by_type(self, spawn_type):
        return self.spawns.get(spawn_type, [])
    
    
    def get_map_size(self):
        return (self.width, self.height)
    
    
    def get_npcs_data(self):
        npcs = []
        for spawn_type in ["nurse", "shopkeeper", "professor", "quest", "trainer"]:
            npcs.extend(self.spawns.get(spawn_type, []))
        return npcs
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _parse_collisions(self):
        self.collision_rects = []
        for layer in self.tmx_data.layers:
            if layer.name in ["Collision", "Collisions"]:
                if isinstance(layer, pytmx.TiledObjectGroup):
                    for obj in layer:
                        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                        self.collision_rects.append(rect)
    
    
    def _parse_grass(self):
        self.grass_rects = []
        for layer in self.tmx_data.layers:
            if layer.name == "Grass":
                if isinstance(layer, pytmx.TiledObjectGroup):
                    for obj in layer:
                        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                        self.grass_rects.append(rect)
    
    
    def _parse_transitions(self, point_size=None):
        default = point_size or TILE_SIZE
        self.transitions = []
        for layer in self.tmx_data.layers:
            if layer.name == "Transitions":
                if isinstance(layer, pytmx.TiledObjectGroup):
                    for obj in layer:
                        w = obj.width if obj.width > 0 else default
                        h = obj.height if obj.height > 0 else default
                        # Point objects (w=h=0 in Tiled): center the rect on the
                        # object's coordinates so the trigger tile is the one
                        # where the point was placed, not the tile below-right.
                        if obj.width == 0 and obj.height == 0:
                            rx = int(obj.x) - w // 2
                            ry = int(obj.y) - h // 2
                        else:
                            rx, ry = int(obj.x), int(obj.y)
                        raw_zone = obj.properties.get("target_zone", "")
                        target_zone = raw_zone.strip('"') if isinstance(raw_zone, str) else raw_zone
                        transition = {
                            "rect": pygame.Rect(rx, ry, w, h),
                            "target_zone": target_zone,
                            "spawn_x": obj.properties.get("spawn_x", 0),
                            "spawn_y": obj.properties.get("spawn_y", 0)
                        }
                        self.transitions.append(transition)
    
    
    def _parse_spawns(self):
        self.spawns = {}
        for layer in self.tmx_data.layers:
            if layer.name == "Spawns":
                if isinstance(layer, pytmx.TiledObjectGroup):
                    for obj in layer:
                        # Strip surrounding quotes added by Tiled ("value" → value)
                        props = {}
                        for k, v in obj.properties.items():
                            props[k] = v.strip('"') if isinstance(v, str) else v

                        spawn_type = props.get("spawn_type", props.get("type", "unknown"))

                        # Snap pixel position to tile grid (Tiled places point
                        # objects at arbitrary sub-pixel positions).
                        snapped_x = int(obj.x // TILE_SIZE) * TILE_SIZE
                        snapped_y = int(obj.y // TILE_SIZE) * TILE_SIZE
                        spawn_data = {
                            "id": obj.id,
                            "x": snapped_x,
                            "y": snapped_y,
                            "type": spawn_type,
                            "name": props.get("npc_name", props.get("name", "NPC")),
                        }
                        # Merge remaining props (level, direction, sprite, etc.)
                        for k, v in props.items():
                            if k not in ("spawn_type", "npc_name"):
                                spawn_data.setdefault(k, v)

                        if spawn_type not in self.spawns:
                            self.spawns[spawn_type] = []
                        self.spawns[spawn_type].append(spawn_data)