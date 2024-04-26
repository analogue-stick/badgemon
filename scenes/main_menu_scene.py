import scenes.base_scene
import math


class MainMenuScene(scenes.base_scene.BaseScene):

    def setup(self):
        self._ctx.screen.fill(0b11111_000000_00000)

    async def tick(self):
        r = int((math.sin(self._frame/5) + 1) * 16)
        colour = r << 11
        self._ctx.screen.fill(colour)

