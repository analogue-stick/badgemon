try:
    from sys import implementation as _sys_implementation
    if _sys_implementation.name != "micropython":
        from typing import Callable, Union, TYPE_CHECKING
        if TYPE_CHECKING:
            from . import player, battle_main, mons
except ImportError:
    pass

from ..game import constants

class FieldTargetingType:
    NOT_USABLE = 0
    TARGETS_SPECIFIC_MON = 1
    NO_TARGETS = 2


class Item:
    id_inc = 0

    def __init__(self, name: str, desc: str, value: int, usable_in_battle: bool, usable_in_field: int,
                 function_in_battle: Union[
                     Callable[['player.Player', 'battle_main.Battle', 'mons.Mon', 'mons.Mon'], None], None
                 ] = None,
                 function_in_field: Union[Callable[['player.Player', Union['mons.Mon', None]], None], None] = None):
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

def parabox(mon: 'mons.Mon'):
    mon.heal_status(None)
    mon.take_heal(999999)

items_list = [
    Item("Charcoal", "A lump of activated charcoal. It does the job of curing poison, just about.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.heal_status(constants.StatusEffect.POISONED), lambda _, m: m.heal_status(constants.StatusEffect.POISONED)),
    Item("Ointment", "A wet, sticky gel that soothes burns.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.heal_status(constants.StatusEffect.BURNED), lambda _, m: m.heal_status(constants.StatusEffect.BURNED)),
    Item("Heat Pack", "A portable heater to attach to frozen badgemon.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.heal_status(constants.StatusEffect.FROZEN), lambda _, m: m.heal_status(constants.StatusEffect.FROZEN)),
    Item("Klaxon", "\'Heals\' a sleeping badgemon.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.heal_status(constants.StatusEffect.SLEEPING), lambda _, m: m.heal_status(constants.StatusEffect.SLEEPING)),
    Item("Hot Chocolate", "One cup of this and paralysis is no more.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.heal_status(constants.StatusEffect.PARALYZED), lambda _, m: m.heal_status(constants.StatusEffect.PARALYZED)),
    Item("Antibiotics", "Cures any status condition and heals the badgemon to full HP.",
         3000, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: parabox(m), lambda _, m: parabox(m)),
    Item("Gargantuan Cookie", "Heals a badgemon to full HP. Useless if they are fainted.",
         2500, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.take_heal(999999), lambda _, m: m.take_heal(999999)),
    Item("Massive Cookie", "Heals a badgemon by 200 HP. Useless if they are fainted.",
         1500, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.take_heal(200), lambda _, m: m.take_heal(200)),
    Item("Large Cookie", "Heals a badgemon by 50 HP. Useless if they are fainted.",
         700, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.take_heal(50), lambda _, m: m.take_heal(50)),
    Item("Cookie", "Heals a badgemon by 20 HP. Useless if they are fainted.",
         200, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.take_heal(20), lambda _, m: m.take_heal(20)),
    Item("Paracetamol", "Cures any status condition.",
         400, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.heal_status(None), lambda _, m: m.heal_status(None)),
    Item("Enticing Scent", "Revives a badgemon at half HP.",
         2000, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.revive(True), lambda _, m: m.revive(True)),
    Item("Extreme Scent", "Revives a badgemon at full HP.",
         4000, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.revive(), lambda _, m: m.revive()),
    Item("Espresso", "Restores 10 PP of all a badgemon's moves.",
         400, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.modify_pp(10), lambda _, m: m.modify_pp(10)),
    Item("Energy Drink", "Fully restores the PP of all a badgemon's moves.",
         1000, True,  FieldTargetingType.TARGETS_SPECIFIC_MON, lambda _, __, m, ___: m.modify_pp(999999), lambda _, m: m.modify_pp(999999)),
    Item("Fishing Rod", "Allows fishing, but only if you have an Eastnor Fishing Permit.",
         500, False,  FieldTargetingType.NO_TARGETS, None, lambda _, __: print("You don't have a licence!")),
    Item("Badgemon Doll", "Was intended to look cute... probably.",
         400, True,  FieldTargetingType.NOT_USABLE, lambda _, __, m, ___: print(f"{m.nickname} appreciated the craftsmanship of the doll."), None),
    Item("HexBox", "A device able to catch badgemon after they are weakened.",
         200, True,  FieldTargetingType.NOT_USABLE, lambda p, b, ___, t: 1, None),
    Item("Super HexBox", "A modification of the original HexBox design, with enhanced catching ability.",
         600, True,  FieldTargetingType.NOT_USABLE, lambda p, b, ___, t: 1.5, None),
    Item("Ultra HexBox", "A high-tech box full of features to make catching badgemon easier.",
         800, True,  FieldTargetingType.NOT_USABLE, lambda p, b, ___, t: 2, None),
    Item("Master HexBox", "The ultimate box. Will catch a badgemon without fail.",
         1600, True,  FieldTargetingType.NOT_USABLE, lambda p, b, ___, t: 255, None),
]
