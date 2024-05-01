import asyncio
import display
import gc
import math

from system.eventbus import eventbus
from events.input import ButtonDownEvent

from ctx import Context

MAX_LINE_WIDTH = 200
BOX_WIDTH = 200
BOX_HEIGHT = 40

class SpeechDialog:
    def __init__(self, app, speech: str):
        self.speech = speech
        self.lines = []
        self.app = app
        self.open = False
        self.state = "CLOSED"
        self.current_line = 1
        self.current_line_visually = 1

    def update(self, delta):
        if self.open:
            if self.state == "CLOSED":
                self.state = "OPENING"
                self.opened_amount = 0.0
                self.lines = []
                self.current_line = 1
                self.current_line_visually = 1
                eventbus.on(ButtonDownEvent, self._handle_buttondown, self.app)
            if self.state == "OPENING":
                if self.opened_amount > 0.99:
                    self.opened_amount = 1.0
                    self.state = "OPEN"
                    return
                weight = math.pow(0.8, (delta/10000))
                self.opened_amount = (self.opened_amount * (weight)) + (1-weight)
            elif self.state == "CLOSING":
                if self.opened_amount < 0.01:
                    self.opened_amount = 0.0
                    self.state = "CLOSED"
                    self.open = False
                    self.lines = []
                    return
                weight = math.pow(0.8, (delta/10000))
                self.opened_amount = self.opened_amount * weight
            if self.current_line_visually != self.current_line:
                weight = math.pow(0.8, (delta/10000))
                self.current_line_visually = (self.current_line_visually * (weight)) + (self.current_line * (1-weight))

    def draw_focus_plane(self, ctx, height):
        ctx.rgba(0.5, 0.5, 0.5, 0.5).rectangle(-120, (-BOX_HEIGHT)*height, 240, (BOX_HEIGHT*2)*height).fill()
        col = ctx.rgba(0.2, 0.2, 0.2, 0.5)
        col.move_to(-120,(-BOX_HEIGHT)*height).line_to(120,(-BOX_HEIGHT)*height).stroke()
        col.move_to(-120,(BOX_HEIGHT)*height).line_to(120,(BOX_HEIGHT)*height).stroke()
    def draw_text(self, ctx, line: str, ypos: int):
        ctx.gray(0).move_to(0, ypos).text(line)

    def draw(self, ctx):
        if self.open:
            ctx.text_baseline = Context.MIDDLE
            ctx.text_align = Context.CENTER
            if not self.lines:
                line = ""
                for word in self.speech.split():
                    if ctx.text_width(line+" "+word) < MAX_LINE_WIDTH:
                        line = line + " " + word
                    else:
                        self.lines.append(line)
                        line = word
                if line != "":
                    self.lines.append(line)
                if len(self.lines) == 0:
                    self._cleanup()
                    return
                elif len(self.lines) == 1:
                    self.current_line = 0
                    self.current_line_visually = 0
                elif len(self.lines) == 2:
                    self.current_line = 0.5
                    self.current_line_visually = 0.5
            self.draw_focus_plane(ctx, self.opened_amount)
            clip = ctx.rectangle(-120, (-BOX_HEIGHT)*self.opened_amount, 240, (BOX_HEIGHT*2)*self.opened_amount).clip()
            for i, line in enumerate(self.lines):
                ypos = (i-self.current_line_visually)*ctx.font_size
                self.draw_text(clip, line, ypos)
            
    def _handle_buttondown(self, event: ButtonDownEvent):
        if len(self.lines) < 4:
            self._cleanup()
            return
        if self.current_line >= len(self.lines) -1:
            self._cleanup()
            return
        else:
            self.current_line += 1

    def _cleanup(self):
        eventbus.remove(ButtonDownEvent, self._handle_buttondown, self.app)
        self.state = "CLOSING"

class SpeechExample():
    def __init__(self):
        self.speech = SpeechDialog(
            app=self,
            speech="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        )
        eventbus.on(ButtonDownEvent, self._handle_buttondown, self)

    def _handle_buttondown(self, event: ButtonDownEvent):
        if not self.speech.open:
            self.speech.open = True

    def update(self, delta):
        self.speech.update(delta)

    async def background_update(self):
        while True:
            await asyncio.sleep(1)
            print("fps:", display.get_fps(), f"mem used: {gc.mem_alloc()}, mem free:{gc.mem_free()}")

    def draw_background(self, ctx):
        ctx.gray(0.9).rectangle(-120, -120, 240, 240).fill()

    def draw(self, ctx):
        self.draw_background(ctx)
        ctx.font_size = 25
        self.speech.draw(ctx)
