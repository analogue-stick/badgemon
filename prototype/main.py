"""
Main. This will be 100% prototype specific. Run it in the terminal ultra-basic stuff.
"""
import badgemon

NORMAL_TYPE = badgemon.MoveType()
NO_EFFECT = badgemon.Effect()

HIT = badgemon.Move('Hit', NORMAL_TYPE, 1, 1, NO_EFFECT)


class Game:

    def __init__(self):
        self.has_won = False

    def do_turn(self):
        pass


def main():
    game = Game()
    while game.has_won == False:
        game.do_turn()


if __name__ == '__main__':
    main()
