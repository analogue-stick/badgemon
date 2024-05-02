try:
    from typing import Callable, Union
except ImportError:
    pass

from ..game import player, battle_main, mons


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


items_list = [
    Item("Potion", "Heals a mon in combat", 200, True, FieldTargetingType.TARGETS_SPECIFIC_MON,
         lambda _, __, m, ___: m.take_heal(20), lambda _, m: m.take_heal(20)),
    # items go here
]
