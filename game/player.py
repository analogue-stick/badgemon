from struct import pack
from typing import List, Tuple
from game import mons, items


class Player:
    def __init__(self, name: str, badgemon: List[mons.Mon], inventory: List[Tuple[items.Item, int]]):
        self.name = str
        self.badgemon = badgemon
        self.inventory = inventory

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
