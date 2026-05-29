from pygame.math import Vector2
import random
if __package__:
    from ...data.constants import *
else:
    from Sobrevivencia.data.constants import *

class QuestManager:
    def _update_quests(self, dt):
        if self.quest is None:
            self.next_quest_timer -= dt
            if self.next_quest_timer <= 0:
                self._start_quest()
            return

        q = self.quest
        gt = q["goal_type"]
        q["timer"] -= dt

        # Accumulate time-based progress
        if gt == "survive_melee":
            self.quest_progress += dt
        elif gt == "stand_fire" and self._player_in_fire:
            self.quest_progress += dt
        elif gt == "survive_no_dash":
            self.quest_progress += dt

        # Check completion
        if self.quest_progress >= q["target"]:
            self._grant_quest_reward()
            return

        # Check timeout
        if q["timer"] <= 0:
            self._fail_quest()

    def _start_quest(self):
        chosen = self.random.choice(QUEST_DEFINITIONS)
        self.quest = dict(chosen)
        self.quest["timer"] = chosen["time_limit"]
        self.quest_progress = 0.0
        self.next_quest_timer = self.random.uniform(90.0, 150.0)
        self.message = f"Nova missao: {chosen['description']}"

    def _fail_quest(self):
        desc = self.quest["description"] if self.quest else ""
        self.quest = None
        self.quest_progress = 0.0
        self.next_quest_timer = self.random.uniform(60.0, 100.0)
        self.message = f"Missao falhou: {desc}"

    def _grant_quest_reward(self):
        desc = self.quest["description"] if self.quest else ""
        self.quest = None
        self.quest_progress = 0.0
        self.next_quest_timer = self.random.uniform(90.0, 150.0)
        self.completed_quick_quests = getattr(self, "completed_quick_quests", 0) + 1
        self._grant_bonus_levels(3)
        if self.completed_quick_quests >= 5:
            self.grant_chalice_fragment("quest_5", self.player.pos)
        self.message = f"Missao concluida: {desc} | +3 niveis!"
        self.screen_shake = max(self.screen_shake, 10.0)
