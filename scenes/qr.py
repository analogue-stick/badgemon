from asyncio import Event

from ..scenes.scene import Scene
from ctx import Context
from ..config import ASSET_PATH
from events.input import ButtonDownEvent

class Qr(Scene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._exit = Event()

    def draw(self, ctx: Context):
        ctx.image_smoothing = 0
        ctx.image(ASSET_PATH+"qr.png", -120, -120, 240, 240)

    def handle_buttondown(self, event: ButtonDownEvent):
        self._exit.set()

    async def background_task(self):
        await self._exit.wait()
        await self.fade_to_scene(2)