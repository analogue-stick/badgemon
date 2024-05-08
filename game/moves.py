import math
import random
from . import constants

try:
    from typing import Callable, List, Union, TYPE_CHECKING
    if TYPE_CHECKING:
        print('\n\n\nYes we are checking types right now\n\n\n')
        from .battle_main import Battle
        from .mons import Mon
        MoveSpecial = Callable[['Battle', 'Mon', 'Mon', int], bool]
except ImportError:
    pass

class MoveOverrideSpecial:
    """
    Any overrides that can't be expressed, even by MoveEffect.

    Example: a move that has power based on some specific stat
    """
    NO_OVERRIDE = 0


class MoveEffect:
    """
    Special effects called when moves are used, to do things aside from just dealing damage.
    Works as a nested set of functions.

    Objects can be instantiated using the MoveEffect static method (for prebuilt functions)
    or by writing a custom function with the signature:
    function(battle: battle_main.Battle, user: mons.Mon, target: mons.Mon, damage: int)

    To chain effects together (e.g. to deal 20% recoil damage then apply the BURNING status effect),
    use "then()" on a MoveEffect object.
    """
    @staticmethod
    def apply_status_effect(status: constants.StatusEffect, chance_to_apply: float = 1) -> "MoveEffect":
        """
        Applies a status effect at a specific chance. Success is if the effect is applied successfully
        (roll success AND effect successfully added)

        :param status: The status to apply to the target.
        :param chance_to_apply: The chance that status is applied.
        :return: A MoveEffect object containing this effect only.
        """
        async def function(battle: 'Battle', user: 'Mon', target: 'Mon', damage: int):
            if random.random() < chance_to_apply:
                return await battle.inflict_status(user, target, status)

            return False

        return MoveEffect(function)

    @staticmethod
    def recoil_damage(pct: float) -> "MoveEffect":
        """
        Deals self-damage equal to a percentage of the original damage (expected damage if missed)
        :param pct: The amount of damage to deal back to the user.
        :return: A MoveEffect object containing this effect only.
        """
        async def function(battle: 'Battle', user: 'Mon', target: 'Mon', damage: int):
            await battle.deal_damage(
                user, target, math.floor(damage * pct), None, "{target} took {damage_taken} recoil damage!"
            )
            return True

        return MoveEffect(function)

    def _extend_with_condition(
            self, new_fn: Union['MoveSpecial', "MoveEffect"], valid_outcomes: List) -> "MoveEffect":
        """
        Appends new_fn to this object under the condition that the previous action returned one of valid_outcomes.
        :param new_fn: The new function to add to this object. Can be MoveEffect or a bare function.
        :param valid_outcomes: A list of the valid outcomes (true or false). "Always" is [True, False].
        :return: This object.
        """
        old_fn = self.action

        new_fn_checked = new_fn
        if isinstance(new_fn, MoveEffect):
            new_fn_checked = new_fn.action

        async def new_action(battle: 'Battle', user: 'Mon', target: 'Mon', damage: int) -> bool:
            outcome = await old_fn(battle, user, target, damage)
            if outcome in valid_outcomes:
                return await new_fn_checked(battle, user, target, damage)

            return False

        self.action = new_action
        return self

    def __init__(self, action: 'MoveSpecial'):
        self.action = action

    def then(self, new_fn: Union['MoveSpecial', "MoveEffect"]):
        """
        Appends new_fn to this object so that it runs after this object's action.
        :param new_fn: The new function to add to this object. Can be MoveEffect or a bare function.
        :return: This object.
        """
        return self._extend_with_condition(new_fn, [True, False])

    def then_if_failed(self, new_fn: Union['MoveSpecial', "MoveEffect"]):
        """
        Appends new_fn to this object so that it runs after this object's action, but only if the previous action failed
         (returned false).
        :param new_fn: The new function to add to this object. Can be MoveEffect or a bare function.
        :return: This object.
        """
        return self._extend_with_condition(new_fn, [False])

    def then_if_success(self, new_fn: Union['MoveSpecial', "MoveEffect"]):
        """
        Appends new_fn to this object so that it runs after this object's action, but only if the previous action
         succeeded (returned true).
        :param new_fn: The new function to add to this object. Can be MoveEffect or a bare function.
        :return: This object.
        """
        return self._extend_with_condition(new_fn, [True])

    async def execute(self, battle: 'Battle', user: 'Mon', target: 'Mon', damage: int):
        """
        Do it. Call this when the move is used - after damage is calculated and dealt. If the move missed, still call
         this, but use the predicted damage rather than the actual damage.
        :param battle: The current battle.
        :param user: The user of the move.
        :param target: The target of the move.
        :param damage: The amount of damage the move dealt (or would have done, in the case of a miss)
        :return:
        """
        await self.action(battle, user, target, damage)


class Move:
    id_inc = 0

    def __init__(
        self, name: str, desc: str, move_type: constants.MonType, max_pp: int, power: int, accuracy: int,
        effect_on_hit: MoveEffect = None, effect_on_miss: MoveEffect = None,
            special_override: MoveOverrideSpecial = MoveOverrideSpecial.NO_OVERRIDE
    ):
        """
        Any kind of move.
        :param name: The name of the move.
        :param desc: The description of the move.
        :param move_type: The damage type of the move.
        :param max_pp: The maximum PP of the move. The move's PP is reset to this on a full heal.
        :param power: Analogous to Pokémon move power, e.g. tackle is 40 power, hyper beam is 150.
        :param accuracy: 0-100 (it's a percentage)
        :param effect_on_hit: Special effect called when the move hits.
        :param effect_on_miss: Special effect called when the move misses.
        :param special_override: Any override that a special case must be made for.
        """
        self.id = Move.id_inc
        Move.id_inc += 1

        self.name = name
        self.desc = desc
        self.move_type = move_type
        self.max_pp = max_pp
        self.power = power
        self.accuracy = accuracy
        self.effect_on_hit = effect_on_hit
        self.effect_on_miss = effect_on_miss
        self.special_override = special_override


moves_list = [
    Move('Scratch', 'Scratches opponent', constants.MonType.NORMAL, 35, 40, 100) for i in range(10)
    # Move(
    #     "Kills you", "Kills you with hammers", constants.MonType.DRAGON, 20, 999, 100,
    #     MoveEffect.recoil_damage(20).then(
    #         MoveEffect.apply_status_effect(constants.StatusEffect.BURNED, 0.3)
    #     )
    # ) for i in range(10)
]
