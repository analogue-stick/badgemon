from ..scenes.scene import Scene
from ..util.choice import ChoiceDialog
from ..util.speech import SpeechDialog
from .battle import Battle
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
            header="SCENE?!"
        )
        self.overlays = [self._speech, self._choice]
        self._animation_scheduler = AnimationScheduler()
        self._scene: Scene = Battle(None, True, self._choice, self._speech, self._animation_scheduler, self)

    def update(self, delta: float):
        self._animation_scheduler.update(delta)
        self._speech.update(delta)
        self._choice.update(delta)
        self._scene.update(delta)

    def draw(self, ctx: Context):
        self._scene.draw(ctx)        

    async def background_task(self):
        while True:
            next_scene = await self._scene.background_task()
            self.switch_scene(next_scene)

    def switch_scene(self, scene):
        self._scene.scene_end()
        self._scene = scene
        self._scene.scene_start()
    