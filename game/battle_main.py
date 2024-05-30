from ..util import static_random as random
import sys

from app import App

from ..util.speech import SpeechDialog

from sys import implementation as _sys_implementation
if _sys_implementation.name != "micropython":
    from typing import Union

from . import constants, mons, moves, calculation, player, items


class Battle:
    def __init__(self, player1: player.Player, player2: player.Player, app: App, news_target: SpeechDialog):
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

        if self.mon1.stats[constants.STAT_SPD] == self.mon2.stats[constants.STAT_SPD]:
            self.turn = random.getrandbits(1) == 0
        else:
            self.turn = self.mon1.stats[constants.STAT_SPD] > self.mon2.stats[constants.STAT_SPD]
        self._app = app

    async def push_news_entry(self, *entry):
        await self.news_target.write(" ".join(str(e) for e in entry))

    async def use_move(self, user: mons.Mon, target: mons.Mon, move: moves.Move, custom_log: str = ""):
        """
        Use a move on a target. This is what you should call to use a move.

        :param user: User of the move.
        :param target: Target of the move.
        :param move: The move to use.
        :param custom_log: A format string. Valid format values are {user} and {move_name}.
        """
        if custom_log == "":
            custom_log = "{user} used {move_name}!\n"
        await self.push_news_entry(custom_log.format(user=user.nickname, move_name=move.name))

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
                await self.push_news_entry("A CRITITCAL Hit!\n")
            else:
                await self.push_news_entry("A Hit!\n")

            if effective == calculation.EFF_EFFECTIVE:
                await self.push_news_entry("It was really effective!\n")
            elif effective == calculation.EFF_INEFFECTIVE:
                await self.push_news_entry("It didn't really do much...\n")
            
            if move.effect_on_hit:
                await move.effect_on_hit.execute(self, user, target, damage)

            await self.deal_damage(user, target, damage, move.move_type)

        else:
            await self.push_news_entry("A Miss!\n")
            if move.effect_on_miss:
                await move.effect_on_miss.execute(self, user, target, damage)

    async def inflict_status(self, user: Union[mons.Mon, None], target: mons.Mon, status: constants.StatusEffect,
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
        await self.push_news_entry(custom_log.format(target=target, user=user, status=constants.status_to_str(status)))
        return status_taken

    async def deal_damage(self, user: Union[mons.Mon, None], target: mons.Mon, amount: int,
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
        await self.push_news_entry(custom_log.format(target=target.nickname, user=user.nickname, damage_taken=-damage_taken,
                                               dmg_type=constants.type_to_str(dmg_type), original_damage=amount))
        return damage_taken

    async def gain_exp(self, user: mons.Mon, target: mons.Mon, custom_log: str = "") -> int:
        """
        Deal damage. Default log message is "{user} gained {exp} experience!"
        :param user: The mon which caused the target to faint. This mon will gain exp.
        :param target: The mon which fainted.
        :param custom_log: A format string. Valid format values are {user}, {target}, {exp}
        :return: The amount of exp gained.
        """
        exp = calculation.get_experience(user, target)
        user.gain_exp(exp)
        if custom_log == "":
            custom_log = "{user} gained {exp} experience!\n"
        await self.push_news_entry(custom_log.format(target=target.nickname, user=user.nickname, exp=exp))
        return exp

    async def heal_target(self, user: Union[mons.Mon, None], target: mons.Mon, amount: int, custom_log: str = ""):
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
        await self.push_news_entry(custom_log.format(target=target, user=user, heal_taken=heal_taken, original_heal=amount))
        return heal_taken

    async def catch(self, user: player.Player, this_mon: mons.Mon, target: mons.Mon, ball: items.Item):
        ball_rate = ball.function_in_battle(user, self, this_mon, target)
        (base, rate) = calculation.get_catch_rate(target, ball_rate)
        if base == 1.0:
            await self.push_news_entry(f"{target.nickname} just fell straight in!")
            return True
        else:
            ooos = ["ooo...", "Oooooo... ", "OOOOOOOOO...", "Yes! You caught them!"]
            escape = "NO! They escaped!"
            caught = True
            for oo in ooos:
                if calculation.get_shake(rate):
                    await self.push_news_entry(oo)
                else:
                    await self.push_news_entry(escape)
                    caught = False
                    break
            return caught
                    
