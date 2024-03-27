from random import random, choice
from struct import pack, unpack
from typing import List
from enum import Enum


# Confusion is not included here because it can be applied alongside other effects
# and is not a persistent effect
class StatusEffect(Enum):
    NO_EFFECT = 0
    POISONED = 1
    BURNED = 2
    PARALYZED = 3
    FROZEN = 4
    SLEEPING = 5


class MonType(Enum):
    NO_TYPE = 0
    BUG = 1
    DARK = 2
    DRAGON = 3
    ELECTRIC = 4
    FIGHTING = 5
    FIRE = 6
    GHOST = 7
    GRASS = 8
    GROUND = 9
    ICE = 10
    NORMAL = 11
    POISON = 12
    PSYCHIC = 13
    ROCK = 14
    STEEL = 15
    WATER = 16
