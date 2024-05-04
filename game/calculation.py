import random

try:
    from typing import Tuple
except ImportError:
    pass

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
