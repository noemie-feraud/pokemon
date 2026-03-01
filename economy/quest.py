# =============================================================================
# QUEST.PY - QUEST SYSTEM
# =============================================================================
#
# Centralized quest system.
# Loads quests from quests.json, tracks state, checks conditions, gives rewards.

import json
from config.settings import QUESTS_DATA_FILE


# =============================================================================
# QUEST MANAGER CLASS
# =============================================================================

class QuestManager:
    """
    Central quest system.
    Loads quest data, checks conditions, gives rewards.
    Stateless — quest state is stored in Player.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self):
        """Load all quests from quests.json."""
        self.quests = {}  # {quest_id: quest_data}
        
        try:
            with open(QUESTS_DATA_FILE, "r") as f:
                quests_data = json.load(f)
            
            for quest in quests_data:
                self.quests[quest["id"]] = quest
        
        except Exception:
            print("Warning: Could not load quests data")
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS - GETTERS
    # -------------------------------------------------------------------------
    
    def get_quest(self, quest_id):
        """Return quest data by ID, or None if not found."""
        return self.quests.get(quest_id, None)
    
    
    def get_quest_by_npc(self, npc_id):
        """Return quest associated with an NPC by npc_id."""
        for quest in self.quests.values():
            if quest["npc_id"] == npc_id:
                return quest
        return None
    
    
    def get_state(self, quest_id, player):
        """
        Determine current state of a quest for a player.
        
        Checks player's lists:
        - quests_completed → "done"
        - quests_active + conditions met → "complete"
        - quests_active + conditions not met → "active"
        - neither → "available"
        
        Args:
            quest_id: quest ID
            player: Player object
        
        Returns:
            string: "available", "active", "complete", or "done"
        """
        if quest_id not in self.quests:
            return "done"  # unknown quest = nothing to do
        
        # Already rewarded?
        if quest_id in player.quests_completed:
            return "done"
        
        # In progress?
        if quest_id in player.active_quests:
            if self.check_conditions(quest_id, player):
                return "complete"
            return "active"
        
        # Not started
        return "available"
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS - ACTIONS
    # -------------------------------------------------------------------------
    
    def activate(self, quest_id, player):
        """
        Activate a quest for player (available → active).
        
        Args:
            quest_id: quest ID
            player: Player object
        
        Returns:
            True if activation succeeded, False otherwise
        """
        if quest_id not in self.quests:
            return False
        
        if quest_id in player.active_quests:
            return False  # already active
        
        if quest_id in player.quests_completed:
            return False  # already done
        
        player.active_quests.append(quest_id)
        return True
    
    
    def check_conditions(self, quest_id, player):
        """
        Check if quest conditions are met.
        
        Args:
            quest_id: quest ID
            player: Player object
        
        Returns:
            True if conditions met, False otherwise
        """
        quest = self.quests.get(quest_id, None)
        
        if quest is None:
            return False
        
        quest_type = quest["type"]
        
        if quest_type == "capture_type":
            return self._check_capture_type(quest, player)
        
        if quest_type == "level_up":
            return self._check_level_up(quest, player)
        
        if quest_type == "defeat_trainers":
            return self._check_defeat_trainers(quest, player)
        
        if quest_type == "exploration":
            return self._check_exploration(quest, player)
        
        return False
    
    
    def give_reward(self, quest_id, player, audio_manager=None):
        """
        Give quest reward to player.
        Moves quest from active to completed.
        
        Args:
            quest_id: quest ID
            player: Player object
            audio_manager: for reward sound (optional)
        
        Returns:
            dict: {
                "success": bool,
                "reward_type": "credits" or "item",
                "reward_amount": int,
                "failure_reason": str or None
            }
        """
        quest = self.quests.get(quest_id, None)
        
        if quest is None:
            return {
                "success": False,
                "reward_type": None,
                "reward_amount": 0,
                "failure_reason": "unknown_quest"
            }
        
        # Check state
        state = self.get_state(quest_id, player)
        
        if state != "complete":
            return {
                "success": False,
                "reward_type": None,
                "reward_amount": 0,
                "failure_reason": "not_complete"
            }
        
        # Get reward info
        reward = quest.get("reward", {})
        reward_type = reward.get("type", "credits")
        reward_amount = reward.get("amount", 0)
        
        # Give reward
        if reward_type == "credits":
            player.credits += reward_amount
        
        if reward_type == "item":
            item_id = reward.get("item_id")
            if item_id is not None:
                player.inventory.add(item_id, reward_amount)
        
        # Play sound
        if audio_manager is not None:
            audio_manager.play_sfx("levelup")
        
        # Update state
        if quest_id in player.active_quests:
            player.active_quests.remove(quest_id)
        
        if quest_id not in player.quests_completed:
            player.quests_completed.append(quest_id)
        
        return {
            "success": True,
            "reward_type": reward_type,
            "reward_amount": reward_amount,
            "failure_reason": None
        }
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS - PROGRESSION
    # -------------------------------------------------------------------------
    
    def get_progress(self, quest_id, player):
        """
        Return current quest progress as string.
        
        Examples:
            capture_type → "2/3"
            level_up → "Niv.15/20"
            defeat_trainers → "4/5"
        
        Args:
            quest_id: quest ID
            player: Player object
        
        Returns:
            progress string
        """
        quest = self.quests.get(quest_id, None)
        
        if quest is None:
            return "?"
        
        quest_type = quest["type"]
        
        if quest_type == "capture_type":
            target_type = quest["target_type"]
            count = 0
            for pokemon in player.team:
                if target_type in pokemon.types:
                    count += 1
            for pokemon in player.storage:
                if target_type in pokemon.types:
                    count += 1
            return f"{count}/{quest['target_count']}"
        
        if quest_type == "level_up":
            max_level = 0
            for pokemon in player.team:
                if pokemon.level > max_level:
                    max_level = pokemon.level
            return f"Niv.{max_level}/{quest['target_level']}"
        
        if quest_type == "defeat_trainers":
            return f"{len(player.trainers_beaten)}/{quest['target_count']}"
        
        if quest_type == "exploration":
            return "In progress..."
        
        return "?"
    
    
    def get_dialogues(self, quest_id, state, player):
        """
        Return quest dialogues for a given state.
        Replaces placeholders ({progress}, {target}, {reward}) with actual values.
        
        Args:
            quest_id: quest ID
            state: "available", "active", "complete", or "done"
            player: Player object
        
        Returns:
            list of dialogue lines
        """
        quest = self.quests.get(quest_id, None)
        
        if quest is None:
            return ["..."]
        
        dialogues = quest.get("dialogues", {})
        
        # Choose dialogue set based on state
        if state == "available":
            lines = dialogues.get("propose", ["I have a challenge for you!"])
        
        elif state == "active":
            lines = dialogues.get("active", ["Keep going, you're almost there!"])
        
        elif state == "complete":
            lines = dialogues.get("complete", ["Well done, you did it!"])
        
        elif state == "done":
            lines = dialogues.get("done", ["You already did my challenge!"])
        
        else:
            lines = ["..."]
        
        # Replace placeholders
        progress = self.get_progress(quest_id, player)
        target = str(quest.get("target_count", quest.get("target_level", "?")))
        reward_amount = str(quest.get("reward", {}).get("amount", 0))
        
        final_lines = []
        for line in lines:
            line = line.replace("{progress}", progress)
            line = line.replace("{target}", target)
            line = line.replace("{reward}", reward_amount)
            final_lines.append(line)
        
        return final_lines
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS - LISTS
    # -------------------------------------------------------------------------
    
    def get_all_quests(self):
        """Return all quests."""
        return list(self.quests.values())
    
    
    def get_active_quests(self, player):
        """Return quests currently active for player."""
        active = []
        for quest_id in player.active_quests:
            quest = self.quests.get(quest_id, None)
            if quest is not None:
                active.append(quest)
        return active
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS - CONDITION CHECKS
    # -------------------------------------------------------------------------
    
    def _check_capture_type(self, quest, player):
        """Check "capture X Pokemon of given type" quest."""
        target_type = quest["target_type"]
        target_count = quest["target_count"]
        
        count = 0
        
        for pokemon in player.team:
            if target_type in pokemon.types:
                count += 1
        
        for pokemon in player.storage:
            if target_type in pokemon.types:
                count += 1
        
        return count >= target_count
    
    
    def _check_level_up(self, quest, player):
        """Check "reach level X with a Pokemon" quest."""
        target_level = quest["target_level"]
        
        for pokemon in player.team:
            if pokemon.level >= target_level:
                return True
        
        return False
    
    
    def _check_defeat_trainers(self, quest, player):
        """Check "defeat X trainers" quest."""
        target_count = quest["target_count"]
        return len(player.trainers_beaten) >= target_count
    
    
    def _check_exploration(self, quest, player):
        """Check "find hidden object" or "visit location" quest."""
        flag_id = quest.get("flag_id", None)
        
        if flag_id is None:
            return False
        
        # Simplified: check if flag is in active_quests
        # In real implementation, would have player.exploration_flags list
        return flag_id in player.active_quests
    
    
    # -------------------------------------------------------------------------
    # SPECIAL METHODS
    # -------------------------------------------------------------------------
    
    def __str__(self):
        return f"QuestManager ({len(self.quests)} quests loaded)"