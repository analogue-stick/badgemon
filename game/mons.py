import math
import random
from struct import pack, unpack_from

from sys import implementation as _sys_implementation
if _sys_implementation.name != "micropython":
    from typing import List, Tuple, Union

from . import moves, constants


class MonTemplate:
    """
    A template for a mon. This is copied into every instance of a mon, but NEVER MODIFIED.
    """
    id_inc = 0

    def __init__(self, name: str, desc: str, type1: constants.MonType, type2: constants.MonType,
                 evolve_mon: Union['MonTemplate', None], evolve_level: Union[int, None],
                 base_hp: int, base_atk: int, base_def: int,
                 base_spatk: int, base_spdef: int, base_spd: int,
                 learnset: List[Tuple[moves.Move, int]],
                 sprite: int,
                 weight: int,
                 catch_rate: int = 1, base_exp = 150):
        """
        :param name: Name of the mon
        :param desc: Description (dex entry)
        :param type1: First type, e.g. Fire, Ground
        :param type2: Second type, e.g. Fire, Ground
        :param evolve_mon: The mon this will evolve into. Will not evolve if this is None.
        :param evolve_level: The level at which this mon evolves. Will not evolve if this is None.
        :param base_hp: Base HP (in the pokemon terms)
        :param base_atk: Base ATK
        :param base_def: Base DEF
        :param base_spatk: Base Special ATK
        :param base_spdef: Base Special DEF
        :param base_spd: Base SPD
        :param learnset: The moves this mon learns. At each specified level,
        the mon tries to learn the move. Must be sorted from low to high, e.g. [[Move1, 2], [Move2, 10], ...]
        :param sprite: The sprite index to use for this mon, E.G. mon-X.png
        :param weight: How likely the mon will appear randomly. Higher numbers will make the mon appear more.
        It is weighted against every other mon (so if one weight increases, the likelyhood of all other mons
        appearing decreases), and should be an integer.
        :param catch_rate: How easy this mon is to catch. 1 is normal, higher numbers make it easier
        :param base_exp: The average amount of exp gained when this mon gains exp
        """
        self.id = MonTemplate.id_inc
        MonTemplate.id_inc += 1

        self.name = name
        self.desc = desc
        self.type1 = type1
        self.type2 = type2
        self.evolve_mon = evolve_mon
        self.evolve_level = evolve_level
        self.base_hp = base_hp
        self.base_atk = base_atk
        self.base_def = base_def
        self.base_spatk = base_spatk
        self.base_spdef = base_spdef
        self.base_spd = base_spd

        self.base_stats = [
            base_hp, base_atk, base_def, base_spatk, base_spdef, base_spd
        ]

        self.learnset = learnset

        self.sprite = sprite

        self.weight = weight
        self.catch_rate = catch_rate
        self.base_exp = base_exp

