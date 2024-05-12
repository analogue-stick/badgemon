from ..game.mons import Mon, mons_list
from ..game.items import items_list
from ..game.player import Player

potion = items_list[0]
mon_template1 = mons_list[0]
mon_template2 = mons_list[1]
mon1 = Mon(mon_template1, 5).set_nickname("small guy")
mon2 = Mon(mon_template2, 17).set_nickname("mr. 17")
mon3 = Mon(mon_template1, 17).set_nickname("David")
mon4 = Mon(mon_template2, 33).set_nickname("large individual")
mon5 = Mon(mon_template1, 100).set_nickname("biggest dude")

class GameContext:
    def __init__(self):
        self.player = Player("Scarlett", [mon2, mon3], [mon4], [(potion, 2)])