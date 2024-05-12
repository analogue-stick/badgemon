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

    def draw(self, ctx: Context):
        ctx.rgba(*self._colour, self._fade).rectangle(-120,-120,240,240).fill()