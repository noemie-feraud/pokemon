# =============================================================================
# SAVE_MANAGER.PY - SAVE GAME MANAGER
# =============================================================================
#
# This is the save manager. Handles all save/load operations:
# - 3 save slots
# - Manual save (from pause menu)
# - Auto-save (after key events)
# - Load game

import json
import os
from config.settings import SAVES_DIR, SAVE_SLOTS


# =============================================================================
# SAVE MANAGER CLASS
# =============================================================================

class SaveManager:
    """
    Manages all save operations. Created when needed, no heavy internal state.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self):
        """Check that saves folder exists, create if necessary."""
        self._ensure_saves_folder()
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _ensure_saves_folder(self):
        """Create saves folder if it doesn't exist."""
        if not os.path.exists(SAVES_DIR):
            os.makedirs(SAVES_DIR)
    
    
    def _get_slot_path(self, slot_index):
        """
        Return full path to a slot file.
        
        Args:
            slot_index: 0, 1, or 2 (internal 0-based)
        
        Returns:
            Path object
        """
        slot_number = slot_index + 1
        return SAVES_DIR / f"slot_{slot_number}.json"
    
    
    def _validate_save_data(self, data):
        """
        Check if loaded save has minimum required fields.
        Protects against corrupted or manually edited files.
        
        Args:
            data: loaded dictionary
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["trainer", "team", "storage", "credits"]
        
        for field in required_fields:
            if field not in data:
                return False
        
        # Check trainer has necessary sub-fields
        trainer = data["trainer"]
        if "name" not in trainer or "character_id" not in trainer:
            return False
        
        return True
    
    
    def _get_date_time(self):
        """Return current date and time formatted for metadata."""
        from datetime import datetime
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def slot_exists(self, slot_index):
        """
        Check if a save slot exists (file present).
        
        Args:
            slot_index: 0, 1, or 2
        
        Returns:
            True if file exists, False otherwise
        """
        path = self._get_slot_path(slot_index)
        return os.path.exists(path)
    
    
    def get_slot_info(self, slot_index):
        """
        Return summary info for a slot (for menu display).
        
        Args:
            slot_index: 0, 1, or 2
        
        Returns:
            dict with keys:
                "occupied": bool
                "trainer_name": str
                "zone": str
                "team_size": int
                "max_level": int
                "play_time": int (seconds)
                "play_time_formatted": str (HHhMM)
                "pokedex_count": int
                "corrupted": bool (optional)
        """
        path = self._get_slot_path(slot_index)
        
        if not os.path.exists(path):
            return {"occupied": False}
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Basic validation
                if "trainer" not in data:
                    return {"occupied": False, "corrupted": True}
                
                trainer_data = data["trainer"]
                team_data = data.get("team", [])
                
                # Calculate max level in team
                max_level = 0
                for poke in team_data:
                    if poke.get("level", 0) > max_level:
                        max_level = poke["level"]
                
                # Format play time (play_time is a float, cast to int first)
                time_seconds = int(data.get("play_time", 0))
                hours = time_seconds // 3600
                minutes = (time_seconds % 3600) // 60
                
                pokedex_data = data.get("pokedex", {})
                pokedex_count = len(pokedex_data.get("seen", []))
                
                return {
                    "occupied": True,
                    "trainer_name": trainer_data.get("name", "???"),
                    "zone": trainer_data.get("position", {}).get("zone", "?"),
                    "team_size": len(team_data),
                    "max_level": max_level,
                    "play_time": time_seconds,
                    "play_time_formatted": f"{hours:02d}h{minutes:02d}",
                    "pokedex_count": pokedex_count
                }
        
        except Exception:
            return {"occupied": False, "corrupted": True}
    
    
    def get_all_slots_info(self):
        """
        Return info for all 3 slots.
        
        Returns:
            list of 3 dicts (see get_slot_info)
        """
        infos = []
        for i in range(SAVE_SLOTS):
            infos.append(self.get_slot_info(i))
        return infos
    
    
    def save(self, game_manager, slot_index):
        """
        Full save of game state to a slot.
        
        Args:
            game_manager: Game object containing all data
            slot_index: 0, 1, or 2
        
        Returns:
            True if save succeeded, False otherwise
        """
        player = game_manager.player
        path = self._get_slot_path(slot_index)
        
        if player is None:
            return False
        
        # Build data
        data = {
            "trainer": {
                "name": player.name,
                "character_id": player.character_id,
                "position": {
                    "zone": player.current_zone,
                    "x": player.x,
                    "y": player.y
                }
            },
            "team": player.team.to_list(),
            "storage": player.storage.to_list(),
            "inventory": player.inventory.to_dict() if hasattr(player, "inventory") else {"items": {}},
            "credits": player.credits,
            "trainers_beaten": player.trainers_beaten,
            "quests_completed": player.quests_completed,
            "quests_active": player.active_quests,
            "pokedex": player.pokedex.to_dict() if hasattr(player, "pokedex") else {"seen": [], "captured": []},
            "day_night_time": game_manager.day_night_cycle.current_time,
            "play_time": player.play_time,
            "_metadata": {
                "version": "1.0",
                "save_date": self._get_date_time()
            }
        }
        
        try:
            self._ensure_saves_folder()
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Save error: {e}")
            return False
    
    
    def auto_save(self, game_manager, slot_index):
        """
        Auto-save (same as save, but called automatically).
        
        Args:
            game_manager: Game object
            slot_index: 0, 1, or 2
        
        Returns:
            True if save succeeded, False otherwise
        """
        if slot_index is None:
            return False
        
        return self.save(game_manager, slot_index)
    
    
    def load(self, slot_index):
        """
        Load a save and return raw data.
        
        Args:
            slot_index: 0, 1, or 2
        
        Returns:
            dict of save data if successful, None otherwise
        """
        path = self._get_slot_path(slot_index)
        
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not self._validate_save_data(data):
                print(f"Warning: Corrupted save: {path}")
                return None
            
            return data
        
        except Exception:
            return None
    
    
    def delete_slot(self, slot_index):
        """
        Delete a save file.
        
        Args:
            slot_index: 0, 1, or 2
        
        Returns:
            True if deletion succeeded (or file didn't exist), False on error
        """
        path = self._get_slot_path(slot_index)
        
        if not os.path.exists(path):
            return True
        
        try:
            os.remove(path)
            return True
        except Exception:
            return False
    
    
    def is_slot_corrupted(self, slot_index):
        """
        Check if a slot is corrupted without fully loading it.
        
        Args:
            slot_index: 0, 1, or 2
        
        Returns:
            True if file exists but is invalid
        """
        info = self.get_slot_info(slot_index)
        return info.get("corrupted", False)
    
    
    def get_occupied_slots_count(self):
        """
        Return number of occupied slots (for UI).
        
        Returns:
            int between 0 and SAVE_SLOTS
        """
        count = 0
        for i in range(SAVE_SLOTS):
            if self.slot_exists(i):
                count += 1
        return count
    
    
    def get_first_free_slot(self):
        """
        Return index of first empty slot.
        
        Returns:
            slot_index (0-based) or None if all slots are occupied
        """
        for i in range(SAVE_SLOTS):
            if not self.slot_exists(i):
                return i
        return None
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHOD
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """Debug representation."""
        occupied = self.get_occupied_slots_count()
        return f"SaveManager ({SAVE_SLOTS} slots, {occupied} occupied)"