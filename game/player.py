from struct import pack
import time

from . import items, badgedex

try:
    from typing import List, Tuple, Union, TYPE_CHECKING

    if TYPE_CHECKING:
        from .mons import Mon
        from .items import Item
        from .moves import Move
        from .battle_main import Battle
except ImportError:
    pass

#_TIME_BETWEEN_HEALS = const(1000*60*1) # 1 minute
_TIME_BETWEEN_HEALS = 1000*60*1 # 1 minute

class Player:
    def __init__(self, name: str, badgemon: List['Mon'], badgemon_case: List['Mon'], inventory: List[Tuple['Item', int]]):
        """
        The Player class will be inherited by classes implementing the user interface, it broadly holds player data and
        handles interaction with the main Battle class

        @param name:
        @param badgemon: player's team. max 6
        @param badgemon_case: all other badgemon
        @param inventory:
        """
        self.name = name
        self.badgemon = badgemon[0:6]
        self.badgemon_case = badgemon_case
        self.inventory = inventory
        self.last_heal = time.ticks_ms()

        self.badgedex = badgedex.Badgedex()

        self.random_encounters = True

        self.battle_context: Union['Move', None] = None

    def serialise(self):
        data = bytearray()

        data += pack('B', len(self.name))
        data += self.name.encode('utf-8')

        data += pack('B', len(self.badgemon))
        for mon in self.badgemon:
            mon_data = mon.serialise()
            data += pack('B', len(mon_data))
            data += mon_data

        data += pack('B', len(self.inventory))
        for item, count in self.inventory:
            data += pack('BB', item.id, count)

    @staticmethod
    def deserialise(data: bytearray) -> 'Player':
        offset = 0

        name_len = data[offset]
        offset += 1
        name = data[offset:offset + name_len].decode('utf-8')
        offset += name_len

        mons_len = data[offset]
        offset += 1
        badgemon = []
        for _ in range(mons_len):
            mon_len = data[offset]
            offset += 1
            mon = Mon.deserialise(data[offset:offset + mon_len])
            badgemon.append(mon)
            offset += mon_len

        inventory = []
        inv_len = data[offset]
        offset += 1
        for _ in range(inv_len):
            item_id, count = data[offset:offset + 2]
            item = items.items_list[item_id]
            inventory.append((item, count))
            offset += 1

        return Player(name, badgemon, inventory)

    def get_move(self) -> Tuple[int, Union['Mon', 'Item', 'Move', None]]:
        """
        This is overridden by any parent class handling user interactions.
        """
        pass

    @staticmethod
    def get_meters_walked():
        return time.ticks_ms()/1000

    def full_heal_available(self) -> int:
        diff = time.ticks_diff(time.ticks_ms(), self.last_heal)
        if diff >= _TIME_BETWEEN_HEALS:
            self.last_heal = time.ticks_add(time.ticks_ms(), -_TIME_BETWEEN_HEALS)
        return diff

    def use_full_heal(self) -> bool:
        diff = self.full_heal_available()
        if diff >= _TIME_BETWEEN_HEALS:
            for guy in self.badgemon:
                guy.full_heal()
            self.last_heal = time.ticks_ms()
            print("Healed!")
        else:
            print(f"Heal is not allowed for another {(_TIME_BETWEEN_HEALS-diff)/1000} seconds")