# =============================================================================
# DATA/TRAINER_DIALOGUES.PY – Dialogues des dresseurs du tournoi
# =============================================================================
# Clé = npc_name exact tel que défini dans le TMX (après strip des guillemets).
# Chaque dresseur a :
#   "challenge"      → avant le combat
#   "defeat"         → après que le joueur gagne
#   "already_beaten" → si le joueur revient parler après avoir gagné
# =============================================================================

TRAINER_DIALOGUES = {

    # ── Campus ────────────────────────────────────────────────────────────────
    "Maxime": {
        "challenge": [
            "Hé, toi ! T'es en IA/DATA ?",
            "Moi je suis en Logiciel.",
            "On a codé un bot de combat en Java cette semaine.",
            "Il a 12 classes abstraites et un singleton.",
            "Bref, mes Pokémon sont solides. Voyons si les tiens le sont aussi !"
        ],
        "defeat": [
            "Mon architecture était trop couplée...",
            "T'as gagné.",
            "La prochaine fois je ferai un design pattern Factory pour mes attaques.",
            "Voilà tes crédits."
        ],
        "already_beaten": [
            "Je refactorise toute mon équipe.",
            "Reviens dans une semaine.",
            "Je serai SOLID."
        ]
    },

    "Théo": {
        "challenge": [
            "Tu veux te battre ?",
            "Je suis en Web, moi.",
            "J'ai optimisé mes Pokémon avec Lighthouse.",
            "Performance score : 98.",
            "Accessibility score : 42. Mais c'est pas grave.",
            "En garde !"
        ],
        "defeat": [
            "Mon équipe était pas responsive...",
            "Elle marchait bien sur desktop.",
            "Toi t'as joué depuis mobile ?",
            "Non ? Peu importe. GG."
        ],
        "already_beaten": [
            "Je migre toute mon équipe sur Next.js.",
            "Ça changera peut-être quelque chose.",
            "...Probablement pas."
        ]
    },

    "Jade": {
        "challenge": [
            "Stop.",
            "T'as été suivi depuis l'entrée du campus.",
            "Je suis en Cyber.",
            "J'ai analysé ton équipe via le réseau.",
            "J'ai trouvé deux vulnérabilités.",
            "Mais comme c'est fair play... on va faire un combat normal."
        ],
        "defeat": [
            "Ton équipe était patchée.",
            "Zero-day : zero.",
            "GG. T'es clean.",
            "Tiens, tes crédits."
        ],
        "already_beaten": [
            "Je t'ai à l'oeil.",
            "CVE-2025-TA/DATA.",
            "C'est toi la vulnérabilité que j'ai pas encore patchée."
        ]
    },

    # ── Quarts de finale ──────────────────────────────────────────────────────
    "Yanis": {
        "challenge": [
            "T'es arrivé jusqu'en quarts ? Respect.",
            "Moi j'ai entraîné mes Pokémon avec du reinforcement learning.",
            "Learning rate : 0.001. Patience : 50 epochs.",
            "J'ai checké dix fois l'accuracy avant ce tournoi.",
            "Montre-moi si ton modèle est mieux calibré que le mien !"
        ],
        "defeat": [
            "...",
            "Mon val_loss était trop haut.",
            "Je refais le fine-tuning ce soir.",
            "GG. Voilà tes crédits.",
            "En demi-finale t'as Channel. Bonne chance,",
        ],
        "already_beaten": [
            "Mon modèle était en underfitting.",
            "Je savais que t'allais gagner.",
            "...Nan, je savais pas. Gg quand même."
        ]
    },

    # ── Demi-finales ──────────────────────────────────────────────────────────
    "Channel": {
        "challenge": [
            "DEMI-FINALE ! Et t'as mis Yanis en déroute ?",
            "Respect. Mais là c'est moi.",
            "J'ai 60 viewers en direct sur mon stream.",
            "Ils ont tous voté 'Channel va écraser'.",
            "Déçois pas le chat, fais un beau combat !"
        ],
        "defeat": [
            "Nooon le chat va me spam des 'L' pendant une heure...",
            "OK, c'était mérité.",
            "Ton équipe était mieux build que la mienne.",
            "Le chat t'envoie un 'GG WP'.",
            "Va chercher cette alternance, t'as mérité d'aller en finale."
        ],
        "already_beaten": [
            "Mon chat a lag au pire moment.",
            "Sinon j'aurais gagné. Clairement.",
            "...Ouais non. T'étais meilleur. Gg."
        ]
    },

    # ── Finale ────────────────────────────────────────────────────────────────
    "Etudiant B3": {
        "challenge": [
            "LA FINALE.",
            "T'as battu Yanis et Channel...",
            "J'ai préparé cette rencontre depuis le début du semestre.",
            "Pas de LLM. Pas de fine-tuning. Juste du travail.",
            "Prouve-moi que t'as fait pareil.",
            "L'alternance ne se décroche qu'à la sueur de ton GPU !"
        ],
        "defeat": [
            "...",
            "Tu l'as mérité.",
            "T'as tout fait mieux : le build, la stratégie, les matchups.",
            "L'alternance est pour toi.",
            "Moi je retente l'an prochain.",
            "Mais ce soir... c'est toi le champion."
        ],
        "already_beaten": [
            "Champion.",
            "Je remets pas ça en question.",
            "T'as été le meilleur aujourd'hui."
        ]
    },

}


# =============================================================================
# PROFESSOR_DIALOGUES – Dialogue "Discuter" des profs non-Akram
# =============================================================================
# Clé = npc_name exact tel que défini dans le TMX.
# "talk" → affiché quand le joueur choisit "Discuter".
# =============================================================================

PROFESSOR_DIALOGUES = {

    "Tristan": {
        "talk": [
            "Ah, un étudiant.",
            "Je travaille sur un modèle qui prédit les issues de combat Pokémon.",
            "Dataset : 40 000 combats. Accuracy : 94.3%.",
            "Les 5.7% d'erreur ?",
            "Des combats contre des dresseurs IA/DATA.",
            "Vous êtes trop imprévisibles.",
            "C'est soit une force, soit un biais de dataset.",
            "Je pencherais pour les deux.",
            "Bonne chance pour le tournoi.",
            "...Je regarderai les logs."
        ]
    },

}


# =============================================================================
# SHOPKEEPER_DIALOGUES – Dialogue "Discuter" des vendeurs (sans ouvrir la boutique)
# =============================================================================
# Clé = npc_name exact tel que défini dans le TMX.
# "talk" → affiché quand le joueur choisit "Discuter" sans déclencher la boutique.
# =============================================================================

SHOPKEEPER_DIALOGUES = {

    "vendeur": {
        "talk": [
            "T'as vu les prix des abonnements LLM ?",
            "GPT-4 : 20€/mois.",
            "Claude Pro : 18€/mois.",
            "Gemini Advanced : 21.99€/mois.",
            "Copilot Business : 19€/mois.",
            "Et ils te disent tous que c'est 'révolutionnaire'.",
            "Moi je vends des potions à 50 crédits.",
            "Ma boutique tourne depuis 3 ans sans frais d'API.",
            "Et elle hallucine pas les prix.",
            "Alors… t'as besoin de quelque chose ?"
        ]
    },

}
