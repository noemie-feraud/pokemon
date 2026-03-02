# =============================================================================
# STATE_NPC_MENU.PY - NPC INTERACTION MENU
# =============================================================================
#
# Transparent overlay that appears when the player presses Space near an NPC.
# Shows the available interactions (talk, battle, etc.).

import pygame
from states.state import State
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT


# =============================================================================
# STATE NPC MENU CLASS
# =============================================================================

class StateNpcMenu(State):
    """
    Small interaction menu that appears over the exploration state.
    Options depend on the NPC type.
    """

    transparent = True

    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------

    def __init__(self, game_manager, npc):
        super().__init__(game_manager)

        self.npc = npc
        self.selection_index = 0

        # Face player
        npc.face_player(game_manager.player.direction)

        # Build options list based on NPC type
        self.options = self._build_options()

        # Fonts
        self.font_name = pygame.font.Font(None, 26)
        self.font_option = pygame.font.Font(None, 28)
        self.font_hint = pygame.font.Font(None, 20)


    # -------------------------------------------------------------------------
    # OPTIONS BUILDER
    # -------------------------------------------------------------------------

    def _build_options(self):
        """
        Build interaction options list.
        Returns list of (label, action_key) tuples.
        """
        player = self.game_manager.player
        npc_type = getattr(self.npc, 'npc_type', 'ambient')

        if npc_type == "shopkeeper":
            return [("Boutique", "boutique"), ("Discuter", "talk")]

        options = [("Discuter", "talk")]
        if player.team.has_valid_pokemon:
            options.append(("Proposer un combat", "challenge"))
        options.append(("Demander un défi", "defi"))
        return options


    # -------------------------------------------------------------------------
    # LIFECYCLE
    # -------------------------------------------------------------------------

    def on_enter(self):
        pass


    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------

    def handle_events(self, events):
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_UP:
                old = self.selection_index
                self.selection_index = max(0, self.selection_index - 1)
                if self.selection_index != old:
                    self.game_manager.audio_manager.play_sfx("menu_select")

            elif event.key == pygame.K_DOWN:
                old = self.selection_index
                self.selection_index = min(len(self.options) - 1, self.selection_index + 1)
                if self.selection_index != old:
                    self.game_manager.audio_manager.play_sfx("menu_select")

            elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                self._execute_selection()

            elif event.key == pygame.K_ESCAPE:
                self.game_manager.state_manager.pop()


    # -------------------------------------------------------------------------
    # ACTION EXECUTION
    # -------------------------------------------------------------------------

    def _execute_selection(self):
        """Execute the selected action."""
        _, action = self.options[self.selection_index]

        # Pop menu first so the new state lands on top of exploration
        self.game_manager.state_manager.pop()

        if action == "boutique":
            self._do_boutique()
        elif action == "talk":
            self._do_talk()
        elif action == "challenge":
            self._do_challenge()
        elif action == "defi":
            self._do_defi()


    def _do_boutique(self):
        """Open the shop directly for shopkeeper NPCs."""
        from states.state_shop import StateShop
        self.game_manager.state_manager.push(StateShop(self.game_manager, self.npc))

    def _do_talk(self):
        """
        Just talk to the NPC — no combat trigger.
        If the NPC has a "talk" dialogue key, show it without triggering
        their function (no healing, no shop). Otherwise fall back to
        the normal full interaction.
        For trainers, show a non-combat dialogue.
        """
        is_trainer = getattr(self.npc, 'is_trainer', False)

        if not is_trainer:
            # Professor who gives starters: if player has no team yet,
            # use on_interact so the "first" dialogue triggers starter selection.
            gives_starter = getattr(self.npc, 'gives_starter', False)
            if gives_starter and self.game_manager.player.team.is_empty:
                self.npc.on_interact(self.game_manager)
                return

            talk_lines = self.npc.dialogues.get("talk")
            if talk_lines:
                from states.state_dialogue import StateDialogue
                dialogue = StateDialogue(
                    self.game_manager,
                    talk_lines,
                    npc=self.npc,
                    callback=None
                )
                self.game_manager.state_manager.push(dialogue)
            else:
                self.npc.on_interact(self.game_manager)
            return

        # Trainer → show challenge or already_beaten dialogue, no combat callback
        player = self.game_manager.player
        if player.is_trainer_defeated(self.npc.id):
            lines = self.npc.dialogues.get("already_beaten",
                                           ["T'as déjà gagné contre moi..."])
        else:
            lines = self.npc.dialogues.get("challenge",
                                           ["Hé ! Prépare-toi à combattre !"])
        from states.state_dialogue import StateDialogue
        dialogue = StateDialogue(
            self.game_manager,
            lines,
            npc=self.npc,
            callback=None   # No combat after a simple chat
        )
        self.game_manager.state_manager.push(dialogue)


    def _do_challenge(self):
        """
        Player proposes a battle to any NPC.
        - No pokemon: message d'erreur
        - Trainer NPCs → combat direct avec leur équipe (même si déjà battu)
        - Other NPCs   → génère un adversaire aléatoire
        """
        player = self.game_manager.player

        if not player.team.has_valid_pokemon:
            from states.state_dialogue import StateDialogue
            dialogue = StateDialogue(
                self.game_manager,
                ["Tu n'as pas de Pokémon pour te battre !"],
                npc=self.npc,
            )
            self.game_manager.state_manager.push(dialogue)
            return

        is_trainer = getattr(self.npc, 'is_trainer', False)
        lines = self.npc.dialogues.get(
            "challenge",
            ["Très bien, si tu veux te battre !"]
        )
        from states.state_dialogue import StateDialogue

        if is_trainer:
            npc = self.npc
            def start_combat(gm):
                npc.team.heal_all()
                from states.state_combat import StateCombat
                combat = StateCombat(
                    gm,
                    opponent_pokemon=npc.team.get_first_valid(),
                    combat_type="trainer",
                    trainer=npc
                )
                gm.state_manager.push(combat)
        else:
            def start_combat(gm):
                self._start_random_combat(gm)

        dialogue = StateDialogue(
            self.game_manager,
            lines,
            npc=self.npc,
            callback=start_combat
        )
        self.game_manager.state_manager.push(dialogue)

    def _start_random_combat(self, game_manager):
        """Start a trainer-style combat with a random Pokémon for non-trainer NPCs."""
        import random
        from entities.pokemon import Pokemon
        from entities.team import Team
        from states.state_combat import StateCombat
        from config.settings import WILD_POKEMON_LEVELS

        zone = game_manager.player.current_zone
        min_lvl, max_lvl = WILD_POKEMON_LEVELS.get(zone, (5, 10))
        level = random.randint(min_lvl, max_lvl)
        pokemon_id = random.randint(1, 9)
        pokemon = Pokemon.from_data(pokemon_id, level)

        npc = self.npc

        class _TempTrainer:
            id = npc.id
            name = npc.name
            reward_credits = 10
            team = Team([pokemon])

        combat = StateCombat(
            game_manager,
            opponent_pokemon=pokemon,
            combat_type="trainer",
            trainer=_TempTrainer()
        )
        game_manager.state_manager.push(combat)


    def _do_defi(self):
        """
        Système de défi : capture X Pokémon, reviens pour une récompense.
        Chaque NPC donne un défi unique, persisté dans player.challenges.
        """
        import random
        from states.state_dialogue import StateDialogue

        player = self.game_manager.player
        npc_id = str(self.npc.id)
        total_owned = len(player.team) + len(player.storage)

        # Défi déjà complété
        if npc_id in player.challenges_completed:
            dialogue = StateDialogue(
                self.game_manager,
                ["Tu as déjà relevé mon défi !", "Continue comme ça."],
                npc=self.npc,
            )
            self.game_manager.state_manager.push(dialogue)
            return

        # Défi en cours — vérifier progression
        if npc_id in player.challenges:
            challenge = player.challenges[npc_id]
            target = challenge["target"]
            reward = challenge["reward"]

            if total_owned >= target:
                # Réussi !
                player.credits += reward
                player.challenges_completed.append(npc_id)
                del player.challenges[npc_id]
                self.game_manager.audio_manager.play_sfx("levelup")
                dialogue = StateDialogue(
                    self.game_manager,
                    [
                        "Bien joué !",
                        f"Tu as capturé {target} Pokémon.",
                        f"Tiens, {reward} crédits !"
                    ],
                    npc=self.npc,
                )
            else:
                dialogue = StateDialogue(
                    self.game_manager,
                    [
                        "Pas encore...",
                        f"Tu en es à {total_owned}/{target} Pokémon."
                    ],
                    npc=self.npc,
                )
            self.game_manager.state_manager.push(dialogue)
            return

        # Nouveau défi
        target = random.randint(5, 20)
        reward = target * 5
        player.challenges[npc_id] = {"target": target, "reward": reward}

        dialogue = StateDialogue(
            self.game_manager,
            [
                f"Défi : capture {target} Pokémon.",
                "Reviens me voir quand c'est fait.",
                f"Récompense : {reward} crédits."
            ],
            npc=self.npc,
        )
        self.game_manager.state_manager.push(dialogue)


    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------

    def update(self, dt):
        pass


    # -------------------------------------------------------------------------
    # RENDERING
    # -------------------------------------------------------------------------

    def render(self, screen):
        """Draw small interaction menu in bottom-right corner."""
        padding = 14
        option_h = 30
        name_h = 28

        menu_w = 280
        menu_h = padding * 2 + name_h + 4 + len(self.options) * option_h

        menu_x = SCREEN_WIDTH - menu_w - 20
        menu_y = SCREEN_HEIGHT - menu_h - 60

        # Background
        bg = pygame.Surface((menu_w, menu_h))
        bg.fill((20, 25, 45))
        bg.set_alpha(230)
        screen.blit(bg, (menu_x, menu_y))

        # Border
        pygame.draw.rect(screen, (255, 200, 50),
                         (menu_x, menu_y, menu_w, menu_h), 2)

        # NPC name header
        name_surf = self.font_name.render(self.npc.name, True, (255, 200, 50))
        screen.blit(name_surf, (menu_x + padding, menu_y + padding - 2))

        # Separator
        sep_y = menu_y + padding + name_h
        pygame.draw.line(screen, (80, 80, 120),
                         (menu_x + padding, sep_y),
                         (menu_x + menu_w - padding, sep_y), 1)

        # Options
        for i, (label, _) in enumerate(self.options):
            opt_y = sep_y + 6 + i * option_h
            if i == self.selection_index:
                color = (255, 220, 50)
                prefix = "> "
            else:
                color = (200, 200, 200)
                prefix = "  "
            text_surf = self.font_option.render(prefix + label, True, color)
            screen.blit(text_surf, (menu_x + padding, opt_y))

        # Controls hint
        hint = "[↑↓] Choisir  [Entrée] OK  [Échap] Annuler"
        hint_surf = self.font_hint.render(hint, True, (100, 100, 120))
        screen.blit(hint_surf, (menu_x + padding,
                                menu_y + menu_h - 18))
