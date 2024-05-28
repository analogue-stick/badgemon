from asyncio import Event
import math

from ctx import Context

from ..util.animation import AnimLerp, AnimSin

from ..scenes.scene import Scene
from ..game.mons import MonTemplate, mons_list
from ..util.misc import *
from ..game.constants import type_to_str
from events.input import BUTTON_TYPES

class Badgedex(Scene):
    def _set_wobble(self, x):
        self._arrow_wobble = x

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._index = 0
        self._current_mon = mons_list[self._index]
        self._mon_known = self.context.player.badgedex.found[self._index]
        self._exit = Event()
        self._arrow_wobble = 0
        self.animation_scheduler.trigger(AnimSin(AnimLerp(lambda x: self._set_wobble(x), end=4)))

    def _show_detail(self):
        if self._current_mon is None:
            return
        self.speech.set_speech(self._current_mon.desc)
        self.speech.open()

    def handle_buttondown(self, event):
        if not (self.choice.is_open() or self.speech.is_open()):
            if BUTTON_TYPES["CANCEL"] in event.button or BUTTON_TYPES["LEFT"] in event.button:
                self._exit.set()
            elif BUTTON_TYPES["CONFIRM"] in event.button or BUTTON_TYPES["RIGHT"] in event.button:
                self._show_detail()
            elif BUTTON_TYPES["UP"] in event.button:
                self._index =  (self._index - 1 + len(mons_list)) % len(mons_list)
                self._current_mon = mons_list[self._index]
                self._mon_known = self.context.player.badgedex.found[self._index]
            elif BUTTON_TYPES["DOWN"] in event.button:
                self._index =  (self._index + 1 + len(mons_list)) % len(mons_list)
                self._current_mon = mons_list[self._index]
                self._mon_known = self.context.player.badgedex.found[self._index]

    def _draw_arrow(self, ctx: Context):
        (ctx.move_to(-10, -100+self._arrow_wobble)
           .line_to(10, -100+self._arrow_wobble)
           .line_to(0, -115+self._arrow_wobble)
           .line_to(-10, -100+self._arrow_wobble)
           .fill())

    def draw(self, ctx: Context):
        super().draw(ctx)
        ctx.text_align = Context.CENTER
        ctx.text_baseline = Context.MIDDLE
        if not self._current_mon is None:
            draw_mon(ctx, self._current_mon.sprite, -64, -64, False, False, 4)
            
            name = (self._current_mon.name)
            shrink_until_fit(ctx, name, 100, 60)
            ctx.gray(0).move_to(0,-80).text(name).fill()

            index = f"{self._index}."
            ctx.font_size = 20
            ctx.gray(0).move_to(0,-105).text(index).fill()
            
            types = f"{type_to_str(self._current_mon.type1)}, {type_to_str(self._current_mon.type2)}"
            shrink_until_fit(ctx, types, 120, 40)
            ctx.gray(0.2).move_to(0,75).text(types).fill()
            
            found = "Found" if self._mon_known else "Not Found"
            ctx.font_size = 20
            if self._mon_known:
                ctx.rgb(0.1,0.6,0.1)
            else:
                ctx.rgb(0.6,0.1,0.1)
            ctx.move_to(0,100).text(found).fill()
        ctx.font_size = 30
        ctx.gray(0)
        ctx.rotate(math.pi/2).move_to(0,-80).text("DESC.").fill()
        self._draw_arrow(ctx)
        ctx.rotate(math.pi).move_to(0,-80).text("EXIT").fill()
        self._draw_arrow(ctx)
        ctx.rotate(math.pi/2)

    async def background_task(self):
        await self._exit.wait()
        await self.fade_to_scene(2)