import sys
if sys.implementation.name == "micropython":
    ASSET_PATH = "/apps/badgemon/assets/"
    SAVE_PATH = "/apps/badgemon/saves/"
else:
    ASSET_PATH = "./apps/badgemon/assets/"
    SAVE_PATH = "./apps/badgemon/saves/"