from io import StringIO
from typing import Union
import sys

from game import constants, mons, moves


# TODO battle is currently just method stubs, should be self-explanatory how it should work.
#  i'll get to it at some point. generally just call the related function on the target mon
#  and build a news entry
class Battle:
    def __init__(self, mon1: mons.Mon, mon2: mons.Mon, news_target: StringIO = None):
        self.mon1 = mon1
        self.mon2 = mon2

        if news_target:
            self.news_target = news_target
        else:
            self.news_target = sys.stdout

    def push_news_entry(self, *entry):
        self.news_target.write(" ".join(str(e) for e in entry))

    def use_move(self, user: mons.Mon, target: mons.Mon, move: moves.Move):
        """
        Use a move on a target. This is what you should call to use a move.

        :param user: User of the move.
        :param target: Target of the move.
        :param move: The move to use.
        """
        pass

    def inflict_status(self, user: Union[mons.Mon, None], target: mons.Mon, status: constants.StatusEffect,
                       custom_log: str = "") -> bool:
        """
        Apply a status effect. Default log message is "{target} was inflicted with the {status} condition!"
        :param user: The source of the damage. If the damage was self-inflicted, user is also the target.
         If the damage was from an external source, it is None.
        :param target: The target for the damage.
        :param status: The status to inflict.
        :param custom_log: A format string. Valid format values are {user}, {target}, {status}.
        :return: Whether the status was successfully applied.
        """
        pass

    def deal_damage(self, user: Union[mons.Mon, None], target: mons.Mon, amount: int,
                    dmg_type: Union[constants.MonType, None], custom_log: str = "") -> int:
        """
        Deal damage. Default log message is "{target} took {damage_taken} damage!",
         or "There was no effect." if damage_taken==0.
        :param user: The source of the damage. If the damage was self-inflicted, user is also the target.
         If the damage was from an external source, it is None.
        :param target: The target for the damage.
        :param amount: The amount of damage, before modifications.
        :param dmg_type: The damage type. If None, it is untyped damage which is unaffected by other effects and
         dealt directly.
        :param custom_log: A format string. Valid format values are {user}, {target}, {original_damage},
         {damage_taken}, {dmg_type}.
        :return: The amount of damage taken.
        """
        pass

    def heal_target(self, user: Union[mons.Mon, None], target: mons.Mon, amount: int, custom_log: str = ""):
        """
        Heal some HP. Default log message is "{target} regained {heal_taken} HP!",
         or "There was no effect." if heal_taken==0.
        :param user: The source of the damage. If the damage was self-inflicted, user is also the target.
         If the damage was from an external source, it is None.
        :param target: The target for the damage.
        :param amount: The amount of damage, before modifications.
        :param custom_log: A format string. Valid format values are {user}, {target}, {original_heal},
         {heal_taken}, {dmg_type}. original_heal is "amount" in this function,
         heal_taken is the amount of HP actually gained.
        :return: The amount of damage taken.
        """
        pass
