import requests
import json
import os

# Création d'un dossier pour ranger les images 
dossier_sprites = "sprites_pokemon"
if not os.path.exists(dossier_sprites):
    os.makedirs(dossier_sprites)

# Stockage les infos avant de créer le JSON
liste_pokemons = []

mes_pokemons = [
    1, 2, 3, #F.Bulbizzare
    4, 5, 6, #Salamèche
    7, 8, 9, #Carapuce
    10, 11, 12, #F.Chenipan
    13, 14, 15, #F.Aspicot
    16, 17, 18, #F.Roucool
    29, 30, 31, #F.Nidoran F
    32, 33, 34, #F.Nidoran M
    60, 61, 62, #F.Mystherbe
    63, 64, 65, #F.Abra
    66, 67, 68, #F.Machoc
    69, 70, 71, #F.Chétiflor
    74, 75, 76, #F.Racaillou
    92, 93, 94, #F.Fantominus
    147, 148, 149, #F.Minidraco
    155, 156, 157, #F.Héricendre
    158, 159, 160, #F.Kaiminus
]

print(f"Démarrage du téléchargement de {len(mes_pokemons)} Pokémons...")

# La boucle lit la liste
for compteur, id_pokemon in enumerate(mes_pokemons, 1):
    
    # On utilise id_pokemon
    url = f"https://pokeapi.co/api/v2/pokemon/{id_pokemon}"
    
    try:
        reponse = requests.get(url)
        
        # Si l'API répond "OK" (code 200)
        if reponse.status_code == 200:
            data = reponse.json()
            
            # EXTRACTION DES TEXTES 
            nom = data['name'].capitalize()
            pv = data['stats'][0]['base_stat']
            attaque = data['stats'][1]['base_stat']
            defense = data['stats'][2]['base_stat']
            type_poke = data['types'][0]['type']['name'].capitalize()
            
            url_image = data['sprites']['front_default']
            chemin_image = f"{dossier_sprites}/{nom}.png"
            
            # On télécharge la vraie image
            if url_image:
                img_data = requests.get(url_image).content
                with open(chemin_image, 'wb') as fichier_image:
                    fichier_image.write(img_data)
                
            # Rangement pour le JSON
            liste_pokemons.append({
                "id": id_pokemon, # On garde le vrai ID (ex: 155)
                "nom": nom,
                "type": type_poke,
                "pv": pv,
                "attaque": attaque,
                "defense": defense,
                "chemin_image": chemin_image
            })
            
            print(f"[{compteur}/54] {nom} (ID: {id_pokemon}) sauvegardé !")
            
    except Exception as e:
        print(f"Erreur avec le Pokémon ID {id_pokemon}: {e}")

#On transforme notre liste Python en un beau fichier pokemon.json
with open("pokemon.json", "w", encoding="utf-8") as fichier_json:
    json.dump(liste_pokemons, fichier_json, indent=4, ensure_ascii=False)

print("Téléchargement effectué !")