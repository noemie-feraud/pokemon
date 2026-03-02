# =============================================================================
# STATE_COMBAT.PY - COMBAT STATE
# =============================================================================
#
# This is the combat controller.
# It connects the model (combat.py) and the view (combat_ui.py).

import pygame
from states.state import State
from combat.combat import Combat
from ui.combat_ui import CombatUI
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT


# =============================================================================
# LOCAL CONSTANTS
# =============================================================================

PHASE_INTRO = "intro"
PHASE_PLAYER_CHOICE = "player_choice"
PHASE_EXECUTION = "execution"
PHASE_REPLACEMENT = "replacement"
PHASE_EVOLUTION = "evolution"
PHASE_CAPTURE = "capture"
PHASE_END = "end"


# =============================================================================
# STATE COMBAT CLASS
# =============================================================================

class StateCombat(State):
    """
    Combat controller. Connects the model (Combat) and the view (CombatUI).
    Pushed by state_exploration.py, pops when combat ends.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager, opponent_pokemon, combat_type, trainer=None):
        """
        Initialize combat state.
        
        Args:
            game_manager: reference to Game
            opponent_pokemon: opponent Pokemon (wild or trainer's first)
            combat_type: "wild" or "trainer"
            trainer: Trainer instance (None if wild)
        """
        super().__init__(game_manager)
        
        self.combat_type = combat_type
        self.trainer = trainer
        self.opponent_pokemon = opponent_pokemon
        
        # Combat takes full screen (not transparent)
        self.transparent = False
        
        # --- GET PLAYER'S TEAM ---
        player = game_manager.player
        self.player_team = player.team
        
        # --- CREATE OPPONENT TEAM ---
        # For wild combat, opponent_team is just the single Pokemon
        # For trainer combat, opponent_team is the trainer's full team
        if combat_type == "wild":
            from entities.team import Team
            self.opponent_team = Team([opponent_pokemon])
        else:
            self.opponent_team = trainer.team
        
        # --- CREATE MODEL ---
        self.combat = Combat(
            game_manager=game_manager,
            player_team=self.player_team,
            opponent_team=self.opponent_team,
            combat_type=combat_type,
            trainer=trainer
        )
        
        # --- CREATE VIEW ---
        self.combat_ui = CombatUI(game_manager)
        self.combat_ui.set_state(
            player_pokemon=self.combat.player_pokemon,
            opponent_pokemon=self.combat.opponent_pokemon,
            combat_type=combat_type,
            player_team=self.player_team
        )
        self.combat_ui.load_sprites(
            self.combat.player_pokemon,
            self.combat.opponent_pokemon
        )
        
        # --- CURRENT PHASE ---
        self.phase = PHASE_INTRO

        # --- EVENTS ---
        self.events = []
        self.event_index = 0

        # --- PENDING EVOLUTIONS ---
        self.pending_evolutions = []
        self.evolution_index = 0

        # --- PRE-COMBAT SELECTION ---
        # True when player is choosing their starting Pokémon (no opponent attack)
        self.pre_combat_switch = False
        
        # --- INTRO MESSAGE ---
        if combat_type == "wild":
            intro_message = f"Un {opponent_pokemon.name} sauvage apparaît !"
        else:
            intro_message = f"{trainer.name} veut combattre !"
        
        self.combat_ui.set_events([
            {"type": "message", "text": intro_message}
        ])
        
        # Register opponent Pokemon in Pokedex
        game_manager.player.pokedex.register_seen(opponent_pokemon.id)
    
    
    # -------------------------------------------------------------------------
    # LIFECYCLE METHODS
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """Called when combat state becomes active."""
        self.game_manager.audio_manager.play_music("combat")
    
    
    # -------------------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """
        Handle inputs based on current phase.
        
        Args:
            events: list of Pygame events
        """
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            if self.phase == PHASE_INTRO:
                self._handle_intro(event)
            
            elif self.phase == PHASE_PLAYER_CHOICE:
                self._handle_player_choice(event)
            
            elif self.phase == PHASE_EXECUTION:
                self._handle_execution(event)
            
            elif self.phase == PHASE_REPLACEMENT:
                self._handle_replacement(event)
            
            elif self.phase == PHASE_EVOLUTION:
                self._handle_evolution(event)

            elif self.phase == PHASE_CAPTURE:
                self._handle_capture_choice(event)

            elif self.phase == PHASE_END:
                self._handle_end(event)
    
    
    # -------------------------------------------------------------------------
    # INTRO PHASE
    # -------------------------------------------------------------------------
    
    def _handle_intro(self, event):
        """Handle intro phase (appearance message)."""
        if event.key == pygame.K_SPACE:
            if self.combat_ui.next_event():
                pass
            else:
                self.phase = PHASE_PLAYER_CHOICE
                # If player has multiple valid Pokémon, let them choose the starting one
                if self.player_team.count_valid() > 1:
                    self.pre_combat_switch = True
                    self.combat_ui.set_mode("pokemon")
                else:
                    self.combat_ui.set_mode("menu")
    
    
    # -------------------------------------------------------------------------
    # PLAYER CHOICE PHASE
    # -------------------------------------------------------------------------
    
    def _handle_player_choice(self, event):
        """
        Handle phase where player chooses their action.
        """
        action = self.combat_ui.handle_input(event)

        if action is None:
            return

        # Pre-combat Pokémon selection: switch without opponent attacking
        if self.pre_combat_switch:
            if action["type"] == "switch":
                new_pokemon = self.player_team.get_pokemon(action["index"])
                if new_pokemon and not new_pokemon.is_ko:
                    self.combat.player_pokemon = new_pokemon
                    self.combat_ui.set_state(
                        player_pokemon=new_pokemon,
                        opponent_pokemon=self.combat.opponent_pokemon,
                        combat_type=self.combat_type,
                        player_team=self.player_team
                    )
                    self.combat_ui.load_sprites(new_pokemon, self.combat.opponent_pokemon)
            # In all cases (switch or flee/escape), end pre-combat selection
            self.pre_combat_switch = False
            self.combat_ui.set_mode("menu")
            return

        self._execute_action(action)
    
    
    def _execute_action(self, action):
        """
        Send player action to model and get events.
        
        Args:
            action: dict with type and parameters
        """
        player = self.game_manager.player
        
        # --- FLEE ---
        if action["type"] == "flee":
            if self.combat_type == "trainer":
                # Can't flee from trainer
                self.combat_ui.set_events([
                    {"type": "message", "text": "Impossible de fuir un combat de dresseur !"}
                ])
                self.phase = PHASE_EXECUTION
                return
            else:
                # Flee always succeeds (wild)
                self.combat_ui.set_events([
                    {"type": "message", "text": "Vous prenez la fuite !"},
                    {"type": "combat_end", "result": "flee"}
                ])
                self.phase = PHASE_EXECUTION
                return
        
        # --- SWITCH POKEMON ---
        if action["type"] == "switch":
            chosen_pokemon = player.team.get_pokemon(action["index"])
            
            # Execute turn with switch action
            events = self.combat.execute_turn(
                {"type": "switch", "index": action["index"]}
            )
            self._process_events(events)
            return
        
        # --- USE ITEM ---
        if action["type"] == "item":
            item = self.game_manager.item_catalog.get_item(action["item_id"])
            
            if item.is_pokeball:
                # Capture attempt
                from combat.capture_system import attempt_capture
                result = attempt_capture(
                    self.opponent_pokemon, item,
                    player.team, player.storage,
                    self.combat_type
                )
                player.inventory.remove(item.id, 1)

                if result["capture_success"]:
                    player.pokedex.register_captured(self.opponent_pokemon.id)

                events = self._create_capture_events(result)
                self._process_events(events)
                return
            else:
                # Healing/boost item
                events = self.combat.execute_turn(
                    {"type": "item", "item": item, "target": self.combat.player_pokemon}
                )
                player.inventory.remove(item.id, 1)
                self._process_events(events)
                return
        
        # --- ATTACK ---
        if action["type"] == "attack":
            attack = action["attack"]
            events = self.combat.execute_turn(
                {"type": "attack", "attack": attack}
            )
            self._process_events(events)
    
    
    def _process_events(self, events):
        """
        Receive events from model and pass them to view.

        Args:
            events: list of combat events
        """
        self.events = events
        self.event_index = 0
        self.phase = PHASE_EXECUTION

        # Update visual state FIRST so events see current Pokemon
        self.combat_ui.set_state(
            player_pokemon=self.combat.player_pokemon,
            opponent_pokemon=self.combat.opponent_pokemon,
            combat_type=self.combat_type,
            player_team=self.player_team
        )
        self.combat_ui.set_events(events)
    
    
    def _create_capture_events(self, result):
        """
        Transform capture_system result into events.
        
        Args:
            result: dict from attempt_capture()
            
        Returns:
            list of events
        """
        events = []
        
        # Ball throw animation
        events.append({
            "type": "capture_throw",
            "shake_count": result.get("shake_count", 0)
        })
        
        if result["capture_success"]:
            events.append({
                "type": "message",
                "text": f"{result['captured_pokemon'].name} a été capturé !"
            })
            
            if result["destination"] == "storage":
                events.append({
                    "type": "message",
                    "text": f"L'équipe est pleine. {result['captured_pokemon'].name} a été envoyé au stockage."
                })
            
            events.append({
                "type": "combat_end", "result": "capture"
            })
        else:
            events.append({
                "type": "message",
                "text": f"Raté ! {self.opponent_pokemon.name} s'est libéré !"
            })
            
            # Execute opponent's turn after failed capture
            # The turn is already processed in combat.execute_turn()
            # So we just need to get the opponent's action events
            # For simplicity, we'll let the next turn handle it
            pass
        
        return events
    
    
    # -------------------------------------------------------------------------
    # EXECUTION PHASE
    # -------------------------------------------------------------------------
    
    def _handle_execution(self, event):
        """
        Handle phase where events are displayed one by one.
        Space to advance.
        """
        if event.key == pygame.K_SPACE:
            # Check if current animation is finished
            if not self.combat_ui.is_animation_finished():
                # Animation in progress → skip it
                self.combat_ui.skip_animation()
                return
            
            if self.combat_ui.next_event():
                # If replacement screen just appeared and queue is now empty,
                # transition to PHASE_REPLACEMENT immediately (no extra SPACE needed)
                if not self.combat_ui.pending_events and self.combat_ui.mode == "replacement":
                    self._after_events()
            else:
                # All events displayed → determine next step
                self._after_events()
    
    
    def _after_events(self):
        """
        Called when all events of a turn have been displayed.
        Determine what to do next.
        """
        # If we're in the end sequence (victory/defeat messages just shown)
        if getattr(self, 'waiting_for_end', False):
            self.waiting_for_end = False
            # Offer capture before evolutions
            if getattr(self, 'pending_capture', False):
                self.pending_capture = False
                self._start_capture_prompt()
                return
            if self.pending_evolutions:
                pokemon = self.pending_evolutions[self.evolution_index]
                evolution_name = pokemon.get_evolution_name()
                self.combat_ui.set_events([{
                    "type": "message",
                    "text": f"{pokemon.name} veut évoluer en {evolution_name} ! [Entrée] Oui  [Échap] Non"
                }])
                self.phase = PHASE_EVOLUTION
            else:
                self.phase = PHASE_END
            return

        # Look for end event in the list
        for evt in self.events:
            if evt["type"] == "combat_end":
                self._begin_combat_end(evt["result"])
                return

            if evt["type"] == "replacement_choice":
                # Player's Pokemon is KO → force replacement
                if self.game_manager.player.team.has_valid_pokemon:
                    self.phase = PHASE_REPLACEMENT
                    self.combat_ui.set_mode("replacement")
                else:
                    # No Pokemon left → defeat
                    self._begin_combat_end("defeat")
                return

        # Nothing special → back to player choice
        self.phase = PHASE_PLAYER_CHOICE
        self.combat_ui.set_mode("menu")
    
    
    # -------------------------------------------------------------------------
    # REPLACEMENT PHASE
    # -------------------------------------------------------------------------
    
    def _handle_replacement(self, event):
        """
        Handle phase where player must choose a replacement.
        """
        action = self.combat_ui.handle_input(event)
        
        if action is None:
            return
        
        if action["type"] not in ("switch", "replacement"):
            return  # Only accept switch or replacement
        
        # Execute switch (will also process opponent's turn)
        events = self.combat.execute_turn(
            {"type": "switch", "index": action["index"]}
        )
        self._process_events(events)
    
    
    # -------------------------------------------------------------------------
    # COMBAT END PHASE
    # -------------------------------------------------------------------------
    
    def _begin_combat_end(self, result):
        """
        Prepare combat end phase.

        Args:
            result: "victory", "defeat", "flee", "capture"
        """
        self.final_result = result
        self.pending_capture = False
        end_events = []

        if result == "victory":
            end_events = self._prepare_victory()
            # Offer capture after victory if player has pokeballs
            self.pending_capture = (
                self.game_manager.player.inventory.has_pokeballs()
                and self.opponent_pokemon is not None
            )

        elif result == "defeat":
            end_events = self._prepare_defeat()

        # Flee and capture have no additional events

        if len(end_events) > 0:
            self.combat_ui.set_events(end_events)
            self.phase = PHASE_EXECUTION
            self.waiting_for_end = True
        elif self.pending_capture:
            self.pending_capture = False
            self._start_capture_prompt()
        else:
            self.phase = PHASE_END
    
    
    def _prepare_victory(self):
        """
        Calculate and display victory rewards.
        
        Returns:
            list of events to display
        """
        player = self.game_manager.player
        events = []
        
        # --- CREDITS (trainer only) ---
        if self.combat_type == "trainer" and self.trainer is not None:
            credits = self.trainer.reward_credits
            player.credits += credits
            events.append({
                "type": "message",
                "text": f"Vous avez gagné {credits} crédits !"
            })
        
        # --- EVOLUTIONS ---
        for pokemon in player.team.get_all():
            if pokemon.can_evolve:
                self.pending_evolutions.append(pokemon)
        
        return events
    
    
    def _prepare_defeat(self):
        """
        Handle defeat: heal team, prepare teleport.
        
        Returns:
            list of events to display
        """
        player = self.game_manager.player
        
        # Heal entire team
        player.team.heal_all()
        
        # Teleport to Pokemon Center will be handled by
        # state_exploration via a flag
        player.must_teleport_to_center = True
        
        return [
            {"type": "message", "text": "Vous n'avez plus de Pokémon..."},
            {"type": "message", "text": "Vous êtes ramené au Centre Pokémon."}
        ]
    
    
    # -------------------------------------------------------------------------
    # EVOLUTION PHASE
    # -------------------------------------------------------------------------
    
    def _handle_evolution(self, event):
        """
        Handle evolution phase (Yes/No choice).
        """
        if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            # Accept evolution
            pokemon = self.pending_evolutions[self.evolution_index]
            evolution_name = pokemon.evolve()
            
            self.combat_ui.set_events([{
                "type": "message",
                "text": f"{pokemon.name} a évolué en {evolution_name} !"
            }])
            
            self.evolution_index += 1
            self._check_remaining_evolutions()
        
        elif event.key == pygame.K_ESCAPE:
            # Refuse evolution
            self.evolution_index += 1
            self._check_remaining_evolutions()
    
    
    def _check_remaining_evolutions(self):
        """Check if there are more evolutions to propose."""
        if self.evolution_index < len(self.pending_evolutions):
            # More evolutions
            pokemon = self.pending_evolutions[self.evolution_index]
            evolution_name = pokemon.get_evolution_name()
            self.combat_ui.set_events([{
                "type": "message",
                "text": f"{pokemon.name} veut évoluer en {evolution_name} ! [Entrée] Oui  [Échap] Non"
            }])
            self.phase = PHASE_EXECUTION
        else:
            # All evolutions processed
            self.phase = PHASE_END
    
    
    # -------------------------------------------------------------------------
    # CAPTURE PHASE (post-victory)
    # -------------------------------------------------------------------------

    def _start_capture_prompt(self):
        """Show the post-victory capture prompt."""
        self.combat_ui.set_events([{
            "type": "message",
            "text": f"Capturer {self.opponent_pokemon.name} ? [Espace] Oui  [Échap] Non"
        }])
        self.phase = PHASE_CAPTURE

    def _handle_capture_choice(self, event):
        """Handle the capture Yes/No prompt."""
        if event.key == pygame.K_SPACE:
            self._do_post_victory_capture()
        elif event.key == pygame.K_ESCAPE:
            self._finish_capture_phase()

    def _do_post_victory_capture(self):
        """Capture the defeated opponent (guaranteed, consumes one pokeball)."""
        player = self.game_manager.player
        balls = player.inventory.get_by_category("pokeball")
        ball = balls[0][0]
        player.inventory.remove(ball.id, 1)

        if not player.team.is_full:
            player.team.add(self.opponent_pokemon)
            destination = "team"
        else:
            player.storage.add(self.opponent_pokemon)
            destination = "storage"

        player.pokedex.register_captured(self.opponent_pokemon.id)

        capture_events = [{
            "type": "message",
            "text": f"{self.opponent_pokemon.name} a été capturé !"
        }]
        if destination == "storage":
            capture_events.append({
                "type": "message",
                "text": f"L'équipe est pleine. {self.opponent_pokemon.name} a été envoyé au stockage."
            })
        self.combat_ui.set_events(capture_events)
        self.phase = PHASE_EXECUTION
        self.waiting_for_end = True

    def _finish_capture_phase(self):
        """Skip capture and proceed to evolutions or end."""
        if self.pending_evolutions:
            pokemon = self.pending_evolutions[self.evolution_index]
            evolution_name = pokemon.get_evolution_name()
            self.combat_ui.set_events([{
                "type": "message",
                "text": f"{pokemon.name} veut évoluer en {evolution_name} ! [Entrée] Oui  [Échap] Non"
            }])
            self.phase = PHASE_EVOLUTION
        else:
            self.phase = PHASE_END


    # -------------------------------------------------------------------------
    # END PHASE
    # -------------------------------------------------------------------------

    def _handle_end(self, event):
        """Handle end phase (Space to quit)."""
        if event.key == pygame.K_SPACE:
            self._quit_combat()
    
    
    def _quit_combat(self):
        """Pop StateCombat to return to exploration."""
        # Trainer callback if victory
        if hasattr(self, 'final_result') and self.final_result == "victory" and self.trainer is not None:
            # Trainer's on_defeat will be called by the combat system
            pass
        
        # Return to exploration
        self.game_manager.state_manager.pop()
    
    
    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    
    def update(self, dt):
        """
        Update combat_ui animations.
        
        Args:
            dt: delta time in seconds
        """
        self.combat_ui.update(dt)
        
        # Check if waiting for end events
        if hasattr(self, "waiting_for_end") and self.waiting_for_end:
            if self.phase == PHASE_PLAYER_CHOICE:
                # End events are finished
                self.waiting_for_end = False
                
                if len(self.pending_evolutions) > 0:
                    self.evolution_index = 0
                    pokemon = self.pending_evolutions[0]
                    evolution_name = pokemon.get_evolution_name()
                    self.combat_ui.set_events([{
                        "type": "message",
                        "text": f"{pokemon.name} veut évoluer en {evolution_name} ! [Entrée] Oui  [Échap] Non"
                    }])
                    self.phase = PHASE_EVOLUTION
                else:
                    self.phase = PHASE_END
    
    
    # -------------------------------------------------------------------------
    # RENDERING
    # -------------------------------------------------------------------------
    
    def render(self, screen):
        """
        Delegate all rendering to combat_ui.
        
        Args:
            screen: Pygame surface
        """
        self.combat_ui.draw(screen)