import math
from ..util import static_random as random

from sys import implementation as _sys_implementation

from ..game.mons import Mon
if _sys_implementation.name != "micropython":
    from typing import Tuple

from . import constants

STAGES = [33, 36, 43, 50, 60, 75, 100, 133, 166, 200, 233, 266, 300]

EFF_EFFECTIVE = 1
EFF_INEFFECTIVE = -1
EFF_NORMAL = 0


def calculate_damage(level: int, power: int, attack: int, defense: int, type: constants.MonType,
                     mon1_type1: constants.MonType, mon1_type2: constants.MonType, mon2_type1: constants.MonType,
                     mon2_type2: constants.MonType) -> Tuple[int, bool, int]:
    """
    Calculates the amount of damage to apply.
    Uses https://bulbapedia.bulbagarden.net/wiki/Damage#Generation_V_onward

    @return: (damage, critical hit, effectiveness)
    """
    damage = (((((level << 1) // 5 + 2) * power * attack) // defense) // 50) + 2

    crit = is_critical()
    if crit:
        damage <<= 1

    if type == mon1_type1 or type == mon1_type2:  # STAB
        damage += damage >> 1

    type_bonus1 = constants.type_table[type][mon2_type1]
    type_bonus2 = constants.type_table[type][mon2_type2]
    type_bonus = type_bonus1 + type_bonus2
    effective = EFF_NORMAL
    if type_bonus > 0:
        effective = EFF_EFFECTIVE
        damage <<= type_bonus
    elif type_bonus < 0:
        effective = EFF_INEFFECTIVE
        damage >>= -type_bonus
    damage *= random.randrange(217, 256)
    damage >>= 8
    return damage, crit, effective


def is_critical() -> bool:
    return random.getrandbits(3) == 0  # 1/8 chance


def get_hit(move_accuracy: int, user_accuracy: int, target_evasion: int) -> bool:
    """
    Returns whether an attack should hit
    https://bulbapedia.bulbagarden.net/wiki/Accuracy#Generations_III_and_IV

    @param move_accuracy:
    @param user_accuracy:
    @param target_evasion:
    @return:
    """
    user_accuracy -= target_evasion
    user_accuracy += 6
    user_accuracy = min(user_accuracy, 11)
    stage = STAGES[user_accuracy]

    move_accuracy *= stage
    move_accuracy //= 100

    return random.randrange(0, 100) <= move_accuracy

def get_catch_rate(mon: Mon, ball: float):
    if ball == 255:
        return 1.0
    three = (3 * mon.stats[constants.STAT_HP])
    base = (three - (2 * mon.hp)) / three
    base *= mon.template.catch_rate
    base *= ball
    base *= constants.catch_table[mon.status]
    base = min(max(base,0.0),1.0)
    print(f"BASE: {base}")
    check2 = 1048560/math.pow(65280/base, 0.25)
    print(f"RATE: {check2}")
    return (base, check2)

def get_shake(catch_rate: float):
    check1 = random.randrange(0, 65536)
    print(f"1: {check1}, 2: {catch_rate}")
    return check1 < catch_rate

def get_experience(mon: Mon, target: Mon):
    return int(((mon.template.base_exp * target.level)/5)*math.pow((2*target.level+10)/(target.level+mon.level+10), 2.5)+1)