class Mon:
    """
    The dynamic form of a mon. This is the one used in battles and everywhere else.

    Don't call functions on this directly if currently in battle - use the Battle object instead.
    """

    def __init__(self, template: MonTemplate, level: int,
                 ivs: Union[List[int], None] = None,
                 evs: Union[List[int], None] = None,
                 set_moves: Union[List[moves.Move]] = None):
        """
        :param template: The mon template to use.
        :param level: The level of the mon. This determines stats and moves.
        :param ivs: The mon's IVs, as a list of 6 ints.
        If not specified, randomly selected between 0 and 31 (inclusive), e.g. [2,9,10,0,31,7].
        :param evs: The mon's EVs, as a list of 6 ints.
        This is bounded between 0 and 255 (inclusive), with an ingame limit of 510 - e.g. [2,9,10,0,31,7].
        All new mons (wild, hatched, distributed, whatever) have 0 EVs. Edit this for custom battles, mostly.
        :param set_moves: Any set moves. This will override the usual wild mon move selection.
        """

        self.template = template

        self.nickname = template.name
        self.level = level

        #            hp    atk   def  spatk spdef  spd
        self.stats = [0,    0,    0,    0,    0,    0]

        self.evs = evs if evs else [0, 0, 0, 0, 0, 0]
        self.ivs = ivs if ivs else [random.randint(0, 31) for _ in range(6)]

        self.calculate_stats()

        self.hp = self.stats[0]
        self.fainted = False

        self.accuracy = 100
        self.evasion = 100

        self.status = constants.StatusEffect.NO_EFFECT

        self.xp = level*level*level

        self.pp = [0, 0, 0, 0]

        self.moves = []  # type: List[moves.Move]

        if set_moves:
            self.moves = set_moves
        else:
            self.setup_moves_at_level()

        self.full_heal()

    def __repr__(self):
        return f'{self.nickname}, HP: {self.hp}'

    def serialise(self) -> bytes:
        """
        Transform the mon into serialised data. Opposite of Mon.deserialise().

        :return: The serialised data
        """

        # 🌏 🧑‍🚀 "Wait it's all unsigned bytes?"
        # 🧑‍🚀 🔫 🧑‍🚀 "Always has been"
        # (oh except for the name, fainted, and xp)

        data = bytearray()

        name_len = len(self.nickname)
        data += pack('B', name_len)
        data += self.nickname.encode('utf-8')

        data += pack('BBB?', self.template.id, self.level, self.hp, self.fainted)

        data += pack('BBBBBB', *self.evs)
        data += pack('BBBBBB', *self.ivs)

        data += pack('B', len(self.moves))

        for move, pp in zip(self.moves, self.pp):
            data += pack('BB', move.id, pp)

        data += pack('B', self.accuracy)
        data += pack('B', self.evasion)

        data += pack('B', self.status)

        data += pack('I', self.xp)

        return data

    @staticmethod
    def deserialise(data):
        """
        Deserialise data into a Mon object, then return it.

        :param data: The data to deserialise.
        :return: The newly created Mon.
        """
        offset = 0

        name_len = data[offset]
        offset += 1
        raw_nickname = data[offset:offset + name_len]
        nickname = raw_nickname.decode('utf-8')
        offset += name_len

        template_id, level, hp, fainted = data[offset:offset + 4]
        fainted = bool(fainted)
        offset += 4

        evs = list(data[offset:offset + 6])
        offset += 6
        ivs = list(data[offset:offset + 6])
        offset += 6

        num_moves = data[offset]
        offset += 1

        set_moves = []
        pps = []
        for _ in range(num_moves):
            move, pp = data[offset:offset + 2]
            set_moves.append(moves.moves_list[move])
            pps.append(pp)
            offset += 2

        mon = Mon(mons_list[template_id], level, ivs, evs, set_moves)

        mon.set_nickname(nickname)
        mon.hp = hp
        mon.fainted = fainted
        for i, v in enumerate(pps):
            mon.pp[i] = v

        mon.accuracy = data[offset]
        offset += 1

        mon.evasion = data[offset]
        offset += 1

        mon.status = data[offset]
        offset += 1

        mon.xp = unpack_from('I', data, offset)[0]
        offset += 4

        return mon

    def set_nickname(self, new_name: str) -> "Mon":
        self.nickname = new_name
        return self

    def calculate_stats(self):
        """
        Set stats to the correct value based on level, IVs and EVs.
        This is safe to call whenever as it doesn't modify current stats.
        """
        for i in range(len(self.stats)):
            if i == 0:
                # HP
                base = self.level + 10
            else:
                # any other stats
                base = 5

            self.stats[i] = math.floor(
                ((2 * self.template.base_stats[i] + self.ivs[i] + math.floor(self.evs[i] / 4)) * self.level) / 100
            ) + base

    def setup_moves_at_level(self):
        """
        Set up moveset to be made up of a random selection of the most recently learned moves for that level.

        This is done by going from the highest level to the lowest, picking up moves at a 2/3 chance.

        If the number of moves left to try is the same as or fewer than the number of empty slots on the mon,
        the chance is instead 100%.

        This function resets PP and should only be used when a new mon is instantiated.
        """
        self.moves = []
        self.pp = [0, 0, 0, 0]
        for i in range(len(self.template.learnset) - 1, -1, -1):
            if len(self.moves) >= 4:
                break

            if self.template.learnset[i][1] > self.level:
                continue

            chance = 2.0 / 3.0
            if (4 - len(self.moves)) >= i:
                chance = 1

            if random.random() < chance:
                self.pp[len(self.moves)] = self.template.learnset[i][0].max_pp
                self.moves.append(self.template.learnset[i][0])

    def full_heal(self):
        """
        Your mons are now fully healed! :D
        """
        self.modify_hp(99999999)
        for i in range(min(len(self.pp), len(self.moves))):
            self.pp[i] = self.moves[i].max_pp

    def modify_hp(self, by: int) -> int:
        original = self.hp

        self.hp += by
        self.hp = max(0, min(self.stats[0], self.hp))

        self.fainted = self.hp <= 0
        if self.fainted:
            self.status = constants.StatusEffect.NO_EFFECT

        return self.hp - original

    def take_heal(self, amount: int) -> int:
        """
        Heal HP. This does not trigger resistances, weaknesses or abilities.
        """
        if not self.fainted:
            return self.modify_hp(amount)
        else:
            return 0

    def take_damage(self, amount: int, dmg_type: constants.MonType) -> int:
        """
        Take damage. This takes into account resistances, weaknesses and abilities.
        """
        if not self.fainted:
            return self.modify_hp(-amount)
        else:
            return 0

    def apply_status(self, status: constants.StatusEffect):
        if self.status == constants.StatusEffect.NO_EFFECT:
            self.status = status
            return True
        else:
            return False
        
    def heal_status(self, status: Union[constants.StatusEffect, None]):
        '''
        Heals the status "status", or does nothing

        @returns True if the status was healed
        '''
        if status is None or self.status == status:
            self.status = constants.StatusEffect.NO_EFFECT
            return True
        else:
            return False

    def revive(self, half = False):
        if self.fainted:
            self.fainted = False
            self.hp = self.stats[0]
            if half:
                self.hp >>= 1
            return True
        else:
            return False
        
    def modify_pp(self, by: int) -> int:
        for i in range(min(len(self.pp), len(self.moves))):
            self.pp[i] += by
            self.pp[i] = max(0, min(self.moves[i].max_pp, self.pp[i]))

    def gain_exp(self, amount: int):
        self.xp += amount

    def level_up_needed(self):
        l = (self.level+1)
        return l*l*l <= self.xp

