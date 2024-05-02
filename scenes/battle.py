from system.eventbus import eventbus
from events.input import ButtonDownEvent
from ..util.speech import SpeechDialog
from ..util.misc import *

from ..config import *

from ..game.mons import Mon, mons_list
from ctx import Context

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
        draw_mon(ctx, self.that_mon.template.sprite, 0, -(32*3), False, False, 3)
        draw_mon(ctx, self.this_mon.template.sprite, 0, 0, True, False, 3)

    def draw_health(self, ctx: Context):
        x = 10
        y = 30
        width  = 85 
        radius = 10
        border = 3
        
        other_health = (self.that_mon.hp / self.that_mon.template.base_hp)
        us_health = (self.this_mon.hp / self.this_mon.template.base_hp)

        ctx.gray(0)
        ctx.round_rectangle(-x-width-border, -y-border, width+border*2, radius+border*2, radius).fill()
        ctx.round_rectangle(x-border, y-border-radius, width+border*2, radius+border*2, radius).fill()
        ctx.rgb((0.7*(1-other_health))+0.2,(0.7*other_health)+0.2,0.2)
        ctx.round_rectangle(-x-(width*other_health), -y, width * other_health, radius, radius).fill()
        ctx.rgb((0.7*(1-us_health))+0.2,(0.7*us_health)+0.2,0.2)
        ctx.round_rectangle(x, y-radius, width*us_health, radius, radius).fill()

    def draw_names(self, ctx: Context):
        x = 10
        y = 45

        ctx.gray(0)
        ctx.font_size = 20
        ctx.text_baseline = Context.MIDDLE
        ctx.text_align = Context.RIGHT
        ctx.move_to(-x,-y).text(self.that_mon.nickname)
        ctx.text_align = Context.LEFT
        ctx.move_to(x,y).text(self.this_mon.nickname)

    def your_turn(self, ctx: Context):
        ctx.text_baseline = Context.MIDDLE
        ctx.text_align = Context.CENTER
        ctx.font_size = 24
        ctx.rgb(0.8,0.4,0.2)
        gap = 0.165

        ctx.rotate(gap*-1.5)
        ctx.move_to(0, -100).text("Y")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("O")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("U")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("R")

        ctx.move_to(0, 100).text("T")
        ctx.rotate(-gap)
        ctx.move_to(0, 100).text("U")
        ctx.rotate(-gap)
        ctx.move_to(0, 100).text("R")
        ctx.rotate(-gap)
        ctx.move_to(0, 100).text("N")
        ctx.rotate(gap*1.5)
        ctx.line_width = 5
        ctx.arc(0,0,115,0,6.28,0).stroke()

    def their_turn(self, ctx: Context):
        ctx.text_baseline = Context.MIDDLE
        ctx.text_align = Context.CENTER
        ctx.font_size = 24
        ctx.rgb(0.2,0.4,0.8)
        gap = 0.165

        ctx.rotate(gap*-2)
        ctx.move_to(0, -100).text("T")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("H")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("E")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("I")
        ctx.rotate(gap)
        ctx.move_to(0, -100).text("R")
        ctx.rotate(gap*-0.5)

        ctx.move_to(0, 100).text("T")
        ctx.rotate(-gap)
        ctx.move_to(0, 100).text("U")
        ctx.rotate(-gap)
        ctx.move_to(0, 100).text("R")
        ctx.rotate(-gap)
        ctx.move_to(0, 100).text("N")
        ctx.rotate(gap*1.5)
        ctx.line_width = 5
        ctx.arc(0,0,115,0,6.28,0).stroke()

    def draw(self, ctx):
        ctx.line = ctx_line
        self.draw_background(ctx)
        self.draw_mons(ctx)
        self.draw_health(ctx)
        self.draw_names(ctx)
        self.their_turn(ctx)
        self.speech.draw(ctx)
