import math
import random
from typing import List, Tuple, Union

from prototype.game import moves, abilities, constants


class MonTemplate:
    """
    A template for a mon. This is copied into every instance of a mon, but NEVER MODIFIED.
    """
    id_inc = 0

    def __init__(self, name: str, desc: str, types: List[constants.MonType],
                 ability: abilities.Ability,
                 evolve_mon: Union["MonTemplate", None], evolve_level: Union[int, None],
                 base_hp: int, base_atk: int, base_def: int,
                 base_spatk: int, base_spdef: int, base_spd: int,
                 learnset: List[Tuple[moves.Move, int]]):
        """
        :param name: Name of the mon
        :param desc: Description (dex entry)
        :param types: List of types, e.g. for Fire, Ground give [MonType.Fire, MonType.Ground].
        :param ability: Ability. Use an object reference.
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
        """
        self.id = MonTemplate.id_inc
        MonTemplate.id_inc += 1

        self.name = name
        self.desc = desc
        self.types = types
        self.ability = ability
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


class Mon:
    """
    The dynamic form of a mon. This is the one used in battles and everywhere else.

    Don't call functions on this directly if currently in battle - use the Battle object instead.
    """
    @classmethod
    def deserialise(cls, data):
        """
        Deserialise data into a Mon object, then return it.

        :param data: The data to deserialise.
        :return: The newly created Mon.
        """
        pass

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

        self.status = constants.StatusEffect.NO_EFFECT

        self.pp = [0, 0, 0, 0]

        self.moves = []  # type: List[moves.Move]

        if set_moves:
            self.moves = set_moves
        else:
            self.setup_moves_at_level()

        self.full_heal()

    def serialise(self):
        """
        Transform the mon into serialised data. Opposite of Mon.deserialise().

        :return: The serialised data
        """
        pass

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
        for i in range(len(self.template.learnset)-1, -1, -1):
            if len(self.moves) >= 4:
                break

            if self.template.learnset[i][1] > self.level:
                continue

            chance = 2.0/3.0
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

        return self.hp - original

    def take_heal(self, amount: int) -> int:
        """
        Heal HP. This does not trigger resistances, weaknesses or abilities.
        """

        return self.modify_hp(amount)

    def take_damage(self, amount: int, dmg_type: constants.MonType) -> int:
        """
        Take damage. This takes into account resistances, weaknesses and abilities.
        """

        # TODO do damage multiplication by mon types, then modification by any abilities or stage effects, etc.
        return self.modify_hp(-amount)

    def apply_status(self, status: constants.StatusEffect):
        # TODO abilities would prevent status application here
        if self.status == constants.StatusEffect.NO_EFFECT:
            self.status = status
            return True
        else:
            return False


mons_list = [
    MonTemplate(
        "guy", "fuckin dude", [constants.MonType.FIGHTING, constants.MonType.FIRE],
        abilities.Ability.NO_ABILITY, None, None,
        85, 135, 130, 60, 70, 25, [
            (moves[0], 5),
            (moves[1], 5),
            (moves[2], 8),
            (moves[3], 13),
            (moves[4], 21),
            (moves[5], 30),
            (moves[6], 40)
        ]
    )
]
