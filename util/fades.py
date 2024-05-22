import math
from sys import implementation as _sys_implementation
if _sys_implementation.name != "micropython":
    from typing import Tuple
from ..util.animation import Animation, lerp
from ctx import Context

class FadeToShade(Animation):
    def __init__(self, colour: Tuple[float,float,float], fadein = False, *args, **kwargs) -> None:
        self._colour = colour
        self._fade = 0
        self._fadein = fadein
        super().__init__(*args, **kwargs)

    def _update(self, time: float) -> None:
        if self._fadein:
            self._fade = lerp(1,0,time)
        else:
            self._fade = lerp(0,1,time)
        return super()._update(time)
    
    def reset(self, fadein = False) -> None:
        self._fadein = fadein
        if self._fadein:
            self._fade = 1
        else:
            self._fade = 0
        return super().reset()
    
    def on_anim_start(self) -> None:
        self._update(0)
        return super().on_anim_start()

    def on_anim_end(self) -> None:
        self._update(1)
        return super().on_anim_end()

    def draw(self, ctx: Context):
        ctx.rgba(*self._colour, self._fade).rectangle(-120,-120,240,240).fill()

class BattleFadeToShade(FadeToShade):
    def draw(self, ctx: Context):
        ctx.rgb(*self._colour)
        for i in range(8):
            ctx.move_to(0,0)
            ctx.line_to(140*math.cos(math.pi/4*(i)),
                     140*math.sin(math.pi/4*(i)))
            ctx.line_to(140*math.cos(math.pi/4*(i+self._fade)),
                     140*math.sin(math.pi/4*(i+self._fade)))
            ctx.fill()