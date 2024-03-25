"""
WELCOME TO BADGEMON!!!!

This is where the core gameplay objects go: moves, badgemons, players, whatever. If it stores data and is part of the
game it goes in here.
"""
from random import random
from typing import Callable, List


class Effect:

    def __init__(self):
        pass


class MoveType:
    def __init__(self):
        pass


class Move:
    def __init__(self, name: str, move_type: MoveType, sp_usage: int, base_damage: float, effect: Effect):
        """
        This is the class to hold a specific move.

        :param sp_usage:
        :param base_damage:
        :param effect:
        :param move_type:
        :param name:
        """
        self.name = name
        self.move_type = move_type
        self.base_damage = base_damage
        self.sp_usage = sp_usage
        self.effect = effect


class BadgeMon:
    HP_SCALE = 0.5
    SP_SCALE = 0.3
    STR_SCALE = .03

    def __init__(self, name: str, move_set: List[Move]):
        """


        :param name:
        :param move_set:
        :param death_handler:
        """

        self.active_effect = None
        self.name = name
        self.move_set = move_set
        self.exp = 100

        self.hp = self.get_max_hp()
        self.sp = self.get_max_sp()

    def do_move(self, move_id: int, target: 'BadgeMon') -> bool:
        action: Move = self.move_set[move_id]
        print("making move:", action.name)

        if action.sp_usage > self.sp:
            return False

        # Calculate and do damage
        damage = action.base_damage * (self.exp * BadgeMon.STR_SCALE)
        target.do_damage(damage)

        # Add effect under some condition
        if random() > 0.67:
            target.add_effect(action.effect)

        # Use up SP
        self.sp -= action.sp_usage

        return True

    def level_up(self, exp: int):
        self.exp += exp

    def get_max_hp(self):
        return self.exp // 10

    def get_max_sp(self):
        return int(self.exp / 2.0)

    def do_damage(self, damage: float):
        self.hp -= int(damage)
        if self.hp <= 0:
            print("ded")

    def heal(self, amount: int):
        self.hp = min(self.get_max_hp(), self.hp + amount)

    def add_effect(self, effect: Effect):
        self.active_effect = effect

    def is_down(self) -> bool:
        return self.hp < 0
    
    def list_moves(self):
        for move in self.move_set:
            print(move.name)

    def dump_stats(self):
        print("BADGEMON:", self.name)
        print("HP:", self.hp, "SP:", self.sp)
        print("EXP:", self.exp)

class Player:

    def __init__(self, party: List[BadgeMon]):
        self.party = party

    def make_move(mon: BadgeMon):
        pass

class User(Player):

    def make_move(self, mon: BadgeMon, target: BadgeMon):
        print("MAKE MOVE:")
        i = input()
        if i == "attack":
            mon.list_moves()
            i = input()
            for x, move in enumerate(mon.move_set):
                if move.name == i:
                    mon.do_move(x, target)


class Battle():
    a_mon: BadgeMon
    b_mon: BadgeMon
    a_player: Player
    b_player: Player
    turn: bool = True

    def __init__(self, a_player, b_player):
        self.a_player = a_player
        self.b_player = b_player
        self.a_mon = a_player.party[0]
        self.b_mon = b_player.party[0]

    def do_battle(self):
        while (not self.a_mon.is_down() and not self.b_mon.is_down()):
            self.a_mon.dump_stats()
            self.b_mon.dump_stats()
            if self.turn:
                print("A's Turn")
                self.a_player.make_move(self.a_mon, self.b_mon)
            else:
                print("B's Turn")
                self.b_player.make_move(self.b_mon, self.a_mon)
            self.turn = not self.turn
        print("battle over")