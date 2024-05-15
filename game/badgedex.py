from .mons import mons_list
from struct import pack, iter_unpack

class Badgedex:
    def __init__(self):
        self.found = [False]*len(mons_list)
    
    def find(self, index):
        self.found[index] = True
    
    def serialise(self):
        return pack(f'{len(self.found)}?', *self.found)

    @staticmethod
    def deserialise(data):
        b = Badgedex()
        b.found = [m[0] for m in iter_unpack('?', data)]
        return b
    