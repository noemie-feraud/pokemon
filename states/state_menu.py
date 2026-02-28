# =============================================================================
# STATE_MENU.PY - ÉTAT DU MENU PRINCIPAL
# =============================================================================
#
# C'est le premier écran que le joueur voit au lancement du jeu.
# Il choisit entre "Nouvelle Partie", "Continuer" (charger) et "Quitter".

import pygame
from states.state import State
from entities.player import Player
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, CHAR_WIDTH, CHAR_HEIGHT


# =============================================================================
# CONSTANTES LOCALES
# =============================================================================

MODE_PRINCIPAL = "principal"
MODE_CHOIX_DRESSEUR = "choix_dresseur"
MODE_CHOIX_SLOT = "choix_slot"


# =============================================================================
# CLASSE STATE MENU
# =============================================================================

class StateMenu(State):
    """
    État du menu principal.
    
    Modes :
    - MODE_PRINCIPAL : menu avec 3 options (Nouvelle Partie / Continuer / Quitter)
    - MODE_CHOIX_DRESSEUR : joueur choisit entre les 2 personnages
    - MODE_CHOIX_SLOT : joueur choisit un slot de sauvegarde
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTEUR
    # -------------------------------------------------------------------------
    
    def __init__(self, game_manager):
        """Initialise le menu principal."""
        super().__init__(game_manager)
        
        # --- POLICES ---
        self.font_titre = pygame.font.Font(None, 60)
        self.font_menu = pygame.font.Font(None, 32)
        self.font_info = pygame.font.Font(None, 22)
        
        # --- MODE ET CURSEUR ---
        self.mode = MODE_PRINCIPAL
        self.index_selection = 0
        
        # --- OPTIONS DU MENU PRINCIPAL ---
        self.options_principales = ["Nouvelle Partie", "Continuer", "Quitter"]
        
        # --- INFORMATIONS DES SAUVEGARDES ---
        self.infos_slots = None
        self.continuer_disponible = False
        self._charger_infos_slots()
        
        # --- DONNÉES DES PERSONNAGES ---
        self.personnages = [
            {"id": 1, "nom": "Linus", "description": "Un codeur décontracté, toujours un café à la main"},
            {"id": 2, "nom": "Ada", "description": "Une analyste brillante, carnet toujours en main"}
        ]
    
    
    # -------------------------------------------------------------------------
    # MÉTHODES PRIVÉES
    # -------------------------------------------------------------------------
    
    def _charger_infos_slots(self):
        """
        Charge les informations des slots de sauvegarde.
        Détermine si le bouton "Continuer" doit être disponible.
        """
        try:
            from core.save_manager import SaveManager
            
            gestionnaire_sauvegarde = SaveManager()
            self.infos_slots = gestionnaire_sauvegarde.get_all_slots_info()
            
            # Vérifier si au moins un slot est occupé
            self.continuer_disponible = False
            for slot in self.infos_slots:
                if slot is not None and slot.get("occupied", False):
                    self.continuer_disponible = True
                    break
                    
        except Exception:
            self.infos_slots = [None, None, None]
            self.continuer_disponible = False
    
    
    # -------------------------------------------------------------------------
    # MÉTHODES DE CYCLE DE VIE
    # -------------------------------------------------------------------------
    
    def on_enter(self):
        """Appelé quand le menu devient actif."""
        self.game_manager.audio_manager.play_music("menu")
    
    
    # -------------------------------------------------------------------------
    # GESTION DES ÉVÉNEMENTS
    # -------------------------------------------------------------------------
    
    def handle_events(self, events):
        """Gère les entrées du joueur selon le mode actuel."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            
            if self.mode == MODE_PRINCIPAL:
                self._gerer_principal(event)
            
            elif self.mode == MODE_CHOIX_DRESSEUR:
                self._gerer_choix_dresseur(event)
            
            elif self.mode == MODE_CHOIX_SLOT:
                self._gerer_choix_slot(event)
    
    
    def _gerer_principal(self, event):
        """Gère les entrées en mode menu principal."""
        
        # Navigation
        if event.key == pygame.K_UP:
            self.index_selection = max(0, self.index_selection - 1)
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        elif event.key == pygame.K_DOWN:
            self.index_selection = min(len(self.options_principales) - 1, self.index_selection + 1)
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        # Sélection
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            
            # NOUVELLE PARTIE
            if self.index_selection == 0:
                self.mode = MODE_CHOIX_DRESSEUR
                self.index_selection = 0
            
            # CONTINUER
            elif self.index_selection == 1:
                if self.continuer_disponible:
                    self.mode = MODE_CHOIX_SLOT
                    self.index_selection = 0
            
            # QUITTER
            elif self.index_selection == 2:
                self.game_manager.running = False
    
    
    def _gerer_choix_dresseur(self, event):
        """Gère les entrées en mode choix du personnage."""
        
        # Navigation (gauche/droite entre les 2 personnages)
        if event.key == pygame.K_LEFT:
            self.index_selection = 0
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        elif event.key == pygame.K_RIGHT:
            self.index_selection = 1
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        # Retour au menu principal
        elif event.key == pygame.K_ESCAPE:
            self.mode = MODE_PRINCIPAL
            self.index_selection = 0
        
        # Confirmation
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            self._demarrer_nouvelle_partie(self.personnages[self.index_selection])
    
    
    def _gerer_choix_slot(self, event):
        """Gère les entrées en mode choix du slot de sauvegarde."""
        
        # Navigation (haut/bas entre les 3 slots)
        if event.key == pygame.K_UP:
            self.index_selection = max(0, self.index_selection - 1)
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        elif event.key == pygame.K_DOWN:
            self.index_selection = min(2, self.index_selection + 1)
            self.game_manager.audio_manager.play_sfx("menu_select")
        
        # Retour au menu principal
        elif event.key == pygame.K_ESCAPE:
            self.mode = MODE_PRINCIPAL
            self.index_selection = 1  # Retour sur "Continuer"
        
        # Confirmation
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            slot = self.infos_slots[self.index_selection]
            if slot is not None and slot.get("occupied", False):
                self._charger_sauvegarde(self.index_selection)
    
    
    # -------------------------------------------------------------------------
    # ACTIONS DU JEU
    # -------------------------------------------------------------------------
    
    def _demarrer_nouvelle_partie(self, donnees_personnage):
        """
        Crée un nouveau joueur et lance l'exploration.
        
        Args:
            donnees_personnage: dict avec les infos {"id": 1, "nom": "Linus"}
        """
        from entities.item import ItemCatalog
        from entities.inventory import Inventory
        from economy.quest import QuestManager
        
        # Créer le catalogue d'objets
        catalogue_objets = ItemCatalog()
        self.game_manager.item_catalog = catalogue_objets
        
        # Créer le joueur
        joueur = Player(
            character_id=donnees_personnage["id"],
            name=donnees_personnage["nom"]
        )
        
        # Créer l'inventaire (dépend du catalogue)
        joueur.inventory = Inventory(catalogue_objets)
        
        # Attacher le joueur au game_manager
        self.game_manager.player = joueur
        
        # Créer le gestionnaire de quêtes
        self.game_manager.quest_manager = QuestManager()
        
        # Lancer l'exploration
        from states.state_exploration import StateExploration
        
        etat_exploration = StateExploration(self.game_manager)
        self.game_manager.state_manager.change(etat_exploration)
    
    
    def _charger_sauvegarde(self, index_slot):
        """
        Charge une sauvegarde et lance l'exploration.
        
        Args:
            index_slot: 0, 1 ou 2
        """
        from core.save_manager import SaveManager
        from entities.item import ItemCatalog
        from entities.inventory import Inventory
        from economy.quest import QuestManager
        
        try:
            gestionnaire_sauvegarde = SaveManager()
            donnees = gestionnaire_sauvegarde.load(index_slot)
            
            if donnees is None:
                return  # Slot vide ou erreur
            
            # Créer le catalogue d'objets
            catalogue_objets = ItemCatalog()
            self.game_manager.item_catalog = catalogue_objets
            
            # Recréer le joueur depuis la sauvegarde
            joueur = Player.from_save(donnees)
            
            # Recréer l'inventaire depuis la sauvegarde
            joueur.inventory = Inventory.from_dict(
                donnees.get("inventory", {}), catalogue_objets
            )
            
            # Attacher au game_manager
            self.game_manager.player = joueur
            self.game_manager.slot_sauvegarde_actuel = index_slot
            
            # Restaurer le cycle jour/nuit
            if "day_night_time" in donnees:
                self.game_manager.day_night_cycle.set_time(donnees["day_night_time"])
            
            # Créer le gestionnaire de quêtes
            self.game_manager.quest_manager = QuestManager()
            
            # Lancer l'exploration
            from states.state_exploration import StateExploration
            
            etat_exploration = StateExploration(self.game_manager)
            self.game_manager.state_manager.change(etat_exploration)
            
        except Exception as e:
            print(f"Erreur lors du chargement : {e}")
    
    
    # -------------------------------------------------------------------------
    # MISE À JOUR
    # -------------------------------------------------------------------------
    
    def update(self, dt):
        """Rien à mettre à jour dans le menu."""
        pass
    
    
    # -------------------------------------------------------------------------
    # AFFICHAGE
    # -------------------------------------------------------------------------
    
    def render(self, screen):
        """Dessine l'écran du menu selon le mode actuel."""
        # Fond
        screen.fill((20, 20, 40))  # Bleu foncé
        
        if self.mode == MODE_PRINCIPAL:
            self._dessiner_principal(screen)
        
        elif self.mode == MODE_CHOIX_DRESSEUR:
            self._dessiner_choix_dresseur(screen)
        
        elif self.mode == MODE_CHOIX_SLOT:
            self._dessiner_choix_slot(screen)
    
    
    def _dessiner_principal(self, screen):
        """Dessine le menu principal avec le titre et les 3 options."""
        
        # --- TITRE ---
        surface_titre = self.font_titre.render("Pokémon La Plateforme", True, (255, 255, 255))
        pos_x_titre = (SCREEN_WIDTH - surface_titre.get_width()) // 2
        screen.blit(surface_titre, (pos_x_titre, 150))
        
        # --- OPTIONS ---
        for i, option in enumerate(self.options_principales):
            # Grise "Continuer" si pas de sauvegarde
            if i == 1 and not self.continuer_disponible:
                couleur = (100, 100, 100)
            else:
                couleur = (255, 255, 255)
            
            prefixe = "> " if i == self.index_selection else "  "
            texte = prefixe + option
            surface = self.font_menu.render(texte, True, couleur)
            pos_x = (SCREEN_WIDTH - surface.get_width()) // 2
            pos_y = 350 + i * 50
            screen.blit(surface, (pos_x, pos_y))
    
    
    def _dessiner_choix_dresseur(self, screen):
        """Dessine l'écran de choix du personnage."""
        
        # Titre
        surface_titre = self.font_menu.render("Choisis ton dresseur", True, (255, 255, 255))
        pos_x = (SCREEN_WIDTH - surface_titre.get_width()) // 2
        screen.blit(surface_titre, (pos_x, 100))
        
        # Deux cadres côte à côte
        for i, personnage in enumerate(self.personnages):
            cadre_x = 150 + i * 380
            cadre_y = 200
            cadre_largeur = 300
            cadre_hauteur = 300
            
            # Couleur de bordure selon la sélection
            if i == self.index_selection:
                couleur_bordure = (255, 215, 0)  # Doré
                epaisseur = 4
            else:
                couleur_bordure = (100, 100, 100)
                epaisseur = 2
            
            # Dessiner le cadre
            pygame.draw.rect(screen, couleur_bordure,
                           (cadre_x, cadre_y, cadre_largeur, cadre_hauteur), epaisseur)
            
            # Nom du personnage
            surface_nom = self.font_menu.render(personnage["nom"], True, (255, 255, 255))
            pos_x_nom = cadre_x + (cadre_largeur - surface_nom.get_width()) // 2
            screen.blit(surface_nom, (pos_x_nom, cadre_y + 180))
            
            # Description
            surface_desc = self.font_info.render(personnage["description"], True, (200, 200, 200))
            pos_x_desc = cadre_x + (cadre_largeur - surface_desc.get_width()) // 2
            screen.blit(surface_desc, (pos_x_desc, cadre_y + 220))
            
            # Placeholder pour le sprite
            rectangle_sprite = pygame.Rect(cadre_x + 100, cadre_y + 30, 100, 120)
            if i == 0:  # Linus
                pygame.draw.rect(screen, (0, 100, 200), rectangle_sprite)  # Bleu
            else:  # Ada
                pygame.draw.rect(screen, (200, 100, 200), rectangle_sprite)  # Violet
        
        # Indication des contrôles
        surface_aide = self.font_info.render(
            "[←→] Choisir  [Entrée] Valider  [Échap] Retour", True, (150, 150, 150))
        pos_x_aide = (SCREEN_WIDTH - surface_aide.get_width()) // 2
        screen.blit(surface_aide, (pos_x_aide, 550))
    
    
    def _dessiner_choix_slot(self, screen):
        """Dessine l'écran de choix du slot de sauvegarde."""
        
        # Titre
        surface_titre = self.font_menu.render("Choisir une sauvegarde", True, (255, 255, 255))
        pos_x = (SCREEN_WIDTH - surface_titre.get_width()) // 2
        screen.blit(surface_titre, (pos_x, 80))
        
        for i in range(3):
            slot = self.infos_slots[i] if self.infos_slots else None
            cadre_x = 200
            cadre_y = 150 + i * 140
            cadre_largeur = SCREEN_WIDTH - 400
            cadre_hauteur = 110
            
            # Couleur de bordure selon la sélection
            if i == self.index_selection:
                couleur_bordure = (255, 215, 0)  # Doré
                epaisseur = 3
            else:
                couleur_bordure = (100, 100, 100)
                epaisseur = 2
            
            # Dessiner le cadre
            pygame.draw.rect(screen, couleur_bordure,
                           (cadre_x, cadre_y, cadre_largeur, cadre_hauteur), epaisseur)
            
            if slot and slot.get("occupied", False):
                # Slot occupé - afficher les infos
                texte_nom = f"Slot {i+1} — {slot.get('trainer_name', '???')}"
                surface_nom = self.font_menu.render(texte_nom, True, (255, 255, 255))
                screen.blit(surface_nom, (cadre_x + 20, cadre_y + 15))
                
                # Détails
                details = f"Zone: {slot.get('zone', '?')} — Pokémon: {slot.get('team_size', '?')} — Temps: {slot.get('play_time_formatted', '?')}"
                surface_details = self.font_info.render(details, True, (200, 200, 200))
                screen.blit(surface_details, (cadre_x + 20, cadre_y + 55))
                
            else:
                # Slot vide
                texte_vide = f"Slot {i+1} — Vide"
                surface_vide = self.font_menu.render(texte_vide, True, (100, 100, 100))
                screen.blit(surface_vide, (cadre_x + 20, cadre_y + 35))
        
        # Indication des contrôles
        surface_aide = self.font_info.render(
            "[↑↓] Choisir  [Entrée] Charger  [Échap] Retour", True, (150, 150, 150))
        pos_x_aide = (SCREEN_WIDTH - surface_aide.get_width()) // 2
        screen.blit(surface_aide, (pos_x_aide, 590))