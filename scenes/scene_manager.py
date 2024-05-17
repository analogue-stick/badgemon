import asyncio
import gc
import sys
from typing import Type

from ..scenes.field import Field
from ..game.game_context import GameContext
from ..util.fades import FadeToShade
from ..scenes.main_menu import MainMenu
from ..scenes.scene import Scene
from ..util.choice import ChoiceDialog
from ..util.speech import SpeechDialog
from .battle import Battle
from system import eventbus
from system.scheduler.events import RequestStopAppEvent
from ..util.animation import AnimationScheduler
from app import App
from ctx import Context, _img_cache, _wasm
from ..config import ASSET_PATH, SAVE_PATH

SCENE_LIST = [MainMenu, None, Field, Battle]

class SceneManager(App):
    def __init__(self):
        super().__init__()
        self._speech = SpeechDialog(
            app=self,
            speech="Scene Testing!"
        )
        self._choice = ChoiceDialog(
            app=self,
        )
        self._cache_sprites()
        self._fader = FadeToShade((1.0,1.0,1.0), length=200)
        self.overlays = [self._speech, self._choice, self._fader]
        self._animation_scheduler = AnimationScheduler()
        self._scene = None
        self._attempt_load()
        if self._context == None:
            self._context = GameContext()
            self.switch_scene(0)
        else:
            self.switch_scene(0)

    def _cache_sprites(self):
        paths = [f"{ASSET_PATH}mons/mon-{x}.png" for x in range(5)]
        for path in paths:
            if not path in _img_cache:
                buf = open(path, "rb").read()
                _img_cache[path] = _wasm.stbi_load_from_memory(buf)

    def _attempt_save(self):
        '''
        Save data to disk
        '''
        data = self._context.serialise()
        with open(SAVE_PATH+"sav.dat", "wb") as f:
            f.write(data)

    def _attempt_load(self):
        '''
        Load data from disk
        '''
        try:
            with open(SAVE_PATH+"sav.dat", "rb") as f:
                data = f.read(None)
                self._context = GameContext.deserialise(data)
        except IOError:
            self._context = None

    def update(self, delta: float):
        try:
            self._animation_scheduler.update(delta)
            self._speech.update(delta)
            self._choice.update(delta)
            if self._scene is not None:
                self._scene.update(delta)
        except Exception as e:
            print("UPDATE FAIL")
            print(e)
            sys.exit()

    def draw(self, ctx: Context):
        try:
            if self._scene is not None:
                self._scene.draw(ctx)
            super().draw(ctx)
        except Exception as e:
            print("DRAW FAIL")
            print(e)
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
                print(e)
                sys.exit()
            await asyncio.sleep(0.05)

    def switch_scene(self, scene: int, *args, **kwargs):
        if self._scene is not None:
            self._scene.scene_end()
        if scene is None:
            self._animation_scheduler.kill_animation()
            self._emergency_save()
            eventbus.emit(RequestStopAppEvent(self))
            del self._animation_scheduler
            del self._choice
            del self._fader
            del self._speech
        else:
            print("LOAD SCENE")
            print((SCENE_LIST[scene]))
            self._scene: Scene = (SCENE_LIST[scene])(self, *args, **kwargs)
            gc.collect()
            print(f"mem used: {gc.mem_alloc()}, mem free:{gc.mem_free()}")
            self._scene._fadein()
            print("scene start")
            self._scene.scene_start()
    