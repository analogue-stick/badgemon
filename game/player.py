from struct import pack
from typing import List, Tuple, Union
from game import mons, items, moves
import sys


class Player:
    def __init__(self, name: str, badgemon: List[mons.Mon], inventory: List[Tuple[items.Item, int]]):
        """
        The Player class will be inherited by classes implementing the user interface, it broadly holds player data and
        handles interaction with the main Battle class

        @param name:
        @param badgemon:
        @param inventory:
        """
        self.name = name
        self.badgemon = badgemon
        self.inventory = inventory

        self.news_target = None

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
            mon = mons.Mon.deserialise(data[offset:offset + mon_len])
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

    def get_move(self) -> Tuple[int, Union[mons.Mon, items.Item, moves.Move, None]]:
        """
        This is overridden by any parent class handling user interactions.
        """
        pass
