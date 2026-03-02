def get_story_hint(player):
    """
    Retourne le monologue intérieur du joueur selon l'état du jeu.
    Affiché comme bulle de pensée en exploration.
    """
    zone    = player.current_zone
    beaten  = len(player.trainers_beaten)

    # ── Tournoi gagné ─────────────────────────────────────────────────────────
    if player.tournament_won:
        return (
            "CHAMPION ! L'alternance est décrochée !\n"
            "Je peux enfin mettre 'Pokémon Master'\n"
            "sur LinkedIn, juste après 'RAG expert'."
        )

    # ── Maps de tournoi ────────────────────────────────────────────────────────
    if zone == "finale":
        return (
            "La FINALE !\n"
            "Un combat, une alternance.\n"
            "J'ai demandé sa stratégie à Claude.\n"
            "Il m'a dit 'bonne chance'. Très utile."
        )

    if zone == "demi":
        return (
            "Demi-finale !\n"
            "L'adversaire a sûrement fine-tuné\n"
            "ses Pokémon sur GPU. Moi j'ai juste\n"
            "travaillé dur. Et un peu Copilot."
        )

    if zone == "quart":
        return (
            "Quarts de finale !\n"
            "Si je perds, je retourne faire\n"
            "du prompt engineering en CDI.\n"
            "Je DOIS gagner."
        )

    # ── Arène (pré-tournoi) ───────────────────────────────────────────────────
    if zone == "arena":
        return (
            "L'arène de La Plateforme !\n"
            "C'est ici le grand tournoi.\n"
            "Le gagnant décroche une alternance.\n"
            "Allons-y, pas question de rater ça !"
        )

    # ── Pas encore de starter ──────────────────────────────────────────────────
    if not player.starter_received:
        return (
            "Le Prof. Akram distribue les Pokémon\n"
            "de départ quelque part sur le campus.\n"
            "Je dois le trouver !\n"
        )

    # ── Starter reçu, aucun combat ────────────────────────────────────────
    if beaten == 0:
        name = ""
        try:
            first = player.team.get_first_valid()
            if first:
                name = f" {first.name}"
        except Exception:
            pass
        return (
            f"Mon Pokémon{name} est prêt !\n"
            "ChatGPT m'a dit de 'just vibe'.\n"
            "Je vais plutôt aller m'entraîner\n"
            "sérieusement. Enfin... un peu."
        )

    # ── Peu d'entraînement ─────────────────────────────────────────────────────
    if beaten < 3:
        return (
            "L'entraînement progresse !\n"
            "Je dois battre encore quelques\n"
            "adversaires avant le grand tournoi.\n"
            "Direction l'arène quand je serai prêt."
        )

    # ── Prêt pour le tournoi ───────────────────────────────────────────────
    return (
        "Je me sens prêt pour le tournoi !\n"
        "Direction l'arène pour décrocher\n"
        "mon alternance.\n"
    )