mons_list = [
    MonTemplate(
        "Tetris", "fuckin dude", constants.MonType.FIGHTING, constants.MonType.FIRE,
        None, None,
        85, 135, 130, 60, 70, 25, [
            (moves.moves_list[0], 5),
            (moves.moves_list[1], 5),
            (moves.moves_list[2], 8),
            (moves.moves_list[3], 13),
            (moves.moves_list[4], 21),
            (moves.moves_list[5], 30),
            (moves.moves_list[6], 40)
        ],
        0,
        1
    ),
    MonTemplate(
        "EMF Duck", "quack", constants.MonType.FIGHTING, constants.MonType.FIRE,
        None, None,
        85, 135, 130, 60, 70, 25, [
            (moves.moves_list[43], 5),
            (moves.moves_list[0], 5),
            (moves.moves_list[28], 8),
            (moves.moves_list[23], 13),
            (moves.moves_list[24], 21),
            (moves.moves_list[25], 30),
            (moves.moves_list[26], 40)
        ],
        1,
        2
    )
]

mons_list[1].evolve_level = 6
mons_list[1].evolve_mon = mons_list[0]

_cum = 0
_cum_weights = []
for mon in mons_list:
    _cum += mon.weight
    _cum_weights.append(_cum)

def choose_weighted_mon():
    value = random.randrange(_cum)
    i = 0
    while _cum_weights[i] < value:
        i+=1
    return mons_list[i]
