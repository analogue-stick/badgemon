import sys, os
if sys.implementation.name == "micropython":
    apps = os.listdir("/apps")
    path = ""
    for app in apps:
        if app.startswith("analogue_stick_badgemon"):
            path = "/apps/" + app
    ASSET_PATH = path + "/assets/"
    SAVE_PATH = "/bmon_gr_saves/"
else:
    ASSET_PATH = "./apps/badgemon/assets/"
    SAVE_PATH = "./apps/badgemon/saves/"