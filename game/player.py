from typing import List, Tuple
from game import mons, items


class Player:
    def __init__(self):
        badgemon: List[mons.Mon] = []
        inventory: List[Tuple[items.Item, int]] = []
