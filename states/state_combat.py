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
        
        # --- GET PLAYER'S FIRST POKEMON ---
        player = game_manager.player
        self.player_pokemon = player.team.get_first_valid()
        
        # --- CREATE MODEL ---
        self.combat = Combat(
            player_pokemon=self.player_pokemon,
            opponent_pokemon=self.opponent_pokemon,
            combat_type=combat_type,
            trainer=trainer,
            day_night_cycle=game_manager.day_night_cycle
        )
        
        # --- CREATE VIEW ---
        self.combat_ui = CombatUI(game_manager)
        self.combat_ui.set_state(
            player_pokemon=self.player_pokemon,
            opponent_pokemon=self.opponent_pokemon,
            combat_type=combat_type
        )
        
        # --- CURRENT PHASE ---
        self.phase = PHASE_INTRO
        
        # --- EVENTS ---
        self.events = []
        self.event_index = 0
        
        # --- PENDING EVOLUTIONS ---
        self.pending_evolutions = []
        self.evolution_index = 0
        
        # --- INTRO MESSAGE (IN FRENCH) ---
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
            
            elif self.phase == PHASE_END:
                self._handle_end(event)
    
    
    # -------------------------------------------------------------------------
    # INTRO PHASE
    # -------------------------------------------------------------------------
    
    def _handle_intro(self, event):
        """Handle intro phase (appearance message)."""
        if event.key == pygame.K_SPACE:
            if self.combat_ui.next_event():
                # Still have intro events
                pass
            else:
                # Intro finished → player choice
                self.phase = PHASE_PLAYER_CHOICE
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
            return  # Player is still navigating
        
        # Player has chosen an action
        # action = {"type": "attack", "attack": attack}
        #        or {"type": "item", "item": item}
        #        or {"type": "switch", "index": 2}
        #        or {"type": "flee"}
        
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
            self.combat.switch_player_pokemon(chosen_pokemon)
            self.player_pokemon = chosen_pokemon
            
            # Switch consumes turn → opponent attacks
            events = self.combat.execute_turn_after_switch()
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
                
                events = self._create_capture_events(result)
                self._process_events(events)
                return
            else:
                # Healing/boost item
                events = self.combat.execute_turn(
                    {"type": "item", "item": item, "target": self.player_pokemon}
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
        self.combat_ui.set_events(events)
        self.phase = PHASE_EXECUTION
        
        # Update visual state
        self.combat_ui.set_state(
            player_pokemon=self.combat.player_pokemon,
            opponent_pokemon=self.combat.opponent_pokemon,
            combat_type=self.combat_type
        )
    
    
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
            
            # Opponent attacks after failed capture
            opponent_events = self.combat.execute_opponent_turn_only()
            events.extend(opponent_events)
        
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
                # Still have events
                pass
            else:
                # All events displayed → determine next step
                self._after_events()
    
    
    def _after_events(self):
        """
        Called when all events of a turn have been displayed.
        Determine what to do next.
        """
        # Look for end event in the list
        for evt in self.events:
            if evt["type"] == "combat_end":
                self._begin_combat_end(evt["result"])
                return
            
            if evt["type"] == "replacement_choice":
                # Player's Pokemon is KO → force replacement
                if self.game_manager.player.team.has_valid_pokemon():
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
        
        if action["type"] != "switch":
            return  # Only accept switch
        
        # Perform switch
        chosen_pokemon = self.game_manager.player.team.get_pokemon(action["index"])
        self.combat.switch_player_pokemon(chosen_pokemon)
        self.player_pokemon = chosen_pokemon
        
        # Update view
        self.combat_ui.set_state(
            player_pokemon=self.player_pokemon,
            opponent_pokemon=self.combat.opponent_pokemon,
            combat_type=self.combat_type
        )
        
        # Switch message
        self.combat_ui.set_events([
            {"type": "message", "text": f"Go {chosen_pokemon.name} !"}
        ])
        self.phase = PHASE_EXECUTION
    
    
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
        end_events = []
        
        if result == "victory":
            end_events = self._prepare_victory()
        
        elif result == "defeat":
            end_events = self._prepare_defeat()
        
        # Flee and capture have no additional events
        
        if len(end_events) > 0:
            self.combat_ui.set_events(end_events)
            self.phase = PHASE_EXECUTION
            self.waiting_for_end = True
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
            credits = self.trainer.get_reward()
            player.credits += credits
            events.append({
                "type": "message",
                "text": f"Vous avez gagné {credits} crédits !"
            })
            
            # Mark trainer as defeated
            player.add_defeated_trainer(self.trainer.id)
        
        # --- EVOLUTIONS ---
        for pokemon in player.team.get_all():
            if pokemon.can_evolve():
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
    # END PHASE
    # -------------------------------------------------------------------------
    
    def _handle_end(self, event):
        """Handle end phase (Space to quit)."""
        if event.key == pygame.K_SPACE:
            self._quit_combat()
    
    
    def _quit_combat(self):
        """Pop StateCombat to return to exploration."""
        # Trainer callback if victory
        if self.final_result == "victory" and self.trainer is not None:
            self.trainer.on_defeat()
        
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