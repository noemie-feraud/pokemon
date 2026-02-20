import json
import os
from pathlib import Path

from config.settings import NOMBRE_SLOTS_SAUVEGARDE, CHEMIN_SAVES


class SaveManager:

    def __init__(self):
        
        # Initialise le SaveManager.
        
        self.saves_path = Path(CHEMIN_SAVES)
        self._ensure_saves_directory()

    def _ensure_saves_directory(self):
        # Crée le dossier saves/ s'il n'existe pas
        try:
            self.saves_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"[SaveManager] Erreur lors de la création du dossier saves/ : {e}")

    def _get_slot_path(self, slot_number: int) -> Path:
        # Retourne le chemin du fichier JSON pour un slot donné
        return self.saves_path / f"slot_{slot_number}.json"

    def _is_valid_slot(self, slot_number: int) -> bool:
        # Vérifie que le numéro de slot est valide (entre 1 et NOMBRE_SLOTS_SAUVEGARDE)
        return 1 <= slot_number <= NOMBRE_SLOTS_SAUVEGARDE

    def save(self, slot_number: int, game_data: dict) -> bool:
        
        if not self._is_valid_slot(slot_number):
            print(f"[SaveManager] Numéro de slot invalide : {slot_number}")
            return False

        slot_path = self._get_slot_path(slot_number)

        try:
            with open(slot_path, "w", encoding="utf-8") as f:
                json.dump(game_data, f, ensure_ascii=False, indent=4)
            print(f"[SaveManager] Sauvegarde réussie dans le slot {slot_number}.")
            return True
        except OSError as e:
            print(f"[SaveManager] Erreur lors de la sauvegarde dans le slot {slot_number} : {e}")
            return False

    def auto_save(self, slot_number: int, game_data: dict) -> bool:
        
        print(f"[SaveManager] Auto-save déclenché pour le slot {slot_number}.")
        return self.save(slot_number, game_data)

    def load(self, slot_number: int) -> dict | None:
        
        if not self._is_valid_slot(slot_number):
            print(f"[SaveManager] Numéro de slot invalide : {slot_number}")
            return None

        slot_path = self._get_slot_path(slot_number)

        if not slot_path.exists():
            print(f"[SaveManager] Slot {slot_number} vide (fichier absent).")
            return None

        try:
            with open(slot_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[SaveManager] Chargement réussi depuis le slot {slot_number}.")
            return data
        except (json.JSONDecodeError, OSError) as e:
            print(f"[SaveManager] Erreur lors du chargement du slot {slot_number} : {e}")
            return None

    def delete(self, slot_number: int) -> bool:
        
        if not self._is_valid_slot(slot_number):
            print(f"[SaveManager] Numéro de slot invalide : {slot_number}")
            return False

        slot_path = self._get_slot_path(slot_number)

        if not slot_path.exists():
            print(f"[SaveManager] Slot {slot_number} déjà vide, rien à supprimer.")
            return True

        try:
            slot_path.unlink()
            print(f"[SaveManager] Slot {slot_number} supprimé avec succès.")
            return True
        except OSError as e:
            print(f"[SaveManager] Erreur lors de la suppression du slot {slot_number} : {e}")
            return False

    def get_slot_info(self, slot_number: int) -> dict:
        
        data = self.load(slot_number)

        if data is None:
            return {"exists": False}

        try:
            trainer_name = data.get("trainer", {}).get("name", "Inconnu")
            play_time = data.get("play_time", 0)
            pokemon_count = len(data.get("team", [])) + len(data.get("storage", []))
            credits = data.get("credits", 0)

            return {
                "exists": True,
                "trainer_name": trainer_name,
                "play_time": play_time,
                "pokemon_count": pokemon_count,
                "credits": credits,
            }
        except (AttributeError, TypeError) as e:
            print(f"[SaveManager] Données malformées dans le slot {slot_number} : {e}")
            return {"exists": False}

    def get_all_slots_info(self) -> dict:
        
        return {
            slot_number: self.get_slot_info(slot_number)
            for slot_number in range(1, NOMBRE_SLOTS_SAUVEGARDE + 1)
        }