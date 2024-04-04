"""
Main. This will be 100% prototype specific. Run it in the terminal ultra-basic stuff.
"""
from typing import Tuple, Union

import random

from game import mons, items, moves, battle_main, player

mon_template = mons.mons_list[0]
mon1 = mons.Mon(mon_template, 5).set_nickname("small guy")
mon2 = mons.Mon(mon_template, 17).set_nickname("mr. 17")
mon3 = mons.Mon(mon_template, 17).set_nickname("David")
mon4 = mons.Mon(mon_template, 33).set_nickname("large individual")
mon5 = mons.Mon(mon_template, 100).set_nickname("biggest dude")


class User(player.Player):

    def get_move(self) -> Tuple[int, Union[mons.Mon, items.Item, moves.Move, None]]:
        print("Which move would you like to take?\n" +
              "  1. Make a move\n" +
              "  2. Use an item\n" +
              "  3. Swap mon\n" +
              "  4. Run away")
        res = input(': ')
        if res == "1":
            mon = self.battle_context.mon1
            mon_moves = mon.moves
            print("Pick a move")
            for i, m in enumerate(mon_moves):
                print(f'  {i + 1}. {m.name}')
            res = input(': ')
            return battle_main.Actions.MAKE_MOVE, mon_moves[int(res) - 1]


class Cpu(player.Player):

    def get_move(self) -> Tuple[int, Union[mons.Mon, items.Item, moves.Move, None]]:
        mon = self.battle_context.mon2
        return battle_main.Actions.MAKE_MOVE, random.choice(mon.moves)


def main():
    player_a = User('Player A', [mon1], [])
    player_b = Cpu('Tr41n0rB0T', [mon2], [])
    battle = battle_main.Battle(player_a, player_b, True)
    battle.do_battle()


if __name__ == '__main__':
    main()
