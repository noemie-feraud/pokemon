import json
from config.settings import POKEMON_DATA_FILE

class PokemonCatalog:
    def __init__(self):
        with open(POKEMON_DATA_FILE, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        # Index par ID pour accès rapide
        self.by_id = {p['id']: p for p in self.data}
        # Liste de tous les IDs
        self.all_ids = sorted(self.by_id.keys())

    def get_info(self, pokemon_id):
        """Return the full data dict for a given Pokemon ID."""
        return self.by_id.get(pokemon_id)

    def get_all_ids(self):
        """Return list of all Pokemon IDs."""
        return self.all_ids

    def get_stage1_ids(self):
        """Return IDs of all stage 1 Pokemon."""
        return [pid for pid, data in self.by_id.items() if data.get('evolution_stage') == 1]