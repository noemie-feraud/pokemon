# =============================================================================
# PLAYER.PY - PLAYER CLASS
# =============================================================================
#
# Represents the player - the trainer controlled in the game.
# Central object that holds everything belonging to the player:
# team, storage, inventory, credits, position, sprite, defeated trainers.

import pygame
from config.settings import TILE_SIZE, PLAYER_SPRITES_DIR
from entities.team import Team
from entities.storage import Storage


# =============================================================================
# PLAYER CLASS
# =============================================================================

class Player:
    """
    Represents the player. Holds everything belonging to them:
    team, storage, inventory, credits, position, sprites.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, character_id, name, start_x=0, start_y=0):
        """
        Initialize player.
        
        Args:
            character_id: 1 or 2, chosen character
            name: trainer name
            start_x, start_y: starting pixel position on map
        """
        
        # --- IDENTITY ---
        self.character_id = character_id      # 1 or 2
        self.name = name                      # trainer name
        
        # --- POSITION & MOVEMENT ---
        # Position in pixels on map (sprite top-left)
        self.x = start_x
        self.y = start_y
        
        # Direction: determines which sprite to display
        # "down" by default (Pokemon always start facing down)
        self.direction = "down"
        
        # Movement speed in pixels per second
        # 160 px/s = 5 tiles per second (160 / 32 = 5)
        self.speed = 160
        
        # Flag: is player currently moving?
        self.is_moving = False
        
        # --- COLLISION RECTANGLE ---
        # Rect is 32×32 (one tile), positioned at sprite's FEET.
        # Sprite itself can be larger (32×48), but collision only for feet.
        # This allows player to appear "behind" obstacles visually.
        self.rect = pygame.Rect(self.x, self.y, TILE_SIZE, TILE_SIZE)
        
        # --- CURRENT ZONE ---
        self.current_zone = "campus"   # starting zone
        
        # --- SPRITES ---
        # Dictionary of sprite lists per direction.
        # Each direction has multiple frames for walk animation.
        # Example:
        #   {
        #       "down": [sprite_idle, sprite_walk1, sprite_walk2],
        #       "up": [...],
        #       "left": [...],
        #       "right": [...]
        #   }
        self.sprites = {}
        self._load_sprites()
        
        # --- ANIMATION ---
        # frame_index: which sprite in list to display
        # anim_timer: time counter to alternate frames
        # anim_speed: time between frames in seconds
        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed = 0.15    # ~7 frames per second
        
        # --- TEAM & STORAGE ---
        self.team = Team()
        self.storage = Storage()
        
        # --- ECONOMY ---
        # Will be replaced by real objects later
        self.credits = 0
        # self.inventory = Inventory()
        # self.credits_manager = CreditsManager()
        
        # --- PROGRESSION ---
        # IDs of defeated trainers
        self.trainers_beaten = []
        
        # Quest IDs
        self.quests_completed = []
        self.active_quests = []
        
        # Total play time in seconds (for save display)
        self.play_time = 0
        
        # Starter received flag
        self.starter_received = False
        
        # Teleport flag (after defeat)
        self.must_teleport_to_center = False
        
        # Tournament won flag
        self.tournament_won = False
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _load_sprites(self):
        """Load player sprites from assets folder."""
        base_dir = PLAYER_SPRITES_DIR / str(self.character_id)
        directions = ["down", "up", "left", "right"]
        
        for direction in directions:
            self.sprites[direction] = []
            
            for i in range(3):  # 3 frames per direction
                path = base_dir / f"{direction}_{i}.png"
                
                if path.exists():
                    try:
                        img = pygame.image.load(str(path)).convert_alpha()
                        self.sprites[direction].append(img)
                    except Exception:
                        self.sprites[direction].append(self._create_placeholder())
                else:
                    self.sprites[direction].append(self._create_placeholder())
    
    
    def _create_placeholder(self):
        """Create placeholder sprite if image not found."""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        if self.character_id == 1:  # Linus
            surface.fill((0, 100, 200))      # blue
        else:  # Ada
            surface.fill((200, 100, 200))    # purple
        return surface
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def move(self, direction, dt, map_manager):
        """
        Move player in given direction.
        Called by state_exploration.py when movement key is pressed.
        
        Args:
            direction: "up", "down", "left", "right"
            dt: delta time in seconds
            map_manager: for collision checks
        """
        self.direction = direction
        self.is_moving = True
        
        # Calculate movement in pixels
        move_dist = self.speed * dt
        
        new_x = self.x
        new_y = self.y
        
        if direction == "up":
            new_y = self.y - move_dist
        elif direction == "down":
            new_y = self.y + move_dist
        elif direction == "left":
            new_x = self.x - move_dist
        elif direction == "right":
            new_x = self.x + move_dist
        
        # Test collision on X axis
        test_rect_x = pygame.Rect(new_x, self.y, TILE_SIZE, TILE_SIZE)
        if not map_manager.is_collision(test_rect_x):
            self.x = new_x
        
        # Test collision on Y axis
        test_rect_y = pygame.Rect(self.x, new_y, TILE_SIZE, TILE_SIZE)
        if not map_manager.is_collision(test_rect_y):
            self.y = new_y
        
        # Update collision rect
        self.rect.x = self.x
        self.rect.y = self.y
    
    
    def stop(self):
        """Stop player movement."""
        self.is_moving = False
        self.frame_index = 0
        self.anim_timer = 0
    
    
    def update(self, dt):
        """
        Update player animation.
        Called every frame by state_exploration.py.
        
        Args:
            dt: delta time in seconds
        """
        # Count play time
        self.play_time += dt
        
        # Walk animation
        if self.is_moving:
            self.anim_timer += dt
            
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.frame_index += 1
                
                # Loop through available frames
                num_frames = len(self.sprites[self.direction])
                if self.frame_index >= num_frames:
                    self.frame_index = 0
    
    
    def get_sprite(self):
        """Return current sprite to display."""
        frames = self.sprites[self.direction]
        
        if self.frame_index < len(frames):
            return frames[self.frame_index]
        return frames[0]
    
    
    def get_center(self):
        """
        Return player center position in pixels.
        Used by camera.update() to center on player.
        """
        return (self.x + TILE_SIZE // 2, self.y + TILE_SIZE // 2)
    
    
    def set_position(self, x, y):
        """Teleport player to given pixel position."""
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y
    
    
    def set_tile_position(self, tile_x, tile_y):
        """Set position from tile coordinates."""
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE
        self.rect.x = self.x
        self.rect.y = self.y
    
    
    def get_tile_position(self):
        """Return current tile coordinates."""
        return (self.x // TILE_SIZE, self.y // TILE_SIZE)
    
    
    def get_tile_in_front(self):
        """Return tile coordinates in front of player."""
        tile_x, tile_y = self.get_tile_position()
        
        if self.direction == "up":
            return (tile_x, tile_y - 1)
        elif self.direction == "down":
            return (tile_x, tile_y + 1)
        elif self.direction == "left":
            return (tile_x - 1, tile_y)
        elif self.direction == "right":
            return (tile_x + 1, tile_y)
        return (tile_x, tile_y)
    
    
    def add_defeated_trainer(self, trainer_id):
        """Mark a trainer as defeated."""
        if trainer_id not in self.trainers_beaten:
            self.trainers_beaten.append(trainer_id)
    
    
    def is_trainer_defeated(self, trainer_id):
        """Check if a trainer has been defeated."""
        return trainer_id in self.trainers_beaten
    
    
    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------
    
    def to_dict(self):
        """
        Convert all player data to dict for JSON save.
        Calls to_list() on team and storage, which call to_dict() on each Pokemon.
        """
        return {
            "trainer": {
                "name": self.name,
                "character_id": self.character_id,
                "position": {
                    "zone": self.current_zone,
                    "x": self.x,
                    "y": self.y
                }
            },
            "team": self.team.to_list(),
            "storage": self.storage.to_list(),
            # "inventory": self.inventory.to_dict(),   # later
            "credits": self.credits,
            "trainers_beaten": self.trainers_beaten,
            "quests_completed": self.quests_completed,
            "quests_active": self.active_quests,
            "pokedex": {},  # will be filled by pokedex.py
            "play_time": self.play_time,
            "starter_received": self.starter_received,
            "tournament_won": self.tournament_won
        }
    
    
    @classmethod
    def from_save(cls, data):
        """
        Create Player object from save dict.
        Inverse of to_dict().
        
        Args:
            data: save dict
        
        Returns:
            Player instance
        """
        trainer_data = data["trainer"]
        player = cls(
            character_id=trainer_data["character_id"],
            name=trainer_data["name"],
            start_x=trainer_data["position"]["x"],
            start_y=trainer_data["position"]["y"]
        )
        
        player.current_zone = trainer_data["position"]["zone"]
        
        # Team and storage will be rebuilt by caller with Pokemon.from_data()
        # We just store raw lists here, caller will convert
        
        player.credits = data.get("credits", 0)
        player.trainers_beaten = data.get("trainers_beaten", [])
        player.quests_completed = data.get("quests_completed", [])
        player.active_quests = data.get("quests_active", [])
        player.play_time = data.get("play_time", 0)
        player.starter_received = data.get("starter_received", False)
        player.tournament_won = data.get("tournament_won", False)
        
        return player
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """Debug representation."""
        return f"Player '{self.name}' (char {self.character_id}) - Zone: {self.current_zone} - Credits: {self.credits}"