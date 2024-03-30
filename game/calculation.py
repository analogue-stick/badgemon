import random

from game import constants

@micropython.viper
def calculate_damage(level: int, power: int, attack: int, defense: int, type: constants.MonType, mon1_type1: constants.MonType, mon1_type2: constants.MonType, mon2_type1: constants.MonType, mon2_type2: constants.MonType) -> int:
    """
    Calculates the amount of damage to apply.
    Uses https://bulbapedia.bulbagarden.net/wiki/Damage#Generation_V_onward
    """
    damage = ((((((((level<<1)//5)+2)*power)*attack)/defense)//50)+2)
    if is_critical():
        damage <<= 1
    if type == mon1_type1 or type == mon1_type2: # STAB
        damage += damage >> 1
    type_bonus1 = constants.type_table[type][mon2_type1]
    type_bonus2 = constants.type_table[type][mon2_type2]
    type_bonus = type_bonus1 + type_bonus2
    if type_bonus > 0:
        damage << type_bonus
    elif type_bonus < 0:
        damage >> -type_bonus
    damage *= random.randrange(217,256)
    damage >>= 8
    return damage

@micropython.viper
def is_critical() -> bool:
    return random.getrandbits(3) == 0 # 1/8 chance

@micropython.viper
def get_hit(accuracy: int) -> bool:
    return random.getrandbits(8) >= accuracy