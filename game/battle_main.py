from io import StringIO
from typing import Union
import sys

from game import constants, mons, moves, calculation


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
        damage = calculation.calculate_damage(
            user.level, move.power, user.stats[constants.STAT_ATK], target.stats[constants.STAT_DEF], move.move_type,
            user.template.type1, user.template.type2, target.template.type1, target.template.type2)

        if calculation.get_hit(move.accuracy):
            self.deal_damage(user, target, damage, move.move_type)
            move.effect_on_hit.execute(self, user, target, damage)
        else:
            move.effect_on_miss.execute(self, user, target, damage)

        if move.special_override != constants.MoveOverrideSpecial.NO_OVERRIDE:
            # TODO Handle special moves
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
        status_taken = target.apply_status(status)
        if custom_log == "":
            custom_log = "{target} was inflicted with the {status} condition!"
        self.push_news_entry(custom_log.format(target=target, user=user, status=constants.status_to_str(status)))
        return status_taken

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
        damage_taken = target.take_damage(amount, dmg_type)
        if custom_log == "":
            custom_log = "{target} took {damage_taken} damage!"
        self.push_news_entry(custom_log.format(target=target, user=user, damage_taken=damage_taken,
                                               dmg_type=constants.type_to_str(dmg_type), original_damage=amount))
        return damage_taken

    def heal_target(self, user: Union[mons.Mon, None], target: mons.Mon, amount: int, custom_log: str = ""):
        """
        Heal some HP. Default log message is "{target} regained {heal_taken} HP!",
         or "There was no effect." if heal_taken==0.
        :param user: The source of the damage. If the damage was self-inflicted, user is also the target.
         If the damage was from an external source, it is None.
        :param target: The target for the damage.
        :param amount: The amount of damage, before modifications.
        :param custom_log: A format string. Valid format values are {user}, {target}, {original_heal},
         {heal_taken}. original_heal is "amount" in this function,
         heal_taken is the amount of HP actually gained.
        :return: The amount of damage taken.
        """
        heal_taken = target.take_heal(amount)
        if custom_log == "":
            custom_log = "{target} regained {heal_taken} HP!"
        self.push_news_entry(custom_log.format(target=target, user=user, heal_taken=heal_taken, original_heal=amount))
        return heal_taken
