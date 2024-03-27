import math
import random
from enum import Enum
from typing import Callable, List

import prototype.game.constants as constants
import prototype.game.battle_main as battle_main
from prototype.game import mons


move_special_callback_typ = Callable[[battle_main.Battle, mons.Mon, mons.Mon, int], bool]


class MoveOverrideSpecial(Enum):
    NO_OVERRIDE = 0


class MoveEffect:
    @staticmethod
    def apply_status_effect(status: constants.StatusEffect, chance_to_apply: float = 1):
        def function(battle: battle_main.Battle, user: mons.Mon, target: mons.Mon, damage: int):
            if random.random() < chance_to_apply:
                battle.inflict_status(user, target, status)

        return function

    @staticmethod
    def recoil_damage(pct):
        def function(battle: battle_main.Battle, user: mons.Mon, target: mons.Mon, damage: int):
            battle.deal_damage(user, target, math.floor(damage * pct), None, "from recoil")

    def __init__(self, action: move_special_callback_typ):
        self.action = action

    def _extend_with_condition(self, new_fn: move_special_callback_typ, valid_outcomes: List):
        old_fn = self.action

        def new_action(battle: battle_main.Battle, user: mons.Mon, target: mons.Mon, damage: int):
            outcome = old_fn(battle, user, target, damage)
            if outcome in valid_outcomes:
                new_fn(battle, user, target, damage)

        self.action = new_action
        return self

    def then(self, new_fn: move_special_callback_typ):
        return self._extend_with_condition(new_fn, [True, False])

    def then_if_failed(self, new_fn: move_special_callback_typ):
        return self._extend_with_condition(new_fn, [False])

    def then_if_success(self, new_fn: move_special_callback_typ):
        return self._extend_with_condition(new_fn, [True])

    def execute(self, battle: battle_main.Battle, user: mons.Mon, target: mons.Mon, damage: int):
        self.action(battle, user, target, damage)


class Move:
    def __init__(
        self, name: str, move_type: constants.MonType, max_pp: int, power: int, accuracy: int,
        effect_on_hit: MoveEffect, effect_on_miss: MoveEffect, special_override: MoveOverrideSpecial
    ):
        self.name = name
        self.move_type = move_type
        self.max_pp = max_pp
        self.power = power
        self.accuracy = accuracy
        self.effect_on_hit = effect_on_hit
        self.effect_on_miss = effect_on_miss
        self.special_override = special_override
