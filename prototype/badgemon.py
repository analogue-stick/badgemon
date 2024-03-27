"""
WELCOME TO BADGEMON!!!!

This is where the core gameplay objects go: moves, badgemons, players, whatever. If it stores data and is part of the
game it goes in here.
"""
from random import random, choice
from struct import pack, unpack
from typing import List


class Effects:
    NONE = 0
    POISON = 1


class MoveTypes:
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


class Moves:
    HIT = 0

    MOVES_ID = [
        Move('Hit', MoveTypes.NORMAL, 1, 1, Effects.NONE)
    ]


class BadgeMon:
    SERIALISED_LENGTH = 24

    HP_SCALE = 0.5
    SP_SCALE = 0.3
    STR_SCALE = .03

    def __init__(self, name: str, move_set: List[int]):
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
        action: Move = Moves.MOVES_ID[move_id]
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
        move_set = list(unpack('>HHHH', b[16:24]))
        badgemon = BadgeMon(name, move_set)
        badgemon.hp = hp
        badgemon.sp = sp
        badgemon.exp = exp

        return badgemon

    def is_down(self) -> bool:
        return self.hp < 0

    def list_moves(self):
        names = []
        for move in self.move_set:
            name = Moves.MOVES_ID[move].name
            names.append(name)
        return names

    def dump_stats(self):
        print(f'[*] Mon: {self.name} | HP: {self.hp} | SP: {self.sp}')


class Player:

    def __init__(self, name: str, party: List[BadgeMon]):
        self.name = name
        self.party = party

    def make_move(self, mon: BadgeMon, target: BadgeMon):
        pass

    def serialise(self):
        packet = pack('>10s', self.name)
        for mon in self.party:
            packet += mon.serialise()
        return packet

    @staticmethod
    def deserialise(b: bytes):
        name, = unpack('>10s', b[:10])
        name = name.strip(b'\x00').decode('utf-8')

        mons = []
        for i in range(10, len(b), BadgeMon.SERIALISED_LENGTH):
            mon = BadgeMon.deserialise(b[i:i + BadgeMon.SERIALISED_LENGTH])
            mons.append(mon)

        return Player(name, mons)


class Cpu(Player):

    def make_move(self, mon: BadgeMon, target: BadgeMon):
        move = choice(mon.move_set)
        print(f'[*] CPU used {Moves.MOVES_ID[move].name}')
        mon.do_move(move, target)


class Battle:

    def __init__(self, a_player, b_player):
        self.a_player = a_player
        self.b_player = b_player
        self.a_mon = a_player.party[0]
        self.b_mon = b_player.party[0]

        self.turn = True

    def do_battle(self):
        while not self.a_mon.is_down() and not self.b_mon.is_down():
            self.a_mon.dump_stats()
            self.b_mon.dump_stats()
            if self.turn:
                print(f"[*] Now it's {self.a_player.name}'s turn")
                self.a_player.make_move(self.a_mon, self.b_mon)
            else:
                print(f"[*] Now it's {self.b_player.name}'s turn")
                self.b_player.make_move(self.b_mon, self.a_mon)
            self.turn = not self.turn
        print("battle over")
