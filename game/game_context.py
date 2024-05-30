from struct import pack, unpack_from

from ..game.customisation import Customisation
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

VERSION = 3

class GameContext:
    def __init__(self):
        self.player = Player("SCARLETT", [], [], {potion: 2})
        self.random_encounters = True
        self.custom = Customisation()

    def serialise(self):
        data = bytearray()
        data += b'BGGR'
        data += pack('H', VERSION)
        player = self.player.serialise()
        data += pack("H", len(player))
        data += player
        data += pack('?', self.random_encounters)
        custom = self.custom.serialise()
        data += pack("B", len(custom))
        data += custom
        return data

    def deserialise(data):
        offset = 0
        gc = GameContext()
        pl_len = unpack_from('H', data, offset)[0]
        offset += 2
        gc.player = Player.deserialise(data[offset:offset + pl_len])
        offset += pl_len
        gc.random_encounters = unpack_from('?', data, offset)[0]
        offset += 1
        cm_len = unpack_from('B', data, offset)[0]
        offset += 1
        gc.custom = Customisation.deserialise(data[offset:offset+cm_len])
        offset += cm_len
        return gc