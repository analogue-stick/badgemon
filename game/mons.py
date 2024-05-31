import math
from ..util import static_random as random
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
        # (oh except for the name, and xp)

        data = bytearray()

        name_len = len(self.nickname)
        data += pack('B', name_len)
        data += self.nickname.encode('utf-8')

        data += pack('BBBB', self.template.id, self.level, self.hp, self.fainted)

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
        "EMF Duck", "Can quack louder than a jet engine",
        constants.MonType.WATER, constants.MonType.NO_TYPE,
        None, None,
        50, 40, 40, 65, 60, 35, [
            (moves.moves_list[1], 5),
            (moves.moves_list[2], 5),
            (moves.moves_list[11], 8),
            (moves.moves_list[16], 13),
            (moves.moves_list[14], 21),
            (moves.moves_list[18], 30),
            (moves.moves_list[41], 40)
        ],
        1,
        100
    ),
    MonTemplate(
        "EMF Goose", "It's a peaceful day in the Maths Village, and you are a horrible goose",
        constants.MonType.WATER, constants.MonType.FIGHTING,
        None, None,
        80, 100, 65, 90, 65, 90, [
            (moves.moves_list[1], 5),
            (moves.moves_list[2], 5),
            (moves.moves_list[11], 8),
            (moves.moves_list[16], 13),
            (moves.moves_list[14], 21),
            (moves.moves_list[18], 30),
            (moves.moves_list[41], 40)
        ],
        2,
        4
    ),
    MonTemplate(
        "Bit Warden", "Their powerful shield is self-hosted",
        constants.MonType.PSYCHIC, constants.MonType.NO_TYPE,
        None, None,
        70, 70, 70, 40, 40, 25, [
            (moves.moves_list[0], 5),
            (moves.moves_list[1], 5),
            (moves.moves_list[24], 8),
            (moves.moves_list[18], 13),
            (moves.moves_list[20], 21),
            (moves.moves_list[40], 30),
            (moves.moves_list[44], 40)
        ],
        3,
        100
    ),
    MonTemplate(
        "Install Wizard", "He's actually paid for WinRAR",
        constants.MonType.PSYCHIC, constants.MonType.NO_TYPE,
        None, None,
        75, 75, 75, 100, 100, 30, [
            (moves.moves_list[0], 5),
            (moves.moves_list[1], 5),
            (moves.moves_list[24], 8),
            (moves.moves_list[18], 13),
            (moves.moves_list[20], 21),
            (moves.moves_list[40], 30),
            (moves.moves_list[44], 40)
        ],
        4,
        4
    ),
    MonTemplate(
        "Blacksmith", "Has a lot of coke. don't ask",
        constants.MonType.FIRE, constants.MonType.NO_TYPE,
        None, None,
        60, 90, 70, 20, 20, 60, [
            (moves.moves_list[3], 5),
            (moves.moves_list[12], 5),
            (moves.moves_list[28], 8),
            (moves.moves_list[30], 13),
            (moves.moves_list[17], 21),
            (moves.moves_list[26], 30),
            (moves.moves_list[19], 40)
        ],
        5,
        100
    ),
    MonTemplate(
        "Blacksmite", "This is the last time you misuse an anvil in minecraft",
        constants.MonType.FIRE, constants.MonType.STEEL,
        None, None,
        75, 100, 100, 70, 70, 60, [
            (moves.moves_list[3], 5),
            (moves.moves_list[12], 5),
            (moves.moves_list[28], 8),
            (moves.moves_list[30], 13),
            (moves.moves_list[17], 21),
            (moves.moves_list[26], 30),
            (moves.moves_list[19], 40)
        ],
        6,
        4
    ),
    MonTemplate(
        "Radio Wave", "FM modulated!",
        constants.MonType.WATER, constants.MonType.NO_TYPE,
        None, None,
        40, 60, 45, 60, 45, 120, [
            (moves.moves_list[18], 5),
            (moves.moves_list[3], 5),
            (moves.moves_list[14], 8),
            (moves.moves_list[41], 13),
            (moves.moves_list[14], 21),
            (moves.moves_list[15], 30),
            (moves.moves_list[12], 40)
        ],
        7,
        70
    ),
    MonTemplate(
        "Radio Tsunami", "Someone left the microwave running again",
        constants.MonType.WATER, constants.MonType.WATER,
        None, None,
        50, 75, 50, 75, 50, 150, [
            (moves.moves_list[18], 5),
            (moves.moves_list[3], 5),
            (moves.moves_list[14], 8),
            (moves.moves_list[41], 13),
            (moves.moves_list[14], 21),
            (moves.moves_list[15], 30),
            (moves.moves_list[12], 40)
        ],
        8,
        4
    ),
    MonTemplate(
        "Pirate", "True pirates seed",
        constants.MonType.DARK, constants.MonType.NO_TYPE,
        None, None,
        70, 80, 75, 25, 25, 50, [
            (moves.moves_list[11], 5),
            (moves.moves_list[1], 5),
            (moves.moves_list[26], 8),
            (moves.moves_list[2], 13),
            (moves.moves_list[31], 21),
            (moves.moves_list[15], 30),
            (moves.moves_list[20], 40)
        ],
        "unknown",
        80
    ),
    MonTemplate(
        "Swashbuckler", "Has never paid for a copy of Photoshop",
        constants.MonType.DARK, constants.MonType.NO_TYPE,
        None, None,
        75, 115, 90, 35, 35, 70, [
            (moves.moves_list[11], 5),
            (moves.moves_list[1], 5),
            (moves.moves_list[26], 8),
            (moves.moves_list[2], 13),
            (moves.moves_list[31], 21),
            (moves.moves_list[15], 30),
            (moves.moves_list[20], 40)
        ],
        "unknown",
        4
    ),
    MonTemplate(
        "Furry", "Will nya for headpats",
        constants.MonType.DRAGON, constants.MonType.NO_TYPE,
        None, None,
        75, 35, 25, 80, 80, 20, [
            (moves.moves_list[25], 5),
            (moves.moves_list[0], 5),
            (moves.moves_list[1], 8),
            (moves.moves_list[18], 13),
            (moves.moves_list[2], 21),
            (moves.moves_list[3], 30),
            (moves.moves_list[15], 40)
        ],
        "unknown",
        80
    ),
    MonTemplate(
        "Furry artist", "They're overworked, but damn are they not loaded",
        constants.MonType.DRAGON, constants.MonType.NO_TYPE,
        None, None,
        90, 45, 50, 110, 100, 25, [
            (moves.moves_list[25], 5),
            (moves.moves_list[0], 5),
            (moves.moves_list[1], 8),
            (moves.moves_list[18], 13),
            (moves.moves_list[2], 21),
            (moves.moves_list[3], 30),
            (moves.moves_list[15], 40)
        ],
        "unknown",
        8
    ),
    MonTemplate(
        "Maths PhD", "They've written a thesis on how many hyperplanes you can fit in a non-euclidean sphere or something",
        constants.MonType.NORMAL, constants.MonType.NO_TYPE,
        None, None,
        40, 30, 30, 75, 80, 40, [
            (moves.moves_list[2], 5),
            (moves.moves_list[0], 5),
            (moves.moves_list[1], 8),
            (moves.moves_list[0], 13),
            (moves.moves_list[18], 21),
            (moves.moves_list[34], 30),
            (moves.moves_list[42], 40)
        ],
        "unknown",
        90
    ),
    MonTemplate(
        "Maths Burnout", "Whoops",
        constants.MonType.GHOST, constants.MonType.NO_TYPE,
        None, None,
        60, 40, 40, 140, 100, 50, [
            (moves.moves_list[2], 5),
            (moves.moves_list[0], 5),
            (moves.moves_list[1], 8),
            (moves.moves_list[0], 13),
            (moves.moves_list[18], 21),
            (moves.moves_list[34], 30),
            (moves.moves_list[42], 40)
        ],
        "unknown",
        4
    ),
    MonTemplate(
        "StaticShock", "Kinda spicy tbh",
        constants.MonType.ELECTRIC, constants.MonType.NO_TYPE,
        None, None,
        15, 10, 10, 100, 30, 100, [
            (moves.moves_list[0], 5),
            (moves.moves_list[1], 5),
            (moves.moves_list[29], 8),
            (moves.moves_list[35], 13),
            (moves.moves_list[18], 21),
            (moves.moves_list[21], 30),
            (moves.moves_list[42], 40)
        ],
        "unknown",
        80
    ),
    MonTemplate(
        "Electrocution", "Too spicy tbh",
        constants.MonType.ELECTRIC, constants.MonType.FIGHTING,
        None, None,
        25, 25, 25, 160, 50, 180, [
            (moves.moves_list[0], 5),
            (moves.moves_list[1], 5),
            (moves.moves_list[29], 8),
            (moves.moves_list[35], 13),
            (moves.moves_list[18], 21),
            (moves.moves_list[21], 30),
            (moves.moves_list[42], 40)
        ],
        "unknown",
        4
    ),
    MonTemplate(
        "LAZERS", "LAZERSLAZERSLAZERS",
        constants.MonType.GHOST, constants.MonType.ELECTRIC,
        None, None,
        20, 40, 30, 80, 50, 120, [
            (moves.moves_list[39], 5),
            (moves.moves_list[29], 5),
            (moves.moves_list[18], 8),
            (moves.moves_list[42], 13),
            (moves.moves_list[13], 21),
            (moves.moves_list[0], 30),
            (moves.moves_list[34], 40)
        ],
        "unknown",
        70
    ),
    MonTemplate(
        "LAAAZEERRRSS", "LAAAAAAZZZZZEEE EEEEERRRRRSS",
        constants.MonType.GHOST, constants.MonType.ELECTRIC,
        None, None,
        50, 60, 40, 100, 70, 140, [
            (moves.moves_list[39], 5),
            (moves.moves_list[29], 5),
            (moves.moves_list[18], 8),
            (moves.moves_list[42], 13),
            (moves.moves_list[13], 21),
            (moves.moves_list[0], 30),
            (moves.moves_list[34], 40)
        ],
        "unknown",
        4
    ),
    MonTemplate(
        "Pint", "Quite stout",
        constants.MonType.POISON, constants.MonType.NO_TYPE,
        None, None,
        90, 70, 60, 25, 20, 40, [
            (moves.moves_list[23], 5),
            (moves.moves_list[11], 5),
            (moves.moves_list[0], 8),
            (moves.moves_list[1], 13),
            (moves.moves_list[37], 21),
            (moves.moves_list[19], 30),
            (moves.moves_list[18], 40)
        ],
        "unknown",
        100
    ),
    MonTemplate(
        "Keg", "Finely aged",
        constants.MonType.POISON, constants.MonType.NO_TYPE,
        None, None,
        125, 110, 100, 50, 40, 40, [
            (moves.moves_list[23], 5),
            (moves.moves_list[11], 5),
            (moves.moves_list[0], 8),
            (moves.moves_list[1], 13),
            (moves.moves_list[37], 21),
            (moves.moves_list[19], 30),
            (moves.moves_list[18], 40)
        ],
        "unknown",
        4
    ),
    MonTemplate(
        "AntiStatic", "Makes your body less spicy",
        constants.MonType.GROUND, constants.MonType.NO_TYPE,
        None, None,
        100, 55, 90, 40, 100, 25, [
            (moves.moves_list[0], 5),
            (moves.moves_list[3], 5),
            (moves.moves_list[12], 8),
            (moves.moves_list[36], 13),
            (moves.moves_list[19], 21),
            (moves.moves_list[38], 30),
            (moves.moves_list[2], 40)
        ],
        "unknown",
        60
    ),
    MonTemplate(
        "Multimeter", "Knows how many amps are being drawn",
        constants.MonType.ELECTRIC, constants.MonType.NO_TYPE,
        None, None,
        60, 55, 65, 55, 60, 40, [
            (moves.moves_list[0], 5),
            (moves.moves_list[29], 5),
            (moves.moves_list[35], 8),
            (moves.moves_list[18], 13),
            (moves.moves_list[2], 21),
            (moves.moves_list[40], 30),
            (moves.moves_list[44], 40)
        ],
        "unknown",
        80
    ),
    MonTemplate(
        "Omnimeter", "Knows the answers to the universe",
        constants.MonType.ELECTRIC, constants.MonType.PSYCHIC,
        None, None,
        80, 80, 90, 90, 80, 75, [
            (moves.moves_list[0], 5),
            (moves.moves_list[29], 5),
            (moves.moves_list[35], 8),
            (moves.moves_list[18], 13),
            (moves.moves_list[2], 21),
            (moves.moves_list[40], 30),
            (moves.moves_list[44], 40)
        ],
        "unknown",
        4
    ),
    MonTemplate(
        "Firepit", "Keeps your hands warm - but watch out!",
        constants.MonType.FIRE, constants.MonType.GROUND,
        None, None,
        30, 75, 25, 75, 30, 80, [
            (moves.moves_list[38], 5),
            (moves.moves_list[30], 5),
            (moves.moves_list[18], 8),
            (moves.moves_list[28], 13),
            (moves.moves_list[30], 21),
            (moves.moves_list[12], 30),
            (moves.moves_list[0], 40)
        ],
        "unknown",
        90
    ),
    MonTemplate(
        "Firenado", "Fire makes everything better",
        constants.MonType.FIRE, constants.MonType.FIRE,
        None, None,
        50, 100, 40, 110, 40, 130, [
            (moves.moves_list[38], 5),
            (moves.moves_list[30], 5),
            (moves.moves_list[18], 8),
            (moves.moves_list[28], 13),
            (moves.moves_list[30], 21),
            (moves.moves_list[12], 30),
            (moves.moves_list[0], 40)
        ],
        "unknown",
        4
    ),
    MonTemplate(
        "Ghidra", "There's a lingering feeling that they're a cop but it's probably fine",
        constants.MonType.DRAGON, constants.MonType.NO_TYPE,
        None, None,
        60, 100, 80, 50, 110, 10, [
            (moves.moves_list[25], 5),
            (moves.moves_list[0], 5),
            (moves.moves_list[1], 8),
            (moves.moves_list[2], 13),
            (moves.moves_list[27], 21),
            (moves.moves_list[15], 30),
            (moves.moves_list[43], 40)
        ],
        "unknown",
        50
    ),
    MonTemplate(
        "EMF 2020", "Faint whispers of festivals past",
        constants.MonType.GHOST, constants.MonType.NO_TYPE,
        None, None,
        50, 90, 90, 90, 90, 20, [
            (moves.moves_list[0], 5),
            (moves.moves_list[34], 5),
            (moves.moves_list[39], 8),
            (moves.moves_list[13], 13),
            (moves.moves_list[18], 21),
            (moves.moves_list[19], 30),
            (moves.moves_list[3], 40)
        ],
        "unknown",
        20
    ),
    MonTemplate(
        "smolhaj", "Just a lil guy",
        constants.MonType.WATER, constants.MonType.NO_TYPE,
        None, None,
        15, 15, 25, 20, 40, 20, [
            (moves.moves_list[11], 5),
            (moves.moves_list[0], 5),
            (moves.moves_list[14], 8),
            (moves.moves_list[41], 13),
            (moves.moves_list[18], 21),
            (moves.moves_list[20], 30),
            (moves.moves_list[41], 40)
        ],
        9,
        70
    ),
    MonTemplate(
        "blahaj", "Does 2x damage to transphobes",
        constants.MonType.WATER, constants.MonType.NO_TYPE,
        None, None,
        110, 160, 80, 140, 60, 90, [
            (moves.moves_list[11], 5),
            (moves.moves_list[0], 5),
            (moves.moves_list[14], 8),
            (moves.moves_list[41], 13),
            (moves.moves_list[18], 21),
            (moves.moves_list[20], 30),
            (moves.moves_list[41], 40)
        ],
        10,
        4
    ),
    MonTemplate(
        "Tetris", "Is often seen hiding in the arcade",
        constants.MonType.NORMAL, constants.MonType.NO_TYPE,
        None, None,
        200, 120, 100, 60, 120, 60, [
            (moves.moves_list[0], 5),
            (moves.moves_list[1], 5),
            (moves.moves_list[2], 8),
            (moves.moves_list[3], 13),
            (moves.moves_list[15], 21),
            (moves.moves_list[21], 30),
            (moves.moves_list[43], 40)
        ],
        0,
        20
    ),
    MonTemplate(
        "Mew", "Was found hiding under a van in null sector",
        constants.MonType.PSYCHIC, constants.MonType.NO_TYPE,
        None, None,
        100, 100, 100, 100, 100, 100, [
            (moves.moves_list[40], 5),
            (moves.moves_list[44], 5),
            (moves.moves_list[2], 8),
            (moves.moves_list[3], 13),
            (moves.moves_list[24], 21),
            (moves.moves_list[18], 30),
            (moves.moves_list[19], 40)
        ],
        "unknown",
        4
    ),
    MonTemplate(
        "NaN", "They will absorb your vision into their consiousness",
        constants.MonType.POISON, constants.MonType.BUG,
        None, None,
        10, 156, 42, 11, 69, 12, [
            (moves.moves_list[23], 5),
            (moves.moves_list[8], 5),
            (moves.moves_list[9], 8),
            (moves.moves_list[10], 13),
            (moves.moves_list[23], 21),
            (moves.moves_list[32], 30),
            (moves.moves_list[43], 40)
        ],
        "unknown",
        50
    ),
    MonTemplate(
        "NullPointer", "You follow the signs, but they point at the abyss. Your journey has been meaningless",
        constants.MonType.POISON, constants.MonType.BUG,
        None, None,
        70, 117, 77, 21, 127, 13, [
            (moves.moves_list[23], 5),
            (moves.moves_list[8], 5),
            (moves.moves_list[9], 8),
            (moves.moves_list[10], 13),
            (moves.moves_list[23], 21),
            (moves.moves_list[32], 30),
            (moves.moves_list[43], 40)
        ],
        "unknown",
        20
    ),
    MonTemplate(
        "MISSINGNO.", "The shoreline is awash with the screams of those that should not exist",
        constants.MonType.POISON, constants.MonType.BUG,
        None, None,
        15, 287, 87, 137, 13, 11, [
            (moves.moves_list[23], 5),
            (moves.moves_list[8], 5),
            (moves.moves_list[9], 8),
            (moves.moves_list[10], 13),
            (moves.moves_list[23], 21),
            (moves.moves_list[32], 30),
            (moves.moves_list[43], 40)
        ],
        "unknown",
        10
    ),
    MonTemplate(
        "Div. Zero", "These axioms are too feeble to describe the knowledge of the gods",
        constants.MonType.BUG, constants.MonType.NO_TYPE,
        None, None,
        70, 110, 0, 110, 0, 0, [
            (moves.moves_list[32], 5),
            (moves.moves_list[9], 5),
            (moves.moves_list[10], 8),
            (moves.moves_list[8], 13),
            (moves.moves_list[19], 21),
            (moves.moves_list[18], 30),
            (moves.moves_list[43], 40)
        ],
        "unknown",
        40
    ),
    MonTemplate(
        "Out.Memory", "Your head is full, but it is set to burst. Everything fades",
        constants.MonType.BUG, constants.MonType.NO_TYPE,
        None, None,
        90, 111, 111, 111, 111, 44, [
            (moves.moves_list[32], 5),
            (moves.moves_list[9], 5),
            (moves.moves_list[10], 8),
            (moves.moves_list[8], 13),
            (moves.moves_list[19], 21),
            (moves.moves_list[18], 30),
            (moves.moves_list[43], 40)
        ],
        "unknown",
        10
    ),
]

