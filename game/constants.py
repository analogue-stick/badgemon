# Confusion is not included here because it can be applied alongside other effects
# and is not a persistent effect
class StatusEffect:
    NO_EFFECT = 0
    POISONED = 1
    BURNED = 2
    PARALYZED = 3
    FROZEN = 4
    SLEEPING = 5


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


class ItemType:
    NO_ITEM = 0
    MASTER_HEXBOX = 1
    ULTRA_HEXBOX = 2
    SUPER_HEXBOX = 3
    HEXBOX = 4
    ANTIDOTE = 5
    OINTMENT = 6
    HEAT_PACK = 7
    KLAXON = 8
    HOT_CHOC = 9
    BOX_PARACETAMOL = 10
    BOX_COOKIES = 11
    MASSIVE_COOKIE = 12
    LARGE_COOKIE = 13
    COOKIE = 14
    PARACETAMOL = 15
    ENTICING_SCENT = 16 
    OP_SCENT = 17
    TEA = 18
    COFFEE = 19 
    ESPRESSO = 20
    ENERGY_DRINK = 21

stat_names = ["HP", "ATK", "DEF", "SpATK", "SpDEF", "SPD"]
