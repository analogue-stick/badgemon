# Confusion is not included here because it can be applied alongside other effects
# and is not a persistent effect
class StatusEffect:
    NO_EFFECT = 0
    POISONED = 1
    BURNED = 2
    PARALYZED = 3
    FROZEN = 4
    SLEEPING = 5

def status_to_str(status: StatusEffect) -> str:
    if status == StatusEffect.NO_EFFECT:
        return ""
    elif status == StatusEffect.POISONED:
        return "poisoned"
    elif status == StatusEffect.BURNED:
        return "burned"
    elif status == StatusEffect.PARALYZED:
        return "paralyzed"
    elif status == StatusEffect.FROZEN:
        return "frozen"
    elif status == StatusEffect.SLEEPING:
        return "sleeping"

class MonType:
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

def type_to_str(type: MonType) -> str:
    if type == MonType.NO_TYPE:
        return ""
    elif type == MonType.BUG:
        return "bug"
    elif type == MonType.DARK:
        return "dark"
    elif type == MonType.DRAGON:
        return "dragon"
    elif type == MonType.ELECTRIC:
        return "electric"
    elif type == MonType.FIGHTING:
        return "fighting"
    elif type == MonType.FIRE:
        return "fire"
    elif type == MonType.GHOST:
        return "ghost"
    elif type == MonType.GRASS:
        return "grass"
    elif type == MonType.GROUND:
        return "ground"
    elif type == MonType.ICE:
        return "ice"
    elif type == MonType.NORMAL:
        return "normal"
    elif type == MonType.POISON:
        return "poison"
    elif type == MonType.PSYCHIC:
        return "psychic"
    elif type == MonType.ROCK:
        return "rock"
    elif type == MonType.STEEL:
        return "steel"
    elif type == MonType.WATER:
        return "water"


stat_names = ["HP", "ATK", "DEF", "SpATK", "SpDEF", "SPD"]
STAT_HP = 0
STAT_ATK = 1
STAT_DEF = 2
STAT_SPATK = 3
STAT_SPDEF = 4
STAT_SPD = 5

# [attacking][defending]
# 1 is 2x, 0 is 1x, -1 is 0.5x, -100 is 0x
# So it's damage*2^(this table)
type_table = [
    [0 for _ in range(17)] for _ in range(17)
    ]
