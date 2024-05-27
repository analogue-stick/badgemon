from config import SAVE_PATH

def save_1to2():
    with open(SAVE_PATH+"sav.dat", "rb") as f:
        data = f.read(None)

conversion = {1: save_1to2}
