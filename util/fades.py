from typing import Tuple
from ..util.animation import Animation, lerp
from ctx import Context

class FadeToShade(Animation):
    def __init__(self, colour: Tuple[float,float,float], *args, **kwargs) -> None:
        self._colour = colour
        self._fade = 0
        super().__init__(*args, **kwargs)

    def _update(self, time: float) -> None:
        self._fade = lerp(0,1,time)
        return super()._update(time)
    
    def draw(self, ctx: Context):
        ctx.rgba(*self._colour, self._fade).rectangle(-120,-120,240,240).fill()