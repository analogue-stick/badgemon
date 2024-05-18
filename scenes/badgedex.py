from asyncio import Event
import math

from ctx import Context

from ..util.animation import AnimLerp, AnimRandom, AnimSin

from ..scenes.scene import Scene
from ..game.mons import MonTemplate, mons_list
from ..util.misc import *
from ..game.constants import MonType, type_to_str

class Badgedex(Scene):
    def _set_wobble(self, x):
        self._arrow_wobble = x

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context.player.badgedex.find(0)
        self._gen_main_menu_dialog()
        self._current_mon = None
        self._mon_known = False
        self._exit = Event()
        self._arrow_wobble = 0
        self.animation_scheduler.trigger(AnimSin(AnimLerp(lambda x: self._set_wobble(x), end=4)))

    def _switch_to(self, mon: MonTemplate, mon_known = False):
        def f():
            self._current_mon = mon
            self._mon_known = mon_known
        return f

    def _gen_main_menu_dialog(self):
        self.choice.set_choices(
            (
                "Badgedex",
                    [(f"{m.id}: " + (m.name if f else "?????"), self._switch_to(m, f)) for m, f in zip(mons_list,self.context.player.badgedex.found)]
            )
        )

    def _show_detail(self):
        if self._current_mon is None:
            return
        if self._mon_known:
            self.speech.set_speech(self._current_mon.desc)
        else:
            self.speech.set_speech("You haven't found this mon yet!")
        self.speech.open()

    def handle_buttondown(self, event):
        if not (self.choice.is_open() or self.speech.is_open()):
            parent = event.button
            while parent.parent is not None and parent.group != "System":
                parent = parent.parent
            if parent.group == "System":
                if parent.name == "CANCEL" or parent.name == "LEFT":
                    self._exit.set()
                elif parent.name == "CONFIRM" or parent.name == "RIGHT":
                    self._show_detail()
                else:
                    self.choice.open()

    def _draw_type(self, ctx: Context):
        if self._mon_known:
            name = f"{type_to_str(self._current_mon.type1)}, {type_to_str(self._current_mon.type2)}"
        else:
            name = "?????, ?????"
        shrink_until_fit(ctx, name, 120, 40)
        ctx.text(name).fill()

    def _draw_arrow(self, ctx: Context):
        (ctx.move_to(-10, -100+self._arrow_wobble)
           .line_to(10, -100+self._arrow_wobble)
           .line_to(0, -115+self._arrow_wobble)
           .line_to(-10, -100+self._arrow_wobble)
           .fill())

    def draw(self, ctx: Context):
        super().draw(ctx)
        if not self._current_mon is None:
            draw_mon(ctx, self._current_mon.sprite if self._mon_known else "unknown", -64, -64, False, False, 4)
            name = (self._current_mon.name if self._mon_known else "?????")
            ctx.text_align = Context.CENTER
            ctx.text_baseline = Context.MIDDLE
            shrink_until_fit(ctx, name, 100, 60)
            ctx.gray(0).move_to(0,-80).text(name).fill()
            self._draw_type(ctx.gray(0.2).move_to(0,80))
        ctx.font_size = 30
        ctx.rotate(math.pi/2).move_to(0,-80).text("DESC.").fill()
        self._draw_arrow(ctx)
        ctx.rotate(math.pi).move_to(0,-80).text("EXIT").fill()
        self._draw_arrow(ctx)
        ctx.rotate(math.pi/2)

    async def background_task(self):
        if self.choice._state == "CLOSED":
            await self.choice.open_and_wait()
        await self._exit.wait()
        await self.fade_to_scene(2)