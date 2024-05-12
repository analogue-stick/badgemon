from asyncio import Event
from ..util.fades import FadeToShade
from ..util.choice import ChoiceDialog
from ..util.speech import SpeechDialog
from ..util.animation import AnimationScheduler, AnimationEvent
from ctx import Context

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .scene_manager import SceneManager
except ImportError:
    pass

class Scene:
    def __init__(self, sm: 'SceneManager'):
        self.sm = sm
        self.choice = sm._choice
        self.speech = sm._speech
        self.animation_scheduler = sm._animation_scheduler
        self.context = sm._context
        self._fader = sm._fader
        self._scene_ready = Event()

    async def fade_to_scene(self, scene, *args, **kwargs):
        self._scene_ready.clear()
        end_event = Event()
        self._fader.reset()
        self._fader._colour = (0,0,0)
        self._fader.and_then(AnimationEvent(end_event))
        self.animation_scheduler.trigger(self._fader)
        await end_event.wait()
        self.sm.switch_scene(scene, *args, **kwargs)

    def _fadein(self):
        self._scene_ready.clear()
        self._fader.reset(fadein=True)
        self._fader._colour = (0,0,0)
        self._fader.and_then(AnimationEvent(self._scene_ready))
        self.animation_scheduler.trigger(self._fader)

    def update(self, delta: float):
        pass

    def draw(self, ctx: Context):
        self._draw_background(ctx)

    def scene_start(self):
        pass

    def scene_end(self):
        self.animation_scheduler.kill_animation()

    def _draw_background(self, ctx: Context):
        ctx.gray(0.9).rectangle(-120, -120, 240, 240).fill()

    async def background_task(self):
        await self._scene_ready.wait()