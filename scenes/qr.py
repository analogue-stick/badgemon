from asyncio import Event

from ..scenes.scene import Scene
from events.input import ButtonDownEvent
from system.eventbus import eventbus
from ctx import Context
from ..config import ASSET_PATH


class Qr(Scene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._exit = Event()

    def draw(self, ctx: Context):
        ctx.image_smoothing = 0
        ctx.image(ASSET_PATH+"qr.png", -120, -120, 240, 240)

    def _handle_buttondown(self, event: ButtonDownEvent):
        self._exit.set()

    def scene_start(self):
        eventbus.on(ButtonDownEvent, self._handle_buttondown, self.sm)
        return super().scene_start()

    def scene_end(self):
        eventbus.remove(ButtonDownEvent, self._handle_buttondown, self.sm)
        return super().scene_end()

    async def background_task(self):
        await self._exit.wait()
        await self.fade_to_scene(2)