print(f"NO. MONS: {len(mons_list)}")

# duck -> goose
mons_list[ 0].evolve_level = 15
mons_list[ 0].evolve_mon = mons_list[1]
# warden -> wizard
mons_list[ 2].evolve_level = 20
mons_list[ 2].evolve_mon = mons_list[3]
# smith -> smite
mons_list[ 4].evolve_level = 17
mons_list[ 4].evolve_mon = mons_list[5]
# wave -> tsunami
mons_list[ 6].evolve_level = 18
mons_list[ 6].evolve_mon = mons_list[7]
# pirate -> swashbucker
mons_list[ 8].evolve_level = 19
mons_list[ 8].evolve_mon = mons_list[9]
# furry -> artist
mons_list[10].evolve_level = 16
mons_list[10].evolve_mon = mons_list[11]
# PhD -> burnout
mons_list[12].evolve_level = 16
mons_list[12].evolve_mon = mons_list[13]
# static -> 'cute
mons_list[14].evolve_level = 20
mons_list[14].evolve_mon = mons_list[15]
# lazer -> LAZER
mons_list[16].evolve_level = 15
mons_list[16].evolve_mon = mons_list[17]
# pint -> keg
mons_list[18].evolve_level = 18
mons_list[18].evolve_mon = mons_list[19]
# multi -> omni
mons_list[21].evolve_level = 23
mons_list[21].evolve_mon = mons_list[22]
# pit -> nado
mons_list[23].evolve_level = 19
mons_list[23].evolve_mon = mons_list[24]
# smol -> haj
mons_list[27].evolve_level = 17
mons_list[27].evolve_mon = mons_list[28]
# nan -> null
mons_list[31].evolve_level = 25
mons_list[31].evolve_mon = mons_list[32]
# null -> missing
mons_list[32].evolve_level = 39
mons_list[32].evolve_mon = mons_list[33]
# div -> outmem
mons_list[34].evolve_level = 27
mons_list[34].evolve_mon = mons_list[35]

_cum = 0
_cum_weights = []
for mon in mons_list:
    _cum += mon.weight
    _cum_weights.append(_cum)

def choose_weighted_mon():
    value = random.randrange(0, _cum)
    i = 0
    while _cum_weights[i] < value:
        i+=1
    return mons_list[i]
