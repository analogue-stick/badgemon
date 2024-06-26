import asyncio
import gc
import os
import sys

from ..scenes.scene import Scene
from ..scenes.main_menu import MainMenu
from ..scenes.field import Field
from ..scenes.battle import Battle
from ..scenes.qr import Qr
from ..scenes.badgedex import Badgedex
from ..scenes.onboarding import Onboarding
from ..scenes.levelup import LevelUp
from ..scenes.stats import Stats
from ..game.game_context import GameContext, VERSION
from ..util.fades import FadeToShade, BattleFadeToShade
from ..util.choice import ChoiceDialog
from ..util.speech import SpeechDialog
from ..util.misc import dump_exception, path_isdir
from ..game.migrate import conversion
from ..protocol.bluetooth import BluetoothDevice
from system.eventbus import eventbus
from events.input import Buttons
from system.scheduler.events import RequestStopAppEvent
from ..util.animation import AnimationScheduler
from app import App
from ctx import Context
from ..config import SAVE_PATH

from ..util.text_box import TextExample, TextDialog

SCENE_LIST = [MainMenu, Onboarding, Field, Battle, Qr, Badgedex, TextExample, LevelUp, Stats]

def dump_exception(e: Exception):
    if sys.implementation.name == "micropython":
        sys.print_exception(e)
    else:
        import traceback
        traceback.print_exception(None, e, None)

class SceneManager(App):
    def __init__(self):
        super().__init__()
        try:
            os.mkdir("bmon_gr_saves")
        except Exception as e:
            dump_exception(e)
        self._speech = SpeechDialog(
            app=self,
            speech="Scene Testing!"
        )
        self._choice = ChoiceDialog(
            app=self,
        )
        self._fader = FadeToShade((1.0,1.0,1.0), length=200)
        self._battle_fader = BattleFadeToShade((0.0,0.0,0.0), length=1000)
        self._text = TextDialog(self, "Jim")
        self.overlays = [self._speech, self._choice, self._text, self._fader, self._battle_fader]
        self._animation_scheduler = AnimationScheduler()
        self._button_states = Buttons(self)
        self._scene = None
        self._attempt_load()
        if self._context == None:
            self._context = GameContext()
            self.switch_scene(1)
        else:
            self.switch_scene(0)
        self._bt = BluetoothDevice()
        self.connection_task = None

    def _attempt_save(self):
        '''
        Save data to disk
        '''
        data = self._context.serialise()
        if not path_isdir(SAVE_PATH):
            os.mkdir(SAVE_PATH)
        with open(SAVE_PATH+"sav.dat", "wb") as f:
            f.write(data)

    def _attempt_load(self):
        '''
        Load data from disk
        '''
        try:
            while True:
                f = open(SAVE_PATH+"sav.dat", "rb")
                if f.read(4) != b'BGGR':
                    print("FILE UNRECOGNISED")
                    self._context = None
                    return
                version = int.from_bytes(f.read(1), 'little')
                if version != VERSION:
                    if version > VERSION:
                        print("TOO NEW!")
                        self._context = None
                        return
                    elif version in conversion:
                        f.close()
                        conversion[version]()
                        continue
                    print("UNKNOWN VERSION")
                    self._context = None
                    return
                f.close()
                with open(SAVE_PATH+"sav.dat", "rb") as f:
                    f.seek(6)
                    data = f.read()
                    self._context = GameContext.deserialise(data)
                    return
        except Exception as e:
            dump_exception(e)
            self._context = None

    def update(self, delta: float):
        try:
            self._animation_scheduler.update(delta)
            self._speech.update(delta)
            self._choice.update(delta)
            self._text.update(delta)
            if self._scene is not None:
                self._scene.update(delta)
        except Exception as e:
            print("UPDATE FAIL")
            dump_exception(e)
            sys.exit()

    def draw(self, ctx: Context):
        try:
            if self._scene is not None:
                self._scene.draw(ctx)
            super().draw(ctx)
        except Exception as e:
            print("DRAW FAIL")
            dump_exception(e)
            sys.exit()

    async def background_task(self):
        while True:
            if self._scene is None:
                return
            print("AWAIT READY")
            await self._scene._scene_ready.wait()
            print("AWAIT BACKGROUND TASK")
            try:
                await self._scene.background_task()
            except Exception as e:
                print("BACKGROUND FAIL")
                dump_exception(e)
                sys.exit()
            self._choice.close()
            self._speech.close()
            self._text.close()
            await asyncio.sleep(0.05)

    def switch_scene(self, scene: int, *args, **kwargs):
        if self._scene is not None:
            self._scene.scene_end()
        if scene is None:
            self._animation_scheduler.kill_animation()
            self._attempt_save()
            eventbus.emit(RequestStopAppEvent(self))
            del self._animation_scheduler
            del self._choice
            del self._fader
            del self._battle_fader
            del self._speech
            del self._text
        else:
            self._choice.close()
            self._speech.close()
            self._text.close()
            while scene is not None:
                print("LOAD SCENE")
                print((SCENE_LIST[scene]))
                self._scene: Scene = (SCENE_LIST[scene])(self, *args, **kwargs)
                gc.collect()
                print(f"mem used: {gc.mem_alloc()}, mem free:{gc.mem_free()}")
                scene = self._scene.redirect()
            self._scene._fadein()
            self._battle_fader.reset()
            print("scene start")
            self._scene.scene_start()

