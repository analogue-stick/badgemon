import scenes.base_scene
from scenes import test_menu
import math


class MainMenuScene(scenes.base_scene.BaseScene):

    def __init__(self):
        super().__init__()
        self.channel = 0

    def setup(self):
        self._ctx.screen.fill(0)
        self._ctx.screen.pbitmap(test_menu, 0, 0)
        self._ctx.input_handler.button_callbacks[0] = self.button_press

    def button_press(self):
        self.channel = (self.channel + 1) % 3
    #
    # async def tick(self):
    #
    #     c = math.sin(self._frame/5) + 1
    #     if self.channel == 0:
    #         colour = int(c * 16) << 11
    #     elif self.channel == 1:
    #         colour = int(c * 32) << 5
    #     else:
    #         colour = int(c * 16)
    #
    #     self._ctx.screen.fill(colour)

