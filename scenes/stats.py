from asyncio import Event
import math
from ctx import Context
from ..game.mons import Mon
from ..util.animation import AnimLerp, AnimSin, lerp
from ..game.constants import type_to_str, status_to_str, STAT_HP, stat_names

from ..scenes.scene import Scene
from ..util.misc import draw_mon, shrink_until_fit
from events.input import BUTTON_TYPES

PAGES = 4

class Stats(Scene):
    def _set_wobble(self, x):
        self._arrow_wobble = x

    def __init__(self, *args, mon: Mon = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.mon = mon
        self.page = 0
        self._exit = Event()
        self._arrow_wobble = 0
        self.animation_scheduler.trigger(AnimSin(AnimLerp(lambda x: self._set_wobble(x), end=4)))

    def redirect(self):
        if self.mon is None:
            return 2
        return None
    
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
        ctx.rotate(-math.pi/2).move_to(0,-80).gray(0).text("EXIT").fill()
        self._draw_arrow(ctx)
        ctx.rotate(math.pi/2)
        if self.page == 0:
            draw_mon(ctx, self.mon.template.sprite, -64, -64, False, False, 4)

            name = (self.mon.nickname)
            shrink_until_fit(ctx, name, 120, 60)
            ctx.gray(0).move_to(0,-80).text(name).fill()

            status = status_to_str(self.mon.status).capitalize()
            if status == "":
                status = "No Status"
            shrink_until_fit(ctx, status, 100, 35)
            ctx.gray(0.2).move_to(0,70).text(status).fill()

            hp = f"HP: {self.mon.hp}"
            if self.mon.fainted:
                hp = "Fainted"
            ctx.font_size = 25
            gradient = self.mon.hp / self.mon.stats[STAT_HP]
            ctx.rgb(lerp(time=gradient, start=0.6, end=0.1), lerp(time=gradient, start=0.1, end=0.6),0.1)
            ctx.move_to(0,90).text(hp).fill()
        elif self.page == 1:
            name = "STATS"
            shrink_until_fit(ctx, name, 100, 60)
            ctx.gray(0).move_to(0,-80).text(name).fill()
            for i in range(len(self.mon.stats)+2):
                ctx.font_size = 20
                if i < len(self.mon.stats):
                    stat = f"{stat_names[i]}: {self.mon.stats[i]}"
                elif i == len(self.mon.stats):
                    stat = f"Evasion: {self.mon.evasion}"
                elif i == len(self.mon.stats) + 1:
                    stat = f"Accuracy: {self.mon.accuracy}"
                ctx.gray(0).move_to(0,-60+(20*i)).text(stat)
        elif self.page == 2:
            name = "MOVES"
            shrink_until_fit(ctx, name, 100, 60)
            ctx.gray(0).move_to(0,-80).text(name).fill()
            for i in range(len(self.mon.moves)):
                ctx.font_size = 20
                move = f"{self.mon.moves[i].name} \n (PP: {self.mon.pp[i]})"
                ctx.gray(0).move_to(0,-60+(45*i)).text(move)
        elif self.page == 3:
            name = "LEVEL"
            shrink_until_fit(ctx, name, 100, 60)
            ctx.gray(0).move_to(0,-80).text(name).fill()
            lvl = str(self.mon.level)
            shrink_until_fit(ctx, lvl, 60, 200)
            ctx.gray(0).move_to(0,0).text(lvl).fill()
            ctx.font_size = 20
            xp = f"XP: {self.mon.xp}"
            ctx.gray(0).move_to(0,80).text(xp).fill()
            next = self.mon.level+1
            next = next*next*next
            xp = f"Next LVL: {next}"
            ctx.gray(0).move_to(0,65).text(xp).fill()


    def handle_buttondown(self, event):
        if BUTTON_TYPES["CANCEL"] in event.button or BUTTON_TYPES["LEFT"] in event.button:
            self._exit.set()
        elif BUTTON_TYPES["DOWN"] in event.button or BUTTON_TYPES["CONFIRM"] in event.button:
            self.page = (self.page + 1 + PAGES) % PAGES
        elif BUTTON_TYPES["UP"] in event.button or BUTTON_TYPES["RIGHT"] in event.button:
            self.page = (self.page - 1 + PAGES) % PAGES
    

    async def background_task(self):
        await self._exit.wait()
        await self.fade_to_scene(2)