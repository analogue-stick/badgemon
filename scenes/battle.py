from system.eventbus import eventbus
from events.input import ButtonDownEvent
from ..util.speech import SpeechDialog

from ..config import *

from ..game.mons import Mon, mons_list

def draw_mon(ctx, monIndex, x, y, flipx, flipy, scale):
    ctx.image_smoothing = 0
    if flipx:
        xscale = -1
    else:
        xscale = 1
    if flipy:
        yscale = -1
    else:
        yscale = 1
    ctx.scale(xscale,yscale)
    ctx.translate(x, y)
    ctx.image(ASSET_PATH+f"mons/mon-{monIndex}.png", 0, 0, 32*scale, 32*scale)
    ctx.translate(-x,-y)
    ctx.scale(xscale,yscale)

class Battle():
    def __init__(self, this_mon: Mon, that_mon: Mon, debug=False):
        if debug:
            self.this_mon = Mon(mons_list[0], 17).set_nickname("mr. 17")
            self.that_mon = Mon(mons_list[1], 5).set_nickname("small guy")
        else:    
            self.this_mon = this_mon
            self.that_mon = that_mon
        self.speech = SpeechDialog(
            app=self,
            speech="Battle Testing!"
        )
        eventbus.on(ButtonDownEvent, self._handle_buttondown, self)

    def _handle_buttondown(self, event: ButtonDownEvent):
        if not self.speech.open:
            self.speech.open = True

    def update(self, delta):
        self.speech.update(delta)

    async def background_update(self):
        pass

    def draw_background(self, ctx):
        ctx.gray(0.9).rectangle(-120, -120, 240, 240).fill()

    def draw_mons(self, ctx):
        draw_mon(ctx, self.that_mon.template.sprite, 2, -(32*3), False, False, 3)
        draw_mon(ctx, self.this_mon.template.sprite, 2, 0, True, False, 3)

    def draw(self, ctx):
        self.draw_background(ctx)
        self.draw_mons(ctx)
        self.speech.draw(ctx)
