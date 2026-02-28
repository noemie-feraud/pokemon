# =============================================================================
# STATE_EXPLORATION.PY - ÉTAT D'EXPLORATION
# =============================================================================
#
# C'est le cœur du jeu. Le joueur explore la map, parle aux PNJ,
# entre dans les herbes, déclenche des combats, change de zone.

import pygame
import random
from states.state import State
from ui.hud import HUD
from core.camera import Camera
from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    ENCOUNTER_RATE, WILD_POKEMON_LEVELS
)


# =============================================================================
# CLASSE STATE EXPLORATION
# =============================================================================

class StateExploration(State):
    """
    État d'exploration principale.
    Le joueur se déplace sur la map et interagit avec le monde.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTEUR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager):
        """Initialise l'état d'exploration."""
        super().__init__(game_manager)
        
        # La transparence est désactivée (c'est l'état de base)
        self.transparent = False
        
        # --- COMPOSANTS ---
        self.camera = Camera()
        self.hud = HUD(game_manager)
        
        # --- LISTE DES PNJ DE LA ZONE ACTUELLE ---
        self.pnj = []
        
        # --- ÉTAT DU JEU ---
        self.combat_en_attente = False
        self.transition_en_attente = False
        
        # --- CHARGEMENT INITIAL ---
        self._charger_zone_actuelle()
    
    
    # -------------------------------------------------------------------------
    # MÉTHODES PRIVÉES - CHARGEMENT
    # -------------------------------------------------------------------------
    
    def _charger_zone_actuelle(self):
        """Charge la map et les PNJ de la zone actuelle du joueur."""
        joueur = self.game_manager.player
        gestionnaire_map = self.game_manager.map_manager
        
        # Charger la map
        gestionnaire_map.load_map(joueur.zone_actuelle)
        
        # Charger les PNJ de cette zone
        self.pnj = self._creer_pnj_zone(joueur.zone_actuelle)
        
        # Mettre à jour les limites de la caméra
        self.camera.set_bounds(
            gestionnaire_map.get_map_width(),
            gestionnaire_map.get_map_height()
        )
    
    
    def _creer_pnj_zone(self, zone):
        """
        Crée les instances de PNJ pour la zone donnée.
        
        Args:
            zone: le nom de la zone ("campus", "alentours", "arena")
            
        Returns:
            liste d'instances NPC
        """
        from entities.npc_nurse import NPCNurse
        from entities.npc_shopkeeper import NPCShopkeeper
        from entities.npc_professor import NPCProfessor
        from entities.npc_quest import NPCQuest
        from entities.npc_trainer import NPCTrainer
        from entities.npc_ambient import NPCAmbient
        
        gestionnaire_map = self.game_manager.map_manager
        donnees_pnj = gestionnaire_map.get_npcs_data()
        pnj = []
        
        for donnee in donnees_pnj:
            type_pnj = donnee["type"]
            
            if type_pnj == "nurse":
                pnj.append(NPCNurse(donnee))
            elif type_pnj == "shopkeeper":
                pnj.append(NPCShopkeeper(donnee))
            elif type_pnj == "professor":
                pnj.append(NPCProfessor(donnee))
            elif type_pnj == "quest":
                pnj.append(NPCQuest(donnee))
            elif type_pnj == "trainer":
                pnj.append(NPCTrainer(donnee))
            else:  # ambient par défaut
                pnj.append(NPCAmbient(donnee))
        
        return pnj
    
    
    # -------------------------------------------------------------------------
    # MÉTHODES DE CYCLE DE VIE
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """
        Appelée quand l'exploration redevient l'état actif.
        Soit au premier lancement, soit quand un état pushé se termine.
        """
        # Relancer la musique de la zone
        zone = self.game_manager.player.zone_actuelle
        self.game_manager.audio_manager.play_music(zone)
        
        # Réinitialiser les flags
        self.combat_en_attente = False
        self.transition_en_attente = False
    
    
    # -------------------------------------------------------------------------
    # GESTION DES ÉVÉNEMENTS
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """
        Gère les événements ponctuels (appui de touche).
        Les touches maintenues sont gérées dans update().
        """
        joueur = self.game_manager.player
        
        # Ne pas traiter les inputs si le joueur est en mouvement
        if joueur.en_mouvement:
            return
        
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            # --- INTERACTION (Espace) ---
            if event.key == pygame.K_SPACE:
                self._tenter_interaction()
            
            # --- MENU PAUSE (Échap) ---
            elif event.key == pygame.K_ESCAPE:
                from states.state_menu_pause import StateMenuPause
                pause = StateMenuPause(self.game_manager)
                self.game_manager.state_manager.push(pause)
            
            # --- INVENTAIRE (I) ---
            elif event.key == pygame.K_i:
                from states.state_inventory import StateInventory
                inventaire = StateInventory(self.game_manager)
                self.game_manager.state_manager.push(inventaire)
            
            # --- ÉQUIPE (P) ---
            elif event.key == pygame.K_p:
                from states.state_team_screen import StateTeamScreen
                equipe = StateTeamScreen(self.game_manager)
                self.game_manager.state_manager.push(equipe)
    
    
    # -------------------------------------------------------------------------
    # MISE À JOUR
    # -------------------------------------------------------------------------
    
    def update(self, dt):
        """
        Met à jour la logique à chaque frame.
        
        Args:
            dt: delta time en secondes
        """
        joueur = self.game_manager.player
        
        # --- MOUVEMENT CONTINU ---
        if joueur.en_mouvement:
            # Le joueur est en train de glisser vers la tuile cible
            joueur.update_mouvement(dt)
            
            # Vérifier si le mouvement vient de se terminer
            if not joueur.en_mouvement:
                self._on_arrive_sur_tuile()
        
        else:
            # Le joueur est immobile → vérifier si une touche est maintenue
            self._verifier_input_direction()
        
        # --- MISE À JOUR DES SYSTÈMES ---
        self.game_manager.day_night_cycle.update(dt)
        self.hud.update(dt)
        self.camera.update(joueur.get_position_pixels())
        
        # --- MISE À JOUR DES PNJ (animation) ---
        for pnj in self.pnj:
            pnj.update(dt)
    
    
    def _verifier_input_direction(self):
        """
        Vérifie si le joueur maintient une touche directionnelle.
        Si oui, tente de le déplacer dans cette direction.
        """
        touches = pygame.key.get_pressed()
        joueur = self.game_manager.player
        gestionnaire_map = self.game_manager.map_manager
        
        direction = None
        delta_x = 0
        delta_y = 0
        
        if touches[pygame.K_UP] or touches[pygame.K_z]:
            direction = "haut"
            delta_y = -TILE_SIZE
        elif touches[pygame.K_DOWN] or touches[pygame.K_s]:
            direction = "bas"
            delta_y = TILE_SIZE
        elif touches[pygame.K_LEFT] or touches[pygame.K_q]:
            direction = "gauche"
            delta_x = -TILE_SIZE
        elif touches[pygame.K_RIGHT] or touches[pygame.K_d]:
            direction = "droite"
            delta_x = TILE_SIZE
        
        if direction is None:
            return
        
        # Mettre à jour la direction du sprite
        joueur.set_direction(direction)
        
        # Calculer la tuile de destination
        tuile_dest_x = joueur.tuile_x + (delta_x // TILE_SIZE)
        tuile_dest_y = joueur.tuile_y + (delta_y // TILE_SIZE)
        
        # Vérifier la collision
        if not gestionnaire_map.is_collision(tuile_dest_x, tuile_dest_y):
            # Vérifier qu'aucun PNJ n'est sur cette tuile
            if not self._pnj_sur_tuile(tuile_dest_x, tuile_dest_y):
                joueur.start_mouvement(direction)
    
    
    def _pnj_sur_tuile(self, tuile_x, tuile_y):
        """
        Vérifie si un PNJ occupe la tuile donnée.
        
        Args:
            tuile_x, tuile_y: coordonnées de la tuile
            
        Returns:
            True si un PNJ est présent, False sinon
        """
        for pnj in self.pnj:
            if pnj.tuile_x == tuile_x and pnj.tuile_y == tuile_y:
                return True
        return False
    
    
    def _on_arrive_sur_tuile(self):
        """
        Appelée quand le joueur vient d'arriver sur une nouvelle tuile.
        Vérifie les événements liés à la tuile :
        transition, dresseur, rencontre sauvage.
        """
        joueur = self.game_manager.player
        gestionnaire_map = self.game_manager.map_manager
        
        # 1. TRANSITION DE ZONE (prioritaire)
        transition = gestionnaire_map.get_transition(joueur.tuile_x, joueur.tuile_y)
        if transition is not None:
            self._executer_transition(transition)
            return
        
        # 2. DRESSEUR
        if self._verifier_dresseurs():
            return
        
        # 3. HERBE (rencontre sauvage)
        if gestionnaire_map.is_grass(joueur.tuile_x, joueur.tuile_y):
            self._verifier_rencontre_sauvage()
    
    
    def _executer_transition(self, transition):
        """
        Téléporte le joueur vers une nouvelle zone.
        
        Args:
            transition: dict avec "destination_map", "destination_x", "destination_y"
        """
        joueur = self.game_manager.player
        
        # Mettre à jour la zone du joueur
        joueur.zone_actuelle = transition["destination_map"]
        joueur.set_position_tuiles(
            transition["destination_x"],
            transition["destination_y"]
        )
        
        # Recharger la zone
        self._charger_zone_actuelle()
        
        # Afficher le nom de la zone
        self.hud.show_zone_name(joueur.zone_actuelle)
        
        # Changer la musique
        self.game_manager.audio_manager.play_music(joueur.zone_actuelle)
        
        # Sauvegarde automatique
        try:
            from core.save_manager import SaveManager
            if self.game_manager.slot_sauvegarde_actuel is not None:
                save_manager = SaveManager()
                save_manager.auto_save(
                    self.game_manager,
                    self.game_manager.slot_sauvegarde_actuel
                )
        except:
            pass  # La sauvegarde auto n'est pas critique
    
    
    def _verifier_rencontre_sauvage(self):
        """
        Tire au sort une rencontre sauvage (15% de chance).
        Si oui, génère un Pokémon sauvage et lance le combat.
        """
        if random.random() >= ENCOUNTER_RATE:
            return  # Pas de rencontre
        
        joueur = self.game_manager.player
        
        # Vérifier que le joueur a au moins un Pokémon vivant
        if not joueur.team.a_pokemon_valide():
            return
        
        # Générer le Pokémon sauvage
        pokemon_sauvage = self._generer_pokemon_sauvage(joueur.zone_actuelle)
        
        # Lancer le combat
        from states.state_combat import StateCombat
        combat = StateCombat(
            self.game_manager,
            pokemon_adverse=pokemon_sauvage,
            type_combat="sauvage"
        )
        self.game_manager.state_manager.push(combat)
    
    
    def _generer_pokemon_sauvage(self, zone):
        """
        Génère un Pokémon sauvage adapté à la zone.
        
        Args:
            zone: le nom de la zone
            
        Returns:
            objet Pokemon
        """
        from entities.pokemon import Pokemon
        
        # Plage de niveaux pour la zone
        niveau_min, niveau_max = WILD_POKEMON_LEVELS[zone]
        niveau = random.randint(niveau_min, niveau_max)
        
        # Choisir un Pokémon de base (stade 1) aléatoire
        # pokemon.json contient les 54 Pokémon, on filtre les stade 1
        pokemons_base = self.game_manager.pokemon_data.get_stade1_ids()
        pokemon_id = random.choice(pokemons_base)
        
        # Créer le Pokémon
        pokemon = Pokemon.from_data(pokemon_id, niveau)
        
        return pokemon
    
    
    def _verifier_dresseurs(self):
        """
        Vérifie si un dresseur non battu voit le joueur.
        
        Returns:
            True si un combat a été déclenché, False sinon
        """
        joueur = self.game_manager.player
        
        for pnj in self.pnj:
            # Vérifier que c'est un dresseur
            if not hasattr(pnj, 'est_dresseur') or not pnj.est_dresseur:
                continue
            
            # Vérifier qu'il n'est pas déjà battu
            if pnj.est_battu(joueur):
                continue
            
            # Vérifier la vision
            if pnj.peut_voir_joueur(joueur.get_position_tuiles()):
                self._lancer_combat_dresseur(pnj)
                return True
        
        return False
    
    
    def _lancer_combat_dresseur(self, dresseur):
        """
        Lance un combat contre un dresseur.
        
        Args:
            dresseur: l'instance du dresseur
        """
        from states.state_combat import StateCombat
        
        combat = StateCombat(
            self.game_manager,
            pokemon_adverse=dresseur.get_premier_pokemon(),
            type_combat="dresseur",
            dresseur=dresseur
        )
        self.game_manager.state_manager.push(combat)
    
    
    def _tenter_interaction(self):
        """
        Vérifie si un PNJ est devant le joueur et lance l'interaction.
        """
        joueur = self.game_manager.player
        
        # Calculer la tuile devant le joueur
        tuile_devant_x, tuile_devant_y = joueur.get_tuile_devant()
        
        # Chercher un PNJ sur cette tuile
        pnj_trouve = None
        for pnj in self.pnj:
            if pnj.tuile_x == tuile_devant_x and pnj.tuile_y == tuile_devant_y:
                pnj_trouve = pnj
                break
        
        if pnj_trouve is None:
            return
        
        # Faire tourner le PNJ vers le joueur
        pnj_trouve.faire_face_a(joueur.get_position_tuiles())
        
        # Obtenir les lignes de dialogue
        donnees_dialogue = pnj_trouve.interagir(joueur, self.game_manager)
        
        # Lancer le dialogue
        from states.state_dialogue import StateDialogue
        dialogue = StateDialogue(
            self.game_manager,
            lignes=donnees_dialogue["lignes"],
            pnj=pnj_trouve,
            callback=donnees_dialogue.get("callback", None)
        )
        self.game_manager.state_manager.push(dialogue)
    
    
    # -------------------------------------------------------------------------
    # AFFICHAGE
    # -------------------------------------------------------------------------
    
    def render(self, screen):
        """
        Dessine l'écran d'exploration.
        
        L'ordre est crucial :
        1. Map couches basses (sol)
        2. PNJ (triés par Y pour la profondeur)
        3. Joueur
        4. Map couches hautes (toits)
        5. Filtre jour/nuit
        6. HUD
        """
        joueur = self.game_manager.player
        gestionnaire_map = self.game_manager.map_manager
        offset = self.camera.get_offset()
        
        # 1. MAP COUCHES BASSES
        gestionnaire_map.draw_bottom(screen, offset)
        
        # 2. ENTITÉS (PNJ + Joueur) triées par Y
        entites = self.pnj.copy()
        entites.append(joueur)
        entites.sort(key=lambda e: e.get_y_pixel())
        
        for entite in entites:
            pos_ecran = (
                entite.get_x_pixel() - offset[0],
                entite.get_y_pixel() - offset[1]
            )
            screen.blit(entite.get_sprite(), pos_ecran)
        
        # 3. MAP COUCHES HAUTES
        gestionnaire_map.draw_top(screen, offset)
        
        # 4. FILTRE JOUR/NUIT
        self.game_manager.day_night_cycle.draw_filter(screen)
        
        # 5. HUD
        self.hud.draw(screen)