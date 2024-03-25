"""
WELCOME TO BADGEMON!!!!

This is where the core gameplay objects go: moves, badgemons, players, whatever. If it stores data and is part of the
game it goes in here.
"""
from random import random
from typing import Callable


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
    STR_SCALE = .3

    def __init__(self, name: str, move_set: [Move], death_handler: 'Callable'):
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
        self.death_handler = death_handler

    def do_move(self, move_id: int, target: 'BadgeMon') -> bool:
        action: Move = self.move_set[move_id]

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
            self.death_handler()

    def heal(self, amount: int):
        self.hp = min(self.get_max_hp(), self.hp + amount)

    def add_effect(self, effect: Effect):
        self.active_effect = effect


class Player:

    def __init__(self, party: [BadgeMon]):
        self.party = party
