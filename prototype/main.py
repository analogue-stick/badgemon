"""
Main. This will be 100% prototype specific. Run it in the terminal ultra-basic stuff.
"""
from badgemon import Player, BadgeMon, Moves, Battle, Cpu

LILGUY = BadgeMon("Lil guy", [Moves.HIT])
BIGGUY = BadgeMon("Big guy", [Moves.HIT])


class User(Player):

    def make_move(self, mon: BadgeMon, target: BadgeMon):
        i = input("[*] What would you like to do?\n- (a)ttack\n- (r)un away\n- (u)se an item\n: ")
        if i == 'a':
            moves = mon.list_moves()
            pretty_print = '\n- ' + '\n- '.join(moves)
            i = input(f"[*] Your available moves are:{pretty_print}\n: ")
            for move in mon.move_set:
                name = Moves.MOVES_ID[move].name
                print(name)
                if name == i:
                    mon.do_move(move, target)


class Game:

    def __init__(self):
        self.has_won = False

    def do_turn(self):
        pass


def main():
    player_a = User('Player A', [LILGUY])
    player_b = Cpu('Tr41n0rB0T', [BIGGUY])
    battle = Battle(player_a, player_b)
    battle.do_battle()


if __name__ == '__main__':
    main()
