"""
abstraction of choice

To be replaced by a GUI version on the badges
"""

import os
import time
from typing import List, Tuple, Union
import keyboard

ChoiceTree = List[Tuple[str, Union['ChoiceTree', int]]]

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

def make_choice(start: str, choice_tree: ChoiceTree) -> int:
    """
    Supply a title and a choice tree, the strings being the choices possible.
    To create another submenu use another choice tree, otherwise specify a unique integer.
    The integer must be unique over the entire choice tree, and not 0.
    0 is returned if the user exited.
    """
    os.system("stty -echo")
    print("\r"+LINE_CLEAR+start)
    choice = 0
    while True:
        name = choice_tree[choice][0]
        print("\r"+LINE_CLEAR+name, end="")
        time.sleep(0.1)
        key = keyboard.read_key()
        if key == "a":
            os.system("stty echo")
            print("\r"+LINE_CLEAR+LINE_UP+LINE_CLEAR, end="")
            return 0
        if key == "d":
            next = choice_tree[choice][1]
            if type(next) == int:
                os.system("stty echo")
                print("\r"+LINE_CLEAR+LINE_UP+LINE_CLEAR, end="")
                return next
            os.system("stty echo")
            choice = make_choice(name,next)
            if choice != 0:
                print(LINE_UP+LINE_CLEAR, end="")
                return choice
            os.system("stty -echo")
        if key == "w":
            choice = (choice - 1 + len(choice_tree)) % len(choice_tree)
        if key == "s":
            choice = (choice + 1 + len(choice_tree)) % len(choice_tree)

if __name__ == "__main__":
    choice_tree = [("thing 1", 1),("thing 2", 2),("thing 3", 3),("more",[("thing 41", 41),("thing 42", 42)])]
    choice = make_choice("CHOOSE:", choice_tree)
    print("choice was:", choice)
        