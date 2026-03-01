# =============================================================================
# POKEMON_SCRAPER.PY - POKEMON DATA SCRAPER
# =============================================================================
#
# Utility script (not executed during gameplay).
# Run once at project start to:
# 1. Fetch data from PokéAPI for our 54 selected Pokemon
# 2. Generate data/pokemon.json with our humorous names
# 3. Download sprites to assets/sprites/pokemon/

import requests
import json
import time
import os
from pathlib import Path


# =============================================================================
# CONSTANTS
# =============================================================================

# Base directory (script is in scripts/, project root is parent)
BASE_DIR = Path(__file__).parent.parent

DATA_DIR = BASE_DIR / "data"
SPRITES_DIR = BASE_DIR / "assets" / "sprites" / "pokemon"

# List of 54 Pokemon IDs (18 types × 3 stages)
# Classic Gen 1 IDs for simplicity
POKEMON_IDS = [
    # Grass
    1, 2, 3,      # Bulbasaur, Ivysaur, Venusaur
    # Fire
    4, 5, 6,      # Charmander, Charmeleon, Charizard
    # Water
    7, 8, 9,      # Squirtle, Wartortle, Blastoise
    # Normal
    16, 17, 18,   # Pidgey, Pidgeotto, Pidgeot
    # Electric
    25, 26,       # Pikachu, Raichu (only 2 stages)
    # Bug
    10, 11, 12,   # Caterpie, Metapod, Butterfree
    # Poison
    13, 14, 15,   # Weedle, Kakuna, Beedrill
    # Ground
    50, 51, 52,   # Diglett, Dugtrio, ??? (using Meowth as placeholder)
    # Rock
    74, 75, 76,   # Geodude, Graveler, Golem
    # Fighting
    66, 67, 68,   # Machop, Machoke, Machamp
    # Psychic
    63, 64, 65,   # Abra, Kadabra, Alakazam
    # Ghost
    92, 93, 94,   # Gastly, Haunter, Gengar
    # Ice
    86, 87,       # Seel, Dewgong (only 2 stages)
    # Dragon
    147, 148, 149, # Dratini, Dragonair, Dragonite
    # Dark (use Gen 2)
    197,          # Umbreon (placeholder)
    # Steel (use Gen 2)
    208,          # Steelix (placeholder)
    # Fairy (use Gen 6)
    700,          # Sylveon (placeholder)
]

# Type to day/night mapping
TYPE_DAY_NIGHT = {
    "grass": "diurne",
    "fire": "diurne",
    "water": "diurne",
    "electric": "diurne",
    "normal": "diurne",
    "flying": "diurne",
    "bug": "diurne",
    "rock": "diurne",
    "ground": "diurne",
    "fighting": "diurne",
    "psychic": "nocturne",
    "ghost": "nocturne",
    "dark": "nocturne",
    "fairy": "nocturne",
    "steel": "nocturne",
    "ice": "nocturne",
    "dragon": "nocturne",
    "poison": "nocturne"
}

# Humorous names (to be filled by creative team)
# Placeholders for now
HUMOROUS_NAMES = {
    1: "BulbyLePlanteur",
    2: "HerbizarreDeLaMort",
    3: "FlorizarreMax",
    4: "SalamècheLeCodeur",
    5: "ReptincelEnRage",
    6: "DracaufeuDesSGBD",
    7: "CarapuceLaPotion",
    8: "TortankLeNull",
    9: "AquaBug",
    # ... to be completed
}

# Request delay to avoid rate limiting
REQUEST_DELAY = 0.5  # 500ms


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def fetch_pokemon_data(pokemon_id):
    """Fetch Pokemon data from PokéAPI."""
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    
    for attempt in range(3):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                time.sleep(1)
        except Exception:
            time.sleep(1)
    
    print(f"Failed to fetch Pokemon {pokemon_id}")
    return None


def fetch_evolution_chain(species_url):
    """Fetch evolution chain from species URL."""
    try:
        response = requests.get(species_url)
        if response.status_code != 200:
            return None
        
        species_data = response.json()
        evolution_url = species_data["evolution_chain"]["url"]
        
        response_evo = requests.get(evolution_url)
        if response_evo.status_code != 200:
            return None
        
        evo_data = response_evo.json()
        chain = evo_data["chain"]
        
        # Simple parsing: get first evolution
        if "evolves_to" in chain and len(chain["evolves_to"]) > 0:
            evolution = chain["evolves_to"][0]
            evolution_id = int(evolution["species"]["url"].split("/")[-2])
            
            level = 16  # default
            if len(evolution["evolution_details"]) > 0:
                details = evolution["evolution_details"][0]
                if "min_level" in details and details["min_level"] is not None:
                    level = details["min_level"]
            
            return {"to": evolution_id, "level": level}
    
    except Exception:
        pass
    
    return None


def download_sprite(url, dest_path):
    """Download a sprite and save to file."""
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return False
        
        with open(dest_path, "wb") as f:
            f.write(response.content)
        
        return True
    except Exception:
        return False


def extract_attacks(moves_data):
    """Extract up to 6 attacks from moves list."""
    attacks = []
    
    for move_entry in moves_data:
        if len(attacks) >= 6:
            break
        
        move_url = move_entry["move"]["url"]
        
        try:
            response = requests.get(move_url)
            if response.status_code != 200:
                continue
            
            move_detail = response.json()
            
            # Keep only attacks with power
            power = move_detail.get("power", 0)
            if power == 0:
                continue
            
            attack_type = move_detail["type"]["name"]
            
            attacks.append({
                "name": move_detail["name"],
                "type": attack_type,
                "power": power
            })
        
        except Exception:
            continue
    
    return attacks


def build_pokemon_data(raw_data):
    """Build our Pokemon data dict from raw API data."""
    pokemon_id = raw_data["id"]
    
    # Types
    types = []
    for type_entry in raw_data["types"]:
        types.append(type_entry["type"]["name"])
    
    # Day/night based on first type
    primary_type = types[0] if types else "normal"
    day_night = TYPE_DAY_NIGHT.get(primary_type, "diurne")
    
    # Evolution
    species_url = raw_data["species"]["url"]
    evolution = fetch_evolution_chain(species_url)
    
    # Stage (rough estimate)
    stage = 1
    if evolution and evolution["to"] < pokemon_id:
        stage = 2
    
    # Sprites
    sprites_data = raw_data["sprites"]
    front_url = sprites_data["front_default"]
    back_url = sprites_data["back_default"]
    
    # Names
    name_original = raw_data["name"]
    name_custom = HUMOROUS_NAMES.get(pokemon_id, name_original.title())
    
    # Base stats
    stats = {}
    for stat_entry in raw_data["stats"]:
        stat_name = stat_entry["stat"]["name"]
        value = stat_entry["base_stat"]
        if stat_name == "hp":
            stats["hp"] = value
        elif stat_name == "attack":
            stats["attack"] = value
        elif stat_name == "defense":
            stats["defense"] = value
    
    # Attacks
    attacks = extract_attacks(raw_data["moves"])
    
    return {
        "id": pokemon_id,
        "name_original": name_original,
        "name_custom": name_custom,
        "types": types,
        "base_stats": stats,
        "evolution": evolution,
        "day_night": day_night,
        "stage": stage,
        "sprite_front": f"assets/sprites/pokemon/{pokemon_id}_front.png",
        "sprite_back": f"assets/sprites/pokemon/{pokemon_id}_back.png",
        "all_attacks": attacks
    }


def download_all_sprites(pokemon_list):
    """Download all sprites for given Pokemon list."""
    count = 0
    
    for pokemon in pokemon_list:
        pokemon_id = pokemon["id"]
        
        # Create folder if needed
        if not os.path.exists(SPRITES_DIR):
            os.makedirs(SPRITES_DIR)
        
        # Front sprite
        front_path = SPRITES_DIR / f"{pokemon_id}_front.png"
        front_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png"
        
        if download_sprite(front_url, front_path):
            count += 1
        
        # Back sprite
        back_path = SPRITES_DIR / f"{pokemon_id}_back.png"
        back_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/{pokemon_id}.png"
        
        if download_sprite(back_url, back_path):
            count += 1
        
        time.sleep(REQUEST_DELAY)
    
    return count


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Main scraping function."""
    print("Starting PokéAPI scraping...")
    
    # Create directories
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if not os.path.exists(SPRITES_DIR):
        os.makedirs(SPRITES_DIR)
    
    # List to store all Pokemon data
    pokemon_data = []
    
    total = len(POKEMON_IDS)
    
    for i, pokemon_id in enumerate(POKEMON_IDS):
        print(f"Fetching {i+1}/{total}: Pokemon #{pokemon_id}")
        
        raw_data = fetch_pokemon_data(pokemon_id)
        
        if raw_data is None:
            continue
        
        pokemon = build_pokemon_data(raw_data)
        pokemon_data.append(pokemon)
        
        time.sleep(REQUEST_DELAY)
    
    # Save JSON
    json_path = DATA_DIR / "pokemon.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(pokemon_data, f, indent=2, ensure_ascii=False)
    
    print(f"JSON file generated: {json_path}")
    
    # Download sprites
    print("Downloading sprites...")
    sprite_count = download_all_sprites(pokemon_data)
    print(f"Downloaded {sprite_count} sprites")
    
    print("Scraping complete!")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()


# =============================================================================
# POST-SCRAPING NOTES
# =============================================================================
#
# After running this script:
#
# 1. Edit data/pokemon.json manually to:
#    - Replace "name_custom" with real humorous names
#    - Adjust "day_night" if needed (some Pokemon may be mixed)
#    - Verify evolutions (API may give incomplete info)
#
# 2. Check that all sprites are present
#    (some Pokemon may not have back sprites in API)
#
# 3. Commit the JSON file and sprites to Git
#    (so the whole team has the same base)