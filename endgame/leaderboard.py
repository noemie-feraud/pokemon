# =============================================================================
# LEADERBOARD.PY - LEADERBOARD SYSTEM
# =============================================================================
#
# Manages tournament victory rankings.
# Stores best times, persists in JSON file.

import json
import os
import datetime


# =============================================================================
# CONSTANTS
# =============================================================================

LEADERBOARD_PATH = "saves/leaderboard.json"
MAX_ENTRIES = 10


# =============================================================================
# LEADERBOARD CLASS
# =============================================================================

class Leaderboard:
    """
    Manages tournament victory rankings.
    Reads and writes JSON file. Self-contained, no Pygame dependency.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self):
        """Load leaderboard from file. Start empty if file missing/corrupted."""
        self.entries = []
        self._load()
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _load(self):
        """Read JSON file and load entries."""
        try:
            if os.path.exists(LEADERBOARD_PATH):
                with open(LEADERBOARD_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.entries = data.get("entries", [])
                    
                    # Validate entries
                    self.entries = [e for e in self.entries if self._validate_entry(e)]
                    
                    # Sort for safety
                    self._sort()
            else:
                self.entries = []
        
        except Exception:
            # Corrupted or unreadable → start fresh
            self.entries = []
    
    
    def _validate_entry(self, entry):
        """Check if an entry has minimum required fields."""
        if not isinstance(entry, dict):
            return False
        
        required = ["name", "time_seconds"]
        for field in required:
            if field not in entry:
                return False
        
        # Time must be positive number
        if not isinstance(entry["time_seconds"], (int, float)):
            return False
        if entry["time_seconds"] < 0:
            return False
        
        return True
    
    
    def _sort(self):
        """
        Sort entries by:
        1. Time ascending (fastest first)
        2. Pokedex descending (most complete first, tie-breaker)
        3. Date descending (most recent first, tie-breaker)
        """
        self.entries.sort(
            key=lambda e: (
                e.get("time_seconds", 999999),
                -e.get("pokedex_count", 0),
                e.get("date", "")    # ISO dates sort naturally
            )
        )
    
    
    def _save(self):
        """Write leaderboard to JSON file."""
        try:
            # Create saves folder if needed
            folder = os.path.dirname(LEADERBOARD_PATH)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
            
            data = {
                "entries": self.entries
            }
            
            with open(LEADERBOARD_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Error saving leaderboard: {e}")
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def register(self, name, play_time, pokemon_count, pokedex_count):
        """
        Register a new entry in the leaderboard.
        
        Args:
            name: trainer name
            play_time: total play time in seconds
            pokemon_count: total Pokemon owned (team + storage)
            pokedex_count: number of Pokemon seen
        
        Returns:
            rank obtained (1-based) or None if not in top
        """
        # Format time
        hours = int(play_time) // 3600
        minutes = (int(play_time) % 3600) // 60
        time_formatted = f"{hours:02d}h{minutes:02d}"
        
        # Create entry
        new_entry = {
            "name": name,
            "time_seconds": int(play_time),
            "time_formatted": time_formatted,
            "pokemon_count": pokemon_count,
            "pokedex_count": pokedex_count,
            "date": datetime.date.today().isoformat()
        }
        
        # Add
        self.entries.append(new_entry)
        
        # Sort
        self._sort()
        
        # Limit to MAX_ENTRIES
        if len(self.entries) > MAX_ENTRIES:
            self.entries = self.entries[:MAX_ENTRIES]
        
        # Save
        self._save()
        
        # Calculate rank
        rank = None
        for i, entry in enumerate(self.entries):
            if entry is new_entry:  # Compare by identity
                rank = i + 1
                break
        
        return rank
    
    
    def get_rankings(self, limit=None):
        """
        Return sorted entries.
        
        Args:
            limit: max number of entries to return (None = all)
        
        Returns:
            list of entry dicts
        """
        if limit is not None:
            return self.entries[:limit]
        return self.entries
    
    
    def get_best_time(self):
        """Return best time in seconds, or None if empty."""
        if not self.entries:
            return None
        return self.entries[0].get("time_seconds", None)
    
    
    def get_rank(self, time_seconds):
        """
        Return rank a given time would get without registering.
        Useful for "You would be Xth!" message.
        
        Args:
            time_seconds: time to evaluate
        
        Returns:
            int (1-based)
        """
        rank = 1
        for entry in self.entries:
            if time_seconds > entry.get("time_seconds", 0):
                rank += 1
            else:
                break
        return rank
    
    
    def would_make_top(self, time_seconds):
        """
        Check if a time would enter top MAX_ENTRIES.
        
        Args:
            time_seconds: time to check
        
        Returns:
            True if time is good enough
        """
        if len(self.entries) < MAX_ENTRIES:
            return True  # leaderboard not full
        return time_seconds < self.entries[-1].get("time_seconds", 999999)
    
    
    def clear(self):
        """Reset leaderboard (debug)."""
        self.entries = []
        self._save()
    
    
    def count(self):
        """Return number of entries."""
        return len(self.entries)