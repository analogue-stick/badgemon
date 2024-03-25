"""
Main. This will be 100% prototype specific. Run it in the terminal ultra-basic stuff.
"""
import badgemon

NORMAL_TYPE = badgemon.MoveType()
NO_EFFECT = badgemon.Effect()

HIT = badgemon.Move('Hit', NORMAL_TYPE, 1, 1, NO_EFFECT)

LILGUY = badgemon.BadgeMon("Lil guy", [HIT])
BIGGUY = badgemon.BadgeMon("Big guy", [HIT])

class Game:

    def __init__(self):
        self.has_won = False

    def do_turn(self):
        pass


def main():
    player_a = badgemon.User([LILGUY])
    player_b = badgemon.User([BIGGUY])
    battle = badgemon.Battle(player_a, player_b)
    battle.do_battle()

if __name__ == '__main__':
    main()
