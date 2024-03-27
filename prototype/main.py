"""
Main. This will be 100% prototype specific. Run it in the terminal ultra-basic stuff.
"""
from badgemon import Player, BadgeMon, Moves, Battle, Cpu
from choice import make_choice

LILGUY = BadgeMon("Lil guy", [Moves.HIT])
BIGGUY = BadgeMon("Big guy", [Moves.HIT])


class User(Player):

    def make_move(self, mon: BadgeMon, target: BadgeMon):
        i = 0
        moves = mon.list_moves()
        move_choices = []
        for x, move in enumerate(moves):
            move_choices.append((move, x+10))
        while i == 0:
            i = make_choice("[*] What would you like to do?", [("attack",move_choices),("run away",2),("use an item",3)])
        if i >= 10 and i < 20:
            mon.do_move(i-10, target)

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
