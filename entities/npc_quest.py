# =============================================================================
# NPC_QUEST.PY - QUEST NPC CLASS
# =============================================================================
#
# NPC that gives quests (challenges) to the player.

import json
from entities.npc import NPC
from config.settings import QUESTS_DATA_FILE


# =============================================================================
# QUEST NPC CLASS
# =============================================================================

class NPCQuest(NPC):
    """
    NPC that gives quests to the player.
    Behavior changes based on quest state.
    """
    
    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------
    
    def __init__(self, data, quest_data=None):
        """
        Initialize quest NPC.
        
        Args:
            data: dict from npcs.json
            quest_data: quest data dict (loaded from quests.json)
        """
        super().__init__(data)
        
        # Quest data
        self.quest_data = quest_data
        
        # If quest data not passed directly, try to load from quests.json
        if self.quest_data is None:
            self.quest_data = self._load_quest_data()
        
        # Temporary attributes for current interaction
        self._current_state = None
        self._current_progress = None
        self._game_manager_ref = None
    
    
    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------
    
    def _load_quest_data(self):
        """
        Find quest associated with this NPC in quests.json.
        Match on "npc_id" field.
        
        Returns:
            quest dict or None if not found
        """
        try:
            with open(QUESTS_DATA_FILE, "r") as f:
                all_quests = json.load(f)
            
            for quest in all_quests:
                if quest["npc_id"] == self.id:
                    return quest
        
        except Exception:
            print("Warning: Could not load quests data")
        
        return None
    
    
    def _get_quest_state(self, game_manager):
        """
        Determine current quest state for this NPC.
        
        Checks player data:
        - If quest in completed → "done"
        - If quest in active → check if completed
          - If conditions met → "complete"
          - Otherwise → "active"
        - Otherwise → "available"
        
        Returns:
            string: "available", "active", "complete", or "done"
        """
        if self.quest_data is None:
            return "done"   # no quest = nothing to do
        
        quest_id = self.quest_data["id"]
        player = game_manager.player
        
        # Already rewarded?
        if quest_id in player.quests_completed:
            return "done"
        
        # In progress?
        if quest_id in player.active_quests:
            # Check if conditions are met
            if self._check_conditions(game_manager):
                return "complete"
            return "active"
        
        # Not started yet
        return "available"
    
    
    def _check_conditions(self, game_manager):
        """
        Check if quest conditions are met.
        Delegates to specialized methods based on quest type.
        
        Returns:
            True if conditions met, False otherwise
        """
        quest_type = self.quest_data["type"]
        player = game_manager.player
        
        if quest_type == "capture_type":
            return self._check_capture_type(player)
        
        if quest_type == "level_up":
            return self._check_level_up(player)
        
        if quest_type == "defeat_trainers":
            return self._check_defeat_trainers(player)
        
        if quest_type == "exploration":
            # Exploration quests are handled by flags somewhere
            # For now, return False
            return False
        
        return False
    
    
    def _check_capture_type(self, player):
        """Check "capture X Pokemon of given type" quest."""
        target_type = self.quest_data["target_type"]
        target_count = self.quest_data["target_count"]
        
        count = 0
        
        # Count in team
        for pokemon in player.team:
            if target_type in pokemon.types:
                count += 1
        
        # Count in storage
        for pokemon in player.storage:
            if target_type in pokemon.types:
                count += 1
        
        return count >= target_count
    
    
    def _check_level_up(self, player):
        """Check "reach level X with a Pokemon" quest."""
        target_level = self.quest_data["target_level"]
        
        for pokemon in player.team:
            if pokemon.level >= target_level:
                return True
        
        return False
    
    
    def _check_defeat_trainers(self, player):
        """Check "defeat X trainers" quest."""
        target_count = self.quest_data["target_count"]
        return len(player.trainers_beaten) >= target_count
    
    
    def _get_progress(self, game_manager):
        """
        Return current quest progress as string.
        Example: "2/3" for "2 out of 3 Water Pokemon captured".
        
        Used to replace placeholders in dialogues.
        """
        quest_type = self.quest_data["type"]
        player = game_manager.player
        
        if quest_type == "capture_type":
            target_type = self.quest_data["target_type"]
            count = 0
            for pokemon in player.team:
                if target_type in pokemon.types:
                    count += 1
            for pokemon in player.storage:
                if target_type in pokemon.types:
                    count += 1
            return f"{count}/{self.quest_data['target_count']}"
        
        if quest_type == "level_up":
            max_level = 0
            for pokemon in player.team:
                if pokemon.level > max_level:
                    max_level = pokemon.level
            return f"Niv.{max_level}/{self.quest_data['target_level']}"
        
        if quest_type == "defeat_trainers":
            return f"{len(player.trainers_beaten)}/{self.quest_data['target_count']}"
        
        return "?"
    
    
    def _give_reward(self, game_manager):
        """Give quest reward to player."""
        reward = self.quest_data.get("reward", {})
        player = game_manager.player
        
        if reward["type"] == "credits":
            player.credits += reward["amount"]
            game_manager.audio_manager.play_sfx("levelup")
        
        if reward["type"] == "item":
            # Will be implemented when inventory is ready
            # player.inventory.add(reward["item_id"], reward.get("amount", 1))
            game_manager.audio_manager.play_sfx("menu_select")
    
    
    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
    
    def get_dialogue(self):
        """
        Return dialogue based on quest state.
        Needs game_manager, but get_dialogue() is called by on_interact()
        which doesn't always have game_manager.
        
        We use temporary self._current_state set at start of on_interact().
        """
        if self.quest_data is None:
            return self.dialogues.get("default", ["..."])
        
        quest_dialogues = self.quest_data.get("dialogues", {})
        
        if self._current_state == "available":
            return quest_dialogues.get("propose", ["I have a challenge for you!"])
        
        if self._current_state == "active":
            lines = quest_dialogues.get("active", ["Keep going, you're almost there!"])
            # Replace progress placeholders
            final_lines = []
            for line in lines:
                line = line.replace("{progress}", self._current_progress)
                line = line.replace("{target}", str(self.quest_data.get("target_count", "?")))
                final_lines.append(line)
            return final_lines
        
        if self._current_state == "complete":
            lines = quest_dialogues.get("complete", ["Well done, you did it!"])
            reward = self.quest_data.get("reward", {})
            reward_str = str(reward.get("amount", 0))
            final_lines = []
            for line in lines:
                final_lines.append(line.replace("{reward}", reward_str))
            return final_lines
        
        if self._current_state == "done":
            return quest_dialogues.get("done", ["You already did my challenge!"])
        
        return ["..."]
    
    
    def on_interact(self, game_manager):
        """
        Override on_interact() to calculate quest state before dialogue.
        
        Sequence:
        1. Calculate quest state
        2. Calculate progress
        3. Store in temporary attributes
        4. Call parent on_interact() (which starts dialogue)
        """
        if not self.interactive:
            return
        
        # Calculate state and progress before dialogue
        self._current_state = self._get_quest_state(game_manager)
        self._current_progress = self._get_progress(game_manager)
        self._game_manager_ref = game_manager
        
        # Call base behavior (face player + start dialogue)
        super().on_interact(game_manager)
    
    
    def on_dialogue_end(self, game_manager):
        """
        Called when dialogue ends.
        Action depends on quest state:
        
        "available" → player just heard proposal
            → Add quest to player's active quests
        
        "active" → player got progress reminder
            → Nothing special
        
        "complete" → player just saw congratulations
            → Give reward
            → Move quest from active to completed
        
        "done" → player saw post-quest dialogue
            → Nothing
        """
        if self.quest_data is None:
            return
        
        quest_id = self.quest_data["id"]
        player = game_manager.player
        
        if self._current_state == "available":
            # Activate quest
            if quest_id not in player.active_quests:
                player.active_quests.append(quest_id)
        
        if self._current_state == "complete":
            # Give reward
            self._give_reward(game_manager)
            
            # Move from active to completed
            if quest_id in player.active_quests:
                player.active_quests.remove(quest_id)
            if quest_id not in player.quests_completed:
                player.quests_completed.append(quest_id)