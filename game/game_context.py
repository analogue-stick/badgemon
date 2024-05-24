from struct import pack, unpack_from
from ..game.mons import Mon, mons_list
from ..game.items import items_list
from ..game.player import Player

potion = items_list[5]
mon_template1 = mons_list[0]
mon_template2 = mons_list[1]
mon1 = Mon(mon_template1, 5).set_nickname("small guy")
mon2 = Mon(mon_template2, 17).set_nickname("mr. 17")
mon3 = Mon(mon_template1, 17).set_nickname("David")
mon4 = Mon(mon_template2, 33).set_nickname("large individual")
mon5 = Mon(mon_template1, 100).set_nickname("biggest dude")

VERSION = 1

class GameContext:
    def __init__(self):
        self.player = Player("Scarlett", [], [], {potion: 2})
        self.random_encounters = True

    def serialise(self):
        data = bytearray()
        data += b'BGGR'
        data += pack('H', VERSION)
        player = self.player.serialise()
        data += pack("H", len(player))
        data += player
        data += pack('?', self.random_encounters)
        return data

    def deserialise(data):
        if data[0:4] != b'BGGR':
            print("FILE UNRECOGNISED")
            return None
        if unpack_from('H', data, 4)[0] != VERSION:
            print("WRONG VERSION")
            return None
        offset = 6
        gc = GameContext()
        pl_len = unpack_from('H', data, offset)[0]
        offset += 2
        gc.player = Player.deserialise(data[offset:offset + pl_len])
        offset += pl_len
        gc.random_encounters = unpack_from('?', data, offset)[0]
        return gc