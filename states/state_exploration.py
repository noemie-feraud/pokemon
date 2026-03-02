# =============================================================================
# STATE_EXPLORATION.PY - EXPLORATION STATE
# =============================================================================

import os
import pygame
import random
from states.state import State
from ui.hud import HUD
from core.camera import Camera
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    ENCOUNTER_RATE, WILD_POKEMON_LEVELS
)

class StateExploration(State):
    """
    Main exploration state.
    Player moves on the map and interacts with the world.
    """

    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.transparent = False
        self.camera = Camera()
        self._view_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.hud = HUD(game_manager)
        self.npcs = []
        self.pending_combat = False
        self.pending_transition = False
        self.nearby_npc = None
        self._bubble_font = None
        self._idle_timer = 0.0
        self._thought_show_until = 0  # ms timestamp (pygame.time.get_ticks)
        self._load_current_zone()
    
    def _load_current_zone(self):
        """Load the player's current zone. Returns True on success, False on failure."""
        player = self.game_manager.player
        map_manager = self.game_manager.map_manager
        substep = self._ZONE_SUBSTEP.get(player.current_zone)
        point_size = substep * 2 if substep else TILE_SIZE
        ok = map_manager.load_map(player.current_zone, self.camera,
                                  transition_point_size=point_size)

        if not ok or map_manager.tmx_data is None:
            return False

        # Zoom automatique : on cherche le zoom minimal qui évite les bordures noires.
        map_w = map_manager.tmx_data.width * TILE_SIZE
        map_h = map_manager.tmx_data.height * TILE_SIZE
        zoom = max(
            (SCREEN_WIDTH + map_w - 1) // map_w,
            (SCREEN_HEIGHT + map_h - 1) // map_h,
            1
        )
        view_w = SCREEN_WIDTH // zoom
        view_h = SCREEN_HEIGHT // zoom
        self.camera = Camera(viewport_width=view_w, viewport_height=view_h)
        self.camera.set_map_size(map_manager.tmx_data.width, map_manager.tmx_data.height)
        self._view_surface = pygame.Surface((view_w, view_h))

        spawn = map_manager.get_spawn_position("player")
        if spawn != (0, 0):
            player.set_position(spawn[0], spawn[1])

        self.npcs = self._create_zone_npcs(player.current_zone)
        self._idle_timer = 0.0
        self._thought_show_until = 0
        return True
    
    def _create_zone_npcs(self, zone):
        from entities.npc_nurse import NPCNurse
        from entities.npc_shopkeeper import NPCShopkeeper
        from entities.npc_professor import NPCProfessor
        from entities.npc_quest import NPCQuest
        from entities.npc_trainer import NPCTrainer

        map_manager = self.game_manager.map_manager
        npcs_data = map_manager.get_npcs_data()
        npcs = []
        for data in npcs_data:
            npc_type = data.get("type", "")
            if npc_type == "nurse":
                npcs.append(NPCNurse(data))
            elif npc_type == "shopkeeper":
                npcs.append(NPCShopkeeper(data))
            elif npc_type == "professor":
                npcs.append(NPCProfessor(data))
            elif npc_type == "quest":
                npcs.append(NPCQuest(data))
            elif npc_type == "trainer":
                npcs.append(NPCTrainer(data))
        return npcs
    
    def on_enter(self):
        player = self.game_manager.player
        if getattr(player, 'must_teleport_to_center', False):
            player.must_teleport_to_center = False
            player.current_zone = "pokemon_center"
            self._load_current_zone()
            player.set_tile_position(2, 2)  # centre bas du pokemon center
        zone = player.current_zone
        self.game_manager.audio_manager.play_music(zone)
        self.pending_combat = False
        self.pending_transition = False
    
    def handle_events(self, events):
        player = self.game_manager.player
        if player.is_moving:
            return
        
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_SPACE:
                self._try_interaction()
            elif event.key == pygame.K_ESCAPE:
                from states.state_menu_pause import StateMenuPause
                pause = StateMenuPause(self.game_manager)
                self.game_manager.state_manager.push(pause)
            elif event.key == pygame.K_i:
                from states.state_inventory import StateInventory
                inventory = StateInventory(self.game_manager)
                self.game_manager.state_manager.push(inventory)
            elif event.key == pygame.K_p:
                from states.state_team_screen import StateTeamScreen
                team = StateTeamScreen(self.game_manager)
                self.game_manager.state_manager.push(team)
    
    def update(self, dt):
        player = self.game_manager.player

        if player.is_moving:
            player.update(dt)
            self._idle_timer = 0.0
            if not player.is_moving:
                self._on_tile_arrival()
        else:
            self._check_direction_input()
            self._idle_timer += dt

        # Bulle de pensée : s'active après 2.5s d'immobilité, reste 30s
        now = pygame.time.get_ticks()
        if self._idle_timer >= 2.5 and now > self._thought_show_until:
            self._thought_show_until = now + 30_000

        self.game_manager.day_night_cycle.update(dt)
        self.hud.update(dt)
        pos_x, pos_y = player.x, player.y
        self.camera.update(pos_x, pos_y)

        for npc in self.npcs:
            if hasattr(npc, 'update'):
                npc.update(dt)

        self.nearby_npc = self._get_adjacent_npc()
    
    def _check_direction_input(self):
        keys = pygame.key.get_pressed()
        player = self.game_manager.player
        map_manager = self.game_manager.map_manager
        
        direction = None
        if keys[pygame.K_UP] or keys[pygame.K_z]:
            direction = "up"
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            direction = "down"
        elif keys[pygame.K_LEFT] or keys[pygame.K_q]:
            direction = "left"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction = "right"
        
        if direction is None:
            return

        substep = self._ZONE_SUBSTEP.get(player.current_zone)
        if substep:
            dx = {"left": -1, "right": 1}.get(direction, 0)
            dy = {"up": -1, "down": 1}.get(direction, 0)
            target_tile_x = int(player.x + dx * substep) // TILE_SIZE
            target_tile_y = int(player.y + dy * substep) // TILE_SIZE
            if self._npc_on_tile(target_tile_x, target_tile_y):
                player.direction = direction
                return
            player.move_subpixel(direction, substep, map_manager)
            return

        # Calculate the target tile and block if an NPC occupies it
        tile_x, tile_y = player.get_tile_position()
        if direction == "up":
            tile_y -= 1
        elif direction == "down":
            tile_y += 1
        elif direction == "left":
            tile_x -= 1
        elif direction == "right":
            tile_x += 1
        if self._npc_on_tile(tile_x, tile_y):
            player.direction = direction  # face the NPC without moving
            return

        player.move(direction, map_manager)
    
    def _npc_on_tile(self, tile_x, tile_y):
        for npc in self.npcs:
            npc_tile_x = npc.x // TILE_SIZE
            npc_tile_y = npc.y // TILE_SIZE
            if npc_tile_x == tile_x and npc_tile_y == tile_y:
                return True
        return False
    
    def _on_tile_arrival(self):
        player = self.game_manager.player
        map_manager = self.game_manager.map_manager
        tile_x, tile_y = player.get_tile_position()

        # Sub-tile zones: use player center pixel for precision,
        # so the transition only fires when physically at the trigger spot.
        if self._ZONE_SUBSTEP.get(player.current_zone):
            cx = int(player.x) + TILE_SIZE // 2
            cy = int(player.y) + TILE_SIZE // 2
            transition = map_manager.check_transition_at_px(cx, cy)
        else:
            transition = map_manager.check_transition(tile_x, tile_y)

        if transition is not None:
            self._execute_transition(transition)
            return

        if map_manager.is_grass(tile_x, tile_y):
            self._check_wild_encounter()
    
    def _execute_transition(self, transition):
        player = self.game_manager.player
        target_zone = transition["target_zone"]
        prev_zone = player.current_zone
        prev_x, prev_y = player.x, player.y

        player.current_zone = target_zone

        # Charger la map d'abord (définit le spawn par défaut)
        if not self._load_current_zone():
            player.current_zone = prev_zone
            player.set_position(prev_x, prev_y)
            return

        # Ensuite, appliquer le spawn de la transition (écrase le spawn par défaut)
        player.set_tile_position(transition["spawn_x"], transition["spawn_y"])

        self.hud.show_zone_name(player.current_zone)
        self.game_manager.audio_manager.play_music(player.current_zone)
        try:
            from core.save_manager import SaveManager
            if hasattr(self.game_manager, 'current_save_slot') and self.game_manager.current_save_slot is not None:
                SaveManager().auto_save(self.game_manager, self.game_manager.current_save_slot)
        except Exception:
            pass
    
    def _check_wild_encounter(self):
        if random.random() >= ENCOUNTER_RATE:
            return
        player = self.game_manager.player
        if not player.team.has_valid_pokemon:
            return
        wild_pokemon = self._generate_wild_pokemon(player.current_zone)
        from states.state_combat import StateCombat
        combat = StateCombat(self.game_manager, opponent_pokemon=wild_pokemon, combat_type="wild")
        self.game_manager.state_manager.push(combat)
    
    def _generate_wild_pokemon(self, zone):
        from entities.pokemon import Pokemon
        min_level, max_level = WILD_POKEMON_LEVELS.get(zone, (5, 10))
        level = random.randint(min_level, max_level)
        pokemon_id = random.randint(1, 9)
        pokemon = Pokemon.from_data(pokemon_id, level)
        return pokemon
    
    def _get_adjacent_npc(self):
        """Return the closest NPC within 1 tile (Manhattan), or None."""
        player = self.game_manager.player
        px, py = player.get_tile_position()
        closest = None
        closest_dist = float('inf')
        for npc in self.npcs:
            nx = npc.x // TILE_SIZE
            ny = npc.y // TILE_SIZE
            dist = abs(nx - px) + abs(ny - py)
            if 0 < dist <= 1 and dist < closest_dist:
                closest = npc
                closest_dist = dist
        return closest

    def _draw_npc_bubble(self, screen, npc):
        """Draw a contextual speech bubble above a nearby NPC."""
        if self._bubble_font is None:
            font_path = os.path.join("assets", "font", "Pokemon_Solid.ttf")
            if os.path.exists(font_path):
                self._bubble_font = pygame.font.Font(font_path, 13)
            else:
                self._bubble_font = pygame.font.Font(None, 17)

        player = self.game_manager.player
        is_trainer = hasattr(npc, 'is_trainer') and npc.is_trainer

        if is_trainer and not player.is_trainer_defeated(npc.id) \
                and player.team.has_valid_pokemon:
            label = "ESPACE - Combat"
            accent = (210, 60, 50)
        elif npc.npc_type == "nurse":
            label = "+ Soins"
            accent = (200, 80, 160)
        elif npc.npc_type == "shopkeeper":
            label = "$ Boutique"
            accent = (60, 170, 80)
        else:
            label = "Parler"
            accent = (80, 120, 200)

        # World pos → view surface pos → scaled screen pos
        vx, vy = self.camera.apply(npc.x, npc.y)
        zoom_x = SCREEN_WIDTH / self._view_surface.get_width()
        zoom_y = SCREEN_HEIGHT / self._view_surface.get_height()
        sx = int(vx * zoom_x)
        sy = int(vy * zoom_y)
        tile_px = int(TILE_SIZE * zoom_x)

        text_surf = self._bubble_font.render(label, True, (20, 20, 20))
        tw, th = text_surf.get_size()
        pad_x, pad_y = 8, 4
        bw = tw + pad_x * 2
        bh = th + pad_y * 2
        tail_h = 6

        bx = sx + tile_px // 2 - bw // 2
        by = sy - bh - tail_h - 2
        bx = max(4, min(bx, SCREEN_WIDTH - bw - 4))
        by = max(4, by)

        surf = pygame.Surface((bw + 2, bh + tail_h + 2), pygame.SRCALPHA)

        # Drop shadow
        pygame.draw.rect(surf, (0, 0, 0, 50), (2, 2, bw, bh), border_radius=5)
        # White fill
        pygame.draw.rect(surf, (252, 252, 250, 235), (0, 0, bw, bh), border_radius=5)
        # Accent border
        pygame.draw.rect(surf, (*accent, 210), (0, 0, bw, bh), width=2, border_radius=5)
        # Tail triangle
        tc = bw // 2
        pygame.draw.polygon(surf, (252, 252, 250, 235), [(tc - 5, bh), (tc + 5, bh), (tc, bh + tail_h)])
        pygame.draw.polygon(surf, (*accent, 210), [(tc - 5, bh), (tc + 5, bh), (tc, bh + tail_h)], 1)
        # Text
        surf.blit(text_surf, (pad_x, pad_y))

        screen.blit(surf, (bx, by))

    def _check_trainers(self):
        player = self.game_manager.player
        for npc in self.npcs:
            if not hasattr(npc, 'is_trainer') or not npc.is_trainer:
                continue
            if player.is_trainer_defeated(npc.id):
                continue
            if npc.is_player_in_vision(player, self.game_manager):
                self._start_trainer_combat(npc)
                return True
        return False
    
    def _start_trainer_combat(self, trainer):
        if not self.game_manager.player.team.has_valid_pokemon:
            return
        opponent_pokemon = trainer.team.get_first_valid()
        if opponent_pokemon is None:
            return
        from states.state_combat import StateCombat
        combat = StateCombat(
            self.game_manager,
            opponent_pokemon=opponent_pokemon,
            combat_type="trainer",
            trainer=trainer
        )
        self.game_manager.state_manager.push(combat)
    
    def _try_interaction(self):
        # Use the NPC already identified as nearby (same one that shows the bubble).
        # Fallback: scan the tile directly in front of the player.
        target_npc = self.nearby_npc
        if target_npc is None:
            player = self.game_manager.player
            front_x, front_y = player.get_tile_in_front()
            for npc in self.npcs:
                if npc.x // TILE_SIZE == front_x and npc.y // TILE_SIZE == front_y:
                    target_npc = npc
                    break
        if target_npc is None:
            return

        from states.state_npc_menu import StateNpcMenu
        menu = StateNpcMenu(self.game_manager, target_npc)
        self.game_manager.state_manager.push(menu)
    
    # Zones où les entités (joueur + NPC) sont dessinées à échelle réduite
    # pour paraître plus petites sans réduire le zoom de la map.
    _ZONE_ENTITY_SCALE = {"arena": 0.5, "quart": 0.5, "demi": 0.5, "finale": 0.5}

    # Zones où le joueur se déplace en sous-pas (fraction d'un tile par step).
    # La valeur est le nombre de pixels par step.
    _ZONE_SUBSTEP = {"quart": TILE_SIZE // 4, "demi": TILE_SIZE // 4, "finale": TILE_SIZE // 4}

    def render(self, screen):
        self._view_surface.fill((20, 20, 20))
        player = self.game_manager.player
        map_manager = self.game_manager.map_manager
        map_manager.draw(self._view_surface, self.camera)
        entities = self.npcs.copy()
        entities.append(player)
        entities.sort(key=lambda e: e.y)
        entity_scale = self._ZONE_ENTITY_SCALE.get(player.current_zone, 1.0)
        for entity in entities:
            if entity_scale != 1.0:
                self._draw_entity_scaled(entity, entity_scale)
            else:
                entity.draw(self._view_surface, self.camera)
        self.game_manager.day_night_cycle.draw_filter(self._view_surface)
        scaled = pygame.transform.scale(self._view_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(scaled, (0, 0))
        if self.nearby_npc is not None:
            self._draw_npc_bubble(screen, self.nearby_npc)
        elif pygame.time.get_ticks() < self._thought_show_until:
            self._draw_player_thought(screen)
        self.hud.draw(screen)

    def _draw_player_thought(self, screen):
        """Bulle de pensée du joueur — voix off narrative."""
        from data.story import get_story_hint
        from ui.poke_style import wrap

        player = self.game_manager.player
        hint = get_story_hint(player)
        if not hint:
            return

        if self._bubble_font is None:
            font_path = os.path.join("assets", "font", "Pokemon_Solid.ttf")
            self._bubble_font = (pygame.font.Font(font_path, 13)
                                 if os.path.exists(font_path)
                                 else pygame.font.Font(None, 17))

        # Position du joueur sur l'écran
        vx, vy = self.camera.apply(player.x, player.y)
        zoom_x = SCREEN_WIDTH / self._view_surface.get_width()
        zoom_y = SCREEN_HEIGHT / self._view_surface.get_height()
        sx = int(vx * zoom_x)
        sy = int(vy * zoom_y)
        tile_px = int(TILE_SIZE * zoom_x)

        # Wrap du texte
        max_w = 340
        lines = wrap(self._bubble_font, hint, max_w - 20)
        line_h = self._bubble_font.get_height() + 3
        tw = max(self._bubble_font.size(l)[0] for l in lines)
        bw = tw + 20
        bh = len(lines) * line_h + 12

        bx = sx + tile_px // 2 - bw // 2
        by = sy - bh - 10
        bx = max(4, min(bx, SCREEN_WIDTH - bw - 4))
        by = max(4, by)

        # Fond crème + bordure dorée (bulle de pensée)
        surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(surf, (255, 250, 210, 225), (0, 0, bw, bh), border_radius=10)
        pygame.draw.rect(surf, (190, 150, 30, 210), (0, 0, bw, bh), width=2, border_radius=10)
        for i, line in enumerate(lines):
            txt = self._bubble_font.render(line, True, (45, 30, 5))
            surf.blit(txt, (10, 6 + i * line_h))
        screen.blit(surf, (bx, by))

        # Petits cercles pointant vers le joueur (style "pensée")
        cx = bx + bw // 2
        pygame.draw.circle(screen, (190, 150, 30), (cx, by + bh + 3), 3)
        pygame.draw.circle(screen, (190, 150, 30), (cx + 4, by + bh + 8), 2)
        pygame.draw.circle(screen, (190, 150, 30), (cx + 7, by + bh + 13), 1)

    def _draw_entity_scaled(self, entity, scale):
        """Dessine une entité à une échelle réduite dans la view surface."""
        # Player: sprites[direction] est une liste de frames — utilise get_sprite()
        # NPC:    sprites[direction] est une Surface directe
        if hasattr(entity, 'get_sprite'):
            sprite = entity.get_sprite()
        else:
            direction = getattr(entity, 'direction', 'down')
            sprite = entity.sprites.get(direction) or entity.sprites.get('down')
        if sprite is None:
            return
        sx, sy = self.camera.apply(entity.x, entity.y)
        orig_w, orig_h = sprite.get_size()
        new_w = max(1, int(orig_w * scale))
        new_h = max(1, int(orig_h * scale))
        scaled_sprite = pygame.transform.scale(sprite, (new_w, new_h))
        # Centré horizontalement, ancré en bas du tile
        ox = (orig_w - new_w) // 2
        oy = orig_h - new_h
        self._view_surface.blit(scaled_sprite, (sx + ox, sy + oy))