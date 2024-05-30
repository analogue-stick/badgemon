from ..config import SAVE_PATH

VERSION_LOC = 4

def save_1to2():
    with open(SAVE_PATH+"sav.dat", "rb") as f:
        data = bytearray(f.read(None))
        data[VERSION_LOC] = 2
    with open(SAVE_PATH+"sav.dat", "wb") as f:
        f.write(data)

def save_2to3():
    with open(SAVE_PATH+"sav.dat", "rb") as f:
        data = bytearray(f.read(None))
        data[VERSION_LOC] = 3
        data.extend(b'\14\09bmon_grey\09mid_green\00')
    with open(SAVE_PATH+"sav.dat", "wb") as f:
        f.write(data)

conversion = {1: save_1to2,
              2: save_2to3}
