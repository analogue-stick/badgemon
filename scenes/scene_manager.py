import asyncio
from typing import Type
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
from ctx import Context



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
        self._fader = FadeToShade((1.0,1.0,1.0), length=200)
        self.overlays = [self._speech, self._choice, self._fader]
        self._animation_scheduler = AnimationScheduler()
        self._context = GameContext()
        self._scene = None
        self.switch_scene(MainMenu)

    def _emergency_save(self):
        '''
        Save data to disk as quickly as fucking possible
        '''
        pass

    def update(self, delta: float):
        self._animation_scheduler.update(delta)
        self._speech.update(delta)
        self._choice.update(delta)
        if self._scene is not None:
            self._scene.update(delta)

    def draw(self, ctx: Context):
        if self._scene is not None:
            self._scene.draw(ctx)
        super().draw(ctx)     

    async def background_task(self):
        while True:
            if self._scene is None:
                return
            await self._scene._scene_ready.wait()
            await self._scene.background_task()
            await asyncio.sleep(0.05)

    def switch_scene(self, scene: Type[Scene], *args, **kwargs):
        if self._scene is not None:
            self._scene.scene_end()
            del self._scene
        self._scene = scene
        if self._scene is None:
            self._animation_scheduler.kill_animation()
            self._emergency_save()
            eventbus.emit(RequestStopAppEvent(self))
            del self._animation_scheduler
            del self._choice
            del self._fader
            del self._speech
        else:
            self._scene: Scene = scene(self, *args, **kwargs)
            self._scene._fadein()
            self._scene.scene_start()
    