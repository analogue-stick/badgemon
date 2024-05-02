from ..game.mons import mons_list

class Badgedex:
    def __init__(self):
        self.found = [False]*len(mons_list)
    
    def find(self, index):
        self.found[index] = True
    
    