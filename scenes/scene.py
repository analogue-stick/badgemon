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
    def __init__(self, choice: ChoiceDialog, speech: SpeechDialog, animation_scheduler: AnimationScheduler, sm: 'SceneManager'):
        self.choice = choice
        self.speech = speech
        self.animation_scheduler = animation_scheduler
        self._fader = FadeToShade((1.0,1.0,1.0), length=200)
        self.sm = sm

    async def fade_to_scene(self, scene):
        end_event = Event()
        self._fader._colour = (0,0,0)
        self._fader.and_then(AnimationEvent(end_event))
        self.animation_scheduler.trigger(self._fader)
        await end_event.wait()
        self.sm.switch_scene(scene)

    def update(self, delta: float):
        pass

    def draw(self, ctx: Context):
        self._fader.draw(ctx)

    def scene_start(self):
        pass

    def scene_end(self):
        self.animation_scheduler.kill_animation()

    async def background_task(self):
        pass