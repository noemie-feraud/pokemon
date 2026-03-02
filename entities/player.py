# =============================================================================
# PLAYER.PY - PLAYER CLASS
# =============================================================================

import pygame
from config.settings import TILE_SIZE, PLAYER_SPRITES_DIR
from entities.team import Team
from entities.storage import Storage
from entities.pokedex import Pokedex


class Player:
    def __init__(self, character_id, name, start_x=0, start_y=0):
        self.character_id = character_id
        self.name = name
        self.x = start_x
        self.y = start_y
        self.direction = "down"
        self.speed = 160
        self.is_moving = False
        self.target_x = start_x
        self.target_y = start_y
        self.rect = pygame.Rect(self.x, self.y, TILE_SIZE, TILE_SIZE)
        self.current_zone = "campus"   # modifié pour utiliser outside temporairement
        self.sprites = {}
        self._load_sprites()
        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed = 0.15
        self.team = Team()
        self.storage = Storage()
        self.pokedex = Pokedex()
        self.credits = 0
        self.trainers_beaten = []
        self.quests_completed = []
        self.active_quests = []
        self.play_time = 0
        self.starter_received = False
        self.must_teleport_to_center = False
        self.tournament_won = False
        self.challenges = {}           # npc_id → {"target": int, "reward": int}
        self.challenges_completed = [] # [npc_id, ...]
    
    def _crop_sprite(self, img):
        """Crop a large canvas image down to its non-transparent bounding box."""
        bbox = img.get_bounding_rect()
        if bbox.width == 0 or bbox.height == 0:
            return img
        cropped = pygame.Surface((bbox.width, bbox.height), pygame.SRCALPHA)
        cropped.blit(img, (0, 0), bbox)
        return cropped

    def _load_sprites(self):
        # Map character_id to sprite file prefix
        char_names = {1: "linus", 2: "ada"}
        char_name = char_names.get(self.character_id)

        # Map game direction → sprite file suffix, and the 3 frame filenames
        # Frame order: 0=idle, 1=walk step 1, 2=walk step 2
        dir_frames = {
            "down":  [f"{char_name}_front.png",       f"{char_name}_front_walk.png",  f"{char_name}_front_walk.png"],
            "up":    [f"{char_name}_back.png",         f"{char_name}_back_walk1.png",  f"{char_name}_back_walk2.png"],
            "left":  [f"{char_name}_left.png",         f"{char_name}_left_walk.png",   f"{char_name}_left_walk.png"],
            "right": [f"{char_name}_right.png",        f"{char_name}_right_walk.png",  f"{char_name}_right_walk.png"],
        }

        for direction in ["down", "up", "left", "right"]:
            self.sprites[direction] = []

            if char_name and char_name in [n for n in char_names.values()]:
                # Use name-based file convention
                for filename in dir_frames[direction]:
                    path = PLAYER_SPRITES_DIR / filename
                    if path.exists():
                        try:
                            img = pygame.image.load(str(path)).convert_alpha()
                            img = self._crop_sprite(img)
                            self.sprites[direction].append(img)
                        except Exception:
                            self.sprites[direction].append(self._create_placeholder())
                    else:
                        # Fallback: reuse previous frame or placeholder
                        if self.sprites[direction]:
                            self.sprites[direction].append(self.sprites[direction][0])
                        else:
                            self.sprites[direction].append(self._create_placeholder())
            else:
                # Legacy fallback: {character_id}/{direction}_{i}.png
                base_dir = PLAYER_SPRITES_DIR / str(self.character_id)
                for i in range(3):
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
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        if self.character_id == 1:
            surface.fill((0, 100, 200))
        else:
            surface.fill((200, 100, 200))
        return surface
    
    def move(self, direction, map_manager):
        self.direction = direction

        target_tile_x, target_tile_y = self.get_tile_position()
        if direction == "up":
            target_tile_y -= 1
        elif direction == "down":
            target_tile_y += 1
        elif direction == "left":
            target_tile_x -= 1
        elif direction == "right":
            target_tile_x += 1

        if map_manager.tmx_data:
            w = map_manager.tmx_data.width
            h = map_manager.tmx_data.height
            if not (0 <= target_tile_x < w and 0 <= target_tile_y < h):
                return
            if map_manager.is_collision(target_tile_x, target_tile_y):
                # Transition tiles are always walkable even if a collision barely overlaps
                if map_manager.check_transition(target_tile_x, target_tile_y) is None:
                    return

        self.target_x = target_tile_x * TILE_SIZE
        self.target_y = target_tile_y * TILE_SIZE
        self.is_moving = True

    def move_subpixel(self, direction, step_px, map_manager):
        """Move in step_px pixel increments instead of a full tile."""
        self.direction = direction
        dx = {"left": -1, "right": 1}.get(direction, 0)
        dy = {"up": -1, "down": 1}.get(direction, 0)
        target_x = self.x + dx * step_px
        target_y = self.y + dy * step_px

        if map_manager.tmx_data:
            tx = int(target_x) // TILE_SIZE
            ty = int(target_y) // TILE_SIZE
            if not (0 <= tx < map_manager.tmx_data.width and
                    0 <= ty < map_manager.tmx_data.height):
                return
            # Collision check only when crossing into a new tile
            cur_tx = int(self.x) // TILE_SIZE
            cur_ty = int(self.y) // TILE_SIZE
            if tx != cur_tx or ty != cur_ty:
                if map_manager.is_collision(tx, ty):
                    if map_manager.check_transition(tx, ty) is None:
                        return

        self.target_x = target_x
        self.target_y = target_y
        self.is_moving = True

    def stop(self):
        self.is_moving = False
        self.frame_index = 0
        self.anim_timer = 0

    def update(self, dt):
        self.play_time += dt
        if self.is_moving:
            move_dist = self.speed * dt
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = (dx ** 2 + dy ** 2) ** 0.5

            if dist <= move_dist:
                self.x = self.target_x
                self.y = self.target_y
                self.rect.x, self.rect.y = int(self.x), int(self.y)
                self.is_moving = False
                self.frame_index = 0
                self.anim_timer = 0
            else:
                ratio = move_dist / dist
                self.x += dx * ratio
                self.y += dy * ratio
                self.anim_timer += dt
                if self.anim_timer >= self.anim_speed:
                    self.anim_timer = 0
                    self.frame_index += 1
                    num_frames = len(self.sprites[self.direction])
                    if self.frame_index >= num_frames:
                        self.frame_index = 0

            self.rect.x, self.rect.y = int(self.x), int(self.y)
    
    def get_sprite(self):
        frames = self.sprites[self.direction]
        if self.frame_index < len(frames):
            return frames[self.frame_index]
        return frames[0]
    
    def get_center(self):
        return (self.x + TILE_SIZE // 2, self.y + TILE_SIZE // 2)
    
    def set_position(self, x, y):
        self.x, self.y = x, y
        self.rect.x, self.rect.y = x, y
    
    def set_tile_position(self, tile_x, tile_y):
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE
        self.rect.x, self.rect.y = self.x, self.y
    
    def get_tile_position(self):
        return (self.x // TILE_SIZE, self.y // TILE_SIZE)
    
    def get_tile_in_front(self):
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
        if trainer_id not in self.trainers_beaten:
            self.trainers_beaten.append(trainer_id)
    
    def is_trainer_defeated(self, trainer_id):
        return trainer_id in self.trainers_beaten
    
    def draw(self, screen, camera):
        sprite = self.get_sprite()
        if sprite is None:
            return
        screen_x, screen_y = camera.apply(self.x, self.y)
        screen.blit(sprite, (screen_x, screen_y))
    
    def to_dict(self):
        return {
            "trainer": {
                "name": self.name,
                "character_id": self.character_id,
                "position": {"zone": self.current_zone, "x": self.x, "y": self.y}
            },
            "team": self.team.to_list(),
            "storage": self.storage.to_list(),
            "credits": self.credits,
            "trainers_beaten": self.trainers_beaten,
            "quests_completed": self.quests_completed,
            "quests_active": self.active_quests,
            "challenges": self.challenges,
            "challenges_completed": self.challenges_completed,
            "pokedex": self.pokedex.to_dict(),
            "play_time": self.play_time,
            "starter_received": self.starter_received,
            "tournament_won": self.tournament_won
        }
    
    @classmethod
    def from_save(cls, data):
        from entities.pokemon import Pokemon
        trainer_data = data["trainer"]
        player = cls(
            character_id=trainer_data["character_id"],
            name=trainer_data["name"],
            start_x=trainer_data["position"]["x"],
            start_y=trainer_data["position"]["y"]
        )
        player.current_zone = trainer_data["position"]["zone"]
        player.credits = data.get("credits", 0)
        player.trainers_beaten = data.get("trainers_beaten", [])
        player.quests_completed = data.get("quests_completed", [])
        player.active_quests = data.get("quests_active", [])
        player.challenges = data.get("challenges", {})
        player.challenges_completed = data.get("challenges_completed", [])
        player.play_time = data.get("play_time", 0)
        player.starter_received = data.get("starter_received", False)
        player.tournament_won = data.get("tournament_won", False)
        player.pokedex = Pokedex.from_dict(data.get("pokedex", {}))
        # Restore team
        team_data = data.get("team", [])
        pokemon_list = [Pokemon(pdata) for pdata in team_data]
        player.team = Team(pokemon_list)
        return player
    
    def __str__(self):
        return f"Player '{self.name}' (char {self.character_id}) - Zone: {self.current_zone} - Credits: {self.credits}"