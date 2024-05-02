from io import StringIO
import sys

try:
    from typing import Union
except ImportError:
    pass

from ..game import constants, mons, moves, calculation, player


class Actions:
    MAKE_MOVE = 0
    USE_ITEM = 1
    SWAP_MON = 2
    RUN_AWAY = 3


class Battle:
    def __init__(self, player1: player.Player, player2: player.Player, start: bool, news_target: StringIO = None):
        """
        A battle takes place between two players, until all BadgeMon on one side have fainted.

        @param player1: The beloved hero!
        @param player2: The cruel enemy!
        @param start: Does player1 start
        @param news_target: Output for all log messages
        """

        self.player1 = player1
        self.player2 = player2

        # We assume the first mon is in position 0
        self.mon1 = player1.badgemon[0]
        self.mon2 = player2.badgemon[0]

        if news_target:
            self.news_target = news_target
        else:
            self.news_target = sys.stdout

        player1.battle_context = self
        player2.battle_context = self

        self.turn = start

    def push_news_entry(self, *entry):
        self.news_target.write(" ".join(str(e) for e in entry))

    def use_move(self, user: mons.Mon, target: mons.Mon, move: moves.Move, custom_log: str = ""):
        """
        Use a move on a target. This is what you should call to use a move.

        :param user: User of the move.
        :param target: Target of the move.
        :param move: The move to use.
        :param custom_log: A format string. Valid format values are {user} and {move_name}.
        """
        if custom_log == "":
            custom_log = "{user} used {move_name}!\n"
        self.push_news_entry(custom_log.format(user=user.nickname, move_name=move.name))

        if move.special_override == moves.MoveOverrideSpecial.NO_OVERRIDE:
            (damage, crit, effective) = calculation.calculate_damage(
                user.level, move.power, user.stats[constants.STAT_ATK], target.stats[constants.STAT_DEF], move.move_type,
                user.template.type1, user.template.type2, target.template.type1, target.template.type2)
        else:
            (damage, crit, effective) = calculation.calculate_damage(
                user.level, move.power, user.stats[constants.STAT_SPATK], target.stats[constants.STAT_SPDEF],
                move.move_type, user.template.type1, user.template.type2, target.template.type1, target.template.type2)

        if calculation.get_hit(move.accuracy, user.accuracy, target.evasion):
            if crit:
                self.push_news_entry("A CRITITCAL Hit!\n")
            else:
                self.push_news_entry("A Hit!\n")

            if effective == calculation.EFF_EFFECTIVE:
                self.push_news_entry("It was really effective!\n")
            elif effective == calculation.EFF_INEFFECTIVE:
                self.push_news_entry("It didn't really do much...\n")
            
            self.deal_damage(user, target, damage, move.move_type)

            if move.effect_on_hit:
                move.effect_on_hit.execute(self, user, target, damage)
        else:
            self.push_news_entry("A Miss!\n")
            if move.effect_on_miss:
                move.effect_on_miss.execute(self, user, target, damage)

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
            custom_log = "{target} was inflicted with the {status} condition!\n"
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
            custom_log = "{target} took {damage_taken} damage!\n"
        self.push_news_entry(custom_log.format(target=target.nickname, user=user.nickname, damage_taken=-damage_taken,
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
            custom_log = "{target} regained {heal_taken} HP!\n"
        self.push_news_entry(custom_log.format(target=target, user=user, heal_taken=heal_taken, original_heal=amount))
        return heal_taken

    def do_battle(self) -> player.Player:
        """
        The stupid function.

        @return: The victor
        """
        while True:
            print(f"({self.mon1}) VS ({self.mon2})")
            if self.turn:
                curr_player, curr_target = self.player1, self.player2
                player_mon, target_mon = self.mon1, self.mon2
            else:
                curr_player, curr_target = self.player2, self.player1
                player_mon, target_mon = self.mon2, self.mon1

            all_fainted = True
            for mon in curr_player.badgemon:
                all_fainted = all_fainted and mon.fainted
            if all_fainted:
                return curr_target

            action, arg = curr_player.get_move()

            if action == Actions.MAKE_MOVE:
                self.use_move(player_mon, target_mon, arg)

            elif action == Actions.RUN_AWAY:
                return curr_target

            elif action == Actions.SWAP_MON:
                if self.turn:
                    self.mon1 = arg
                else:
                    self.mon2 = arg

            elif action == Actions.USE_ITEM:
                arg.function_in_battle(curr_player, self, player_mon, target_mon)

            self.turn = not self.turn
