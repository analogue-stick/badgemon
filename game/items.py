try:
    from typing import Callable, Union
except ImportError:
    pass

from game import constants, player, battle_main, mons


class FieldTargetingType:
    NOT_USABLE = 0
    TARGETS_SPECIFIC_MON = 1
    NO_TARGETS = 2


class Item:
    id_inc = 0

    def __init__(self, name: str, desc: str, value: int, usable_in_battle: bool, usable_in_field: int,
                 function_in_battle: Union[
                     Callable[[player.Player, battle_main.Battle, mons.Mon, mons.Mon], None], None
                 ] = None,
                 function_in_field: Union[Callable[[player.Player, Union[mons.Mon, None]], None], None] = None):
        """
        :param name: Name of the item
        :param desc: Description of the item
        :param value: Value of the item (price when bought)
        :param usable_in_battle: Is this item usable in battle? (Must have function_in_battle defined)
        :param usable_in_field: How is this item usable in the field?
        :param function_in_battle: The function to call when this item is used in battle. (player, battle, user, target)
        user is always the player's mon. target is always the opposing mon - even if those variables are not used.
        :param function_in_field: The function to call when this item is used in the field. (player, target_mon)
        If usable_in_field == FieldTargetingType.NO_TARGETS, target_mon will be None.
        """

        self.id = Item.id_inc
        Item.id_inc += 1

        self.name = name
        self.desc = desc
        self.value = value
        self.usable_in_battle = usable_in_battle
        self.usable_in_field = usable_in_field
        self.function_in_battle = function_in_battle
        self.function_in_field = function_in_field

def parabox(mon: mons.Mon):
    mon.heal_status(None)
    mon.modify_hp(999999)

items_list = [
    Item("Charcoal", "A lump of activated charcoal. It does the job of curing poison, just about.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.heal_status(constants.StatusEffect.POISONED)),
    Item("Ointment", "A wet, sticky gel that soothes burns.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.heal_status(constants.StatusEffect.BURNED)),
    Item("Heat Pack", "A portable heater to attach to frozen badgemon.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.heal_status(constants.StatusEffect.FROZEN)),
    Item("Klaxon", "\"Heals\" a sleeping badgemon.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.heal_status(constants.StatusEffect.SLEEPING)),
    Item("Hot Chocolate", "One cup of this and paralysis is no more.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.heal_status(constants.StatusEffect.PARALYZED)),
    Item("Entire Box of Paracetamol", "Cures any status condition and heals the badgemon to full HP.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: parabox(m)),
    Item("Entire Box of Cookies", "Heals a badgemon to full HP.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.modify_hp(999999)),
    Item("Massive Cookie", "Heals a badgemon by 200 HP.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.modify_hp(200)),
    Item("Large Cookie", "Heals a badgemon by 50 HP.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.modify_hp(50)),
    Item("Cookie", "Heals a badgemon by 20 HP.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.modify_hp(20)),
    Item("Paracetamol", "Cures any status condition.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.heal_status(None)),
]
