# =============================================================================
# NPC.PY - BASE NPC CLASS
# =============================================================================
#
# Base class for all non-player characters.
# Handles: position, sprite, direction, dialogue, interaction.

import pygame
from config.settings import TILE_SIZE, NPC_SPRITES_DIR, PROJECT_ROOT


# =============================================================================
# NPC BASE CLASS
# =============================================================================

class NPC:
    """
    Base class for all NPCs.
    Child classes override on_dialogue_end() for specific behavior.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, data):
        """
        Initialize NPC from JSON data.
        
        Args:
            data: dict from npcs.json or trainers.json
        """
        
        # --- IDENTITY ---
        self.id = data["id"]
        self.name = data.get("name", "NPC")
        self.npc_type = data.get("type", "ambient")  # "nurse", "shopkeeper", etc.
        
        # --- POSITION ---
        self.x = data["x"]
        self.y = data["y"]
        self.direction = data.get("direction", "down")
        self.zone = data.get("zone", "campus")
        
        # --- COLLISION RECTANGLE ---
        # NPC occupies one tile on map.
        # Player cannot walk on NPCs (CA-13).
        self.rect = pygame.Rect(self.x, self.y, TILE_SIZE, TILE_SIZE)
        
        # --- DIALOGUES ---
        # Dictionary of line lists.
        # "default": basic dialogue when interacting
        # Child classes may have other keys ("after", "quest_active", etc.)
        self.dialogues = data.get("dialogues", {"default": ["..."]})
        
        # --- SPRITES (directional, same pattern as player) ---
        self.sprites = {}
        self._load_sprites(data)

        # --- INTERACTION FLAG ---
        # Some NPCs are only interactive once.
        # Default: everyone is re-interactive.
        self.interactive = True
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _crop_sprite(self, img):
        """Crop transparent borders — same as player.py."""
        bbox = img.get_bounding_rect()
        if bbox.width == 0 or bbox.height == 0:
            return img
        cropped = pygame.Surface((bbox.width, bbox.height), pygame.SRCALPHA)
        cropped.blit(img, (0, 0), bbox)
        return cropped

    def _load_sprites(self, data):
        """Load directional sprites — same pattern as player, but from NPC_SPRITES_DIR.

        Two cases:
        - sprite = prefix (e.g. "f3_jade")   → loads prefix_front/back/left/right.png
        - sprite = full path (ends with .png) → single image used for all directions
        """
        sprite_val = data.get("sprite", None)

        if not sprite_val:
            for d in ("down", "up", "left", "right"):
                self.sprites[d] = self._create_placeholder()
            return

        # Single-file sprite (full path ending in .png)
        if sprite_val.endswith(".png"):
            full_path = PROJECT_ROOT / sprite_val
            img = None
            if full_path.exists():
                try:
                    img = self._crop_sprite(pygame.image.load(str(full_path)).convert_alpha())
                except Exception:
                    pass
            for d in ("down", "up", "left", "right"):
                self.sprites[d] = img if img else self._create_placeholder()
            return

        # Prefix-based directional sprites
        dir_files = {
            "down":  f"{sprite_val}_front.png",
            "up":    f"{sprite_val}_back.png",
            "left":  f"{sprite_val}_left.png",
            "right": f"{sprite_val}_right.png",
        }
        for direction, filename in dir_files.items():
            path = NPC_SPRITES_DIR / filename
            if path.exists():
                try:
                    img = pygame.image.load(str(path)).convert_alpha()
                    self.sprites[direction] = self._crop_sprite(img)
                    continue
                except Exception:
                    pass
            self.sprites[direction] = None  # resolved after loop

        # Fallback: missing directions use the front sprite, then placeholder
        fallback = self.sprites.get("down") or next(
            (s for s in self.sprites.values() if s is not None), None
        )
        for d in ("down", "up", "left", "right"):
            if self.sprites.get(d) is None:
                self.sprites[d] = fallback if fallback else self._create_placeholder()
    
    
    def _create_placeholder(self):
        """Create placeholder sprite (colored rectangle)."""
        colors = {
            "nurse": (255, 150, 150),      # pink
            "shopkeeper": (150, 255, 150),  # green
            "trainer": (255, 100, 100),     # red
            "professor": (100, 100, 255),   # blue
            "quest": (255, 255, 100),       # yellow
            "ambient": (180, 180, 180)      # gray
        }
        color = colors.get(self.npc_type, (180, 180, 180))
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surface.fill(color)
        return surface
    
    
    def _file_exists(self, path):
        """Check if a file exists."""
        return (PROJECT_ROOT / path).exists()
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def get_dialogue(self):
        """
        Return dialogue lines to display.
        Default: returns "default" dialogue.
        
        Child classes override this to choose appropriate dialogue
        based on context.
        
        Returns:
            list of strings (each string = one line)
        """
        return self.dialogues.get("default", ["..."])
    
    
    def face_player(self, player_direction):
        """
        Turn NPC to face the player.
        
        Args:
            player_direction: direction player is facing
        """
        opposite = {
            "up": "down",
            "down": "up",
            "left": "right",
            "right": "left"
        }
        self.direction = opposite.get(player_direction, "down")
    
    
    def on_interact(self, game_manager):
        """
        Called when player interacts with this NPC.
        Default behavior:
        1. Face the player
        2. Start dialogue
        
        Args:
            game_manager: Game object reference
        """
        if not self.interactive:
            return
        
        # Face player
        self.face_player(game_manager.player.direction)
        
        # Get dialogue lines
        lines = self.get_dialogue()
        
        # Start dialogue
        from states.state_dialogue import StateDialogue
        
        dialogue_state = StateDialogue(
            game_manager,
            lines,
            npc=self,
            callback=self.on_dialogue_end
        )
        game_manager.state_manager.push(dialogue_state)
    
    
    def on_dialogue_end(self, game_manager):
        """
        Called when dialogue ends (player went through all lines).
        Default: nothing.
        
        This is the method child classes override:
        - NPCNurse → heals team
        - NPCShopkeeper → opens shop (pushes StateShop)
        - NPCProfessor → gives starter (pushes StarterSelect)
        - NPCQuest → checks quest or gives new one
        - NPCTrainer → starts combat (pushes StateCombat)
        - NPCAmbient → nothing (just dialogue)
        """
        pass
    
    
    def draw(self, screen, camera):
        """
        Draw NPC on screen using camera.
        
        Args:
            screen: Pygame surface
            camera: Camera object for world→screen conversion
        """
        sprite = self.sprites.get(self.direction) or self.sprites.get("down")
        if sprite is None:
            return

        screen_x, screen_y = camera.apply(self.x, self.y)
        screen.blit(sprite, (screen_x, screen_y))
    
    
    def get_collision_rect(self):
        """Return collision rectangle."""
        return self.rect
    
    
    def is_near_player(self, player):
        """
        Check if player is close enough to interact.
        Max distance: 1 tile (32px) in facing direction.
        
        Args:
            player: Player object
        
        Returns:
            True if interaction possible, False otherwise
        """
        # Calculate tile in front of player
        target_x = player.x
        target_y = player.y
        
        if player.direction == "up":
            target_y = player.y - TILE_SIZE
        elif player.direction == "down":
            target_y = player.y + TILE_SIZE
        elif player.direction == "left":
            target_x = player.x - TILE_SIZE
        elif player.direction == "right":
            target_x = player.x + TILE_SIZE
        
        target_rect = pygame.Rect(target_x, target_y, TILE_SIZE, TILE_SIZE)
        return self.rect.colliderect(target_rect)
    
    
    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------
    
    def to_dict(self):
        """
        Serialize for debug.
        Actual state (defeated trainers, etc.) is stored in Player, not NPC.
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.npc_type,
            "zone": self.zone,
            "x": self.x,
            "y": self.y,
            "direction": self.direction
        }
    
    
    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------
    
    @property
    def tile_x(self):
        """Return tile X coordinate."""
        return self.x // TILE_SIZE
    
    
    @property
    def tile_y(self):
        """Return tile Y coordinate."""
        return self.y // TILE_SIZE
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """Debug representation."""
        return f"NPC '{self.name}' ({self.npc_type}) @ {self.zone} ({self.x}, {self.y})"