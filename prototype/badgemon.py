"""
WELCOME TO BADGEMON!!!!

This is where the core gameplay objects go: moves, badgemons, players, whatever. If it stores data and is part of the
game it goes in here.
"""
from random import random
from struct import pack, unpack


class EFFECTS:
    NONE = 0
    POISON = 1


class MOVE_TYPES:
    NORMAL = 0
    FIRE = 1
    BUG = 2


class Move:
    def __init__(self, name: str, move_type: int, sp_usage: int, base_damage: float, effect: int):
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

    def __init__(self, name: str, move_set: [int]):
        """


        :param name:
        :param move_set:
        """

        self.active_effect = None
        self.name = name
        self.move_set = move_set
        self.exp = 100

        self.hp = self.get_max_hp()
        self.sp = self.get_max_sp()

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

    def heal(self, amount: int):
        self.hp = min(self.get_max_hp(), self.hp + amount)

    def add_effect(self, effect: int):
        self.active_effect = effect

    def serialise(self) -> bytes:
        output = self.name.encode('utf-8')[:10]
        output += bytes(10 - len(output))
        output += pack('>HHH', self.hp, self.sp, self.exp)
        output += pack('>HHHH', *self.move_set)
        return output

    @staticmethod
    def deserialise(b: bytes) -> 'BadgeMon':
        name = b[:10].rstrip(b'\x00')
        name = name.decode('utf-8')
        hp, sp, exp = unpack('>HHH', b[10:16])
        move_set = unpack('>HHHH', b[16:24])
        badgemon = BadgeMon(name, move_set)
        badgemon.hp = hp
        badgemon.sp = sp
        badgemon.exp = exp

        return badgemon


class Player:

    def __init__(self, party: [BadgeMon]):
        self.party = party
