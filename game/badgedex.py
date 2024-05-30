from .mons import mons_list
from struct import pack, unpack_from, calcsize

class Badgedex:
    def __init__(self):
        self.found = [False]*len(mons_list)
    
    def find(self, index):
        self.found[index] = True
    
    def serialise(self):
        return pack(f'{len(self.found)}B', *self.found)

    @staticmethod
    def deserialise(data):
        b = Badgedex()
        b.found = [bool(unpack_from('B', data, m * calcsize("B"))[0]) for m in range(0, len(mons_list))]
        return b
    