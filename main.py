"""
Main. This will be 100% prototype specific. Run it in the terminal ultra-basic stuff.
"""
try:
    from typing import List, Tuple, Union
except ImportError:
    pass

import random
from game import mons, items, moves, battle_main, player

potion = items.items_list[0]
mon_template = mons.mons_list[0]
mon1 = mons.Mon(mon_template, 5).set_nickname("small guy")
mon2 = mons.Mon(mon_template, 17).set_nickname("mr. 17")
mon3 = mons.Mon(mon_template, 17).set_nickname("David")
mon4 = mons.Mon(mon_template, 33).set_nickname("large individual")
mon5 = mons.Mon(mon_template, 100).set_nickname("biggest dude")


class User(player.Player):

    def get_move(self) -> Tuple[int, Union[mons.Mon, items.Item, moves.Move, None]]:
        res = "0"
        while res == "0":
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
                print("  0. Back")
                for i, m in enumerate(mon_moves):
                    print(f'  {i + 1}. {m.name}')
                res = input(': ')
                if res != "0":
                    return battle_main.Actions.MAKE_MOVE, mon_moves[int(res) - 1]
            elif res == "2":
                player_items: List[Tuple[int, Tuple[items.Item, int]]] = list(
                    filter(lambda i: i[1][0].usable_in_battle and i[1][1] > 0, enumerate(self.inventory)))
                print("Pick an item")
                print("  0. Back")
                for i, (_, (item, count)) in enumerate(player_items):
                    print(f'  {i + 1}. {count}x {item.name}')
                res = input(': ')
                if res != "0":
                    item_index, (item, count) = player_items[int(res) - 1]
                    count -= 1
                    self.inventory[item_index] = (item, count)  # decrease stock
                    return battle_main.Actions.USE_ITEM, item

            elif res == "3":
                player_mons: List[mons.Mon] = list(filter(lambda b: not b.fainted, self.badgemon))
                print("Pick a mon")
                print("  0. Back")
                for i, m in enumerate(player_mons):
                    print(f'  {i + 1}. {m.nickname}')
                res = input(': ')
                if res != "0":
                    return battle_main.Actions.SWAP_MON, player_mons[int(res) - 1]

            elif res == "4":
                print("Are you sure you want to run away?")
                print("  0. No")
                print("  1. Yes")
                res = input(': ')
                if res != "0":
                    return battle_main.Actions.RUN_AWAY, None

            else:
                res = "0"


class Cpu(player.Player):

    def get_move(self) -> Tuple[int, Union[mons.Mon, items.Item, moves.Move, None]]:
        mon = self.battle_context.mon2
        return battle_main.Actions.MAKE_MOVE, random.choice(mon.moves)


def main():
    print("[SHOW PROF]")
    print("Hello there! Welcome to the world of BADGEMON! My name is Acorn R. Machine. People call me the BADGEMON PROF!")
    print("[SHOW BADGEMON]")
    print("This field in the middle of England is inhabited by creatures called BADGEMON! For some people, BADGEMON are pets. Others consider them \"a nuisance\" and \"not covered by the insurance\". Myself... I study BADGEMON as a profession.")
    print("[SHOW YOU]")
    print("First, what is your name?")
    player_name = input(":")
    if len(player_name) > 12:
        player_name = player_name[0:12]
    if player_name == "":
        player_name = "SCARLETT"
    print(f"Right! So your name is {player_name}!")
    print("[SHOW GRANDSON]")
    print("This is my grandson. He's unrelated to the BADGEMON, I just wanted to show you his picture. Isn't he the best? I'm very proud of him.")
    print("[SHOW YOU]")
    print(f"{player_name}! Your very own BADGEMON legend is about to unfold! A whole field of dreams and adventures and tents and seminars with BADGEMON awaits! Let's go!")
    player_a = User(player_name, [mon2], [(potion, 1)])
    player_b = Cpu('Tr41n0rB0T', [mon1], [])
    battle = battle_main.Battle(player_a, player_b, True)
    victor = battle.do_battle()
    print(f"{victor.name} WINS!")


if __name__ == '__main__':
    main()
