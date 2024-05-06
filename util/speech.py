import asyncio
import math

from system.eventbus import eventbus
from events.input import ButtonDownEvent
from app import App

from ctx import Context

MAX_LINE_WIDTH = 200
BOX_WIDTH = 200
BOX_HEIGHT = 40

class SpeechDialog:
    def __init__(self, app: App, speech: str):
        self._speech = speech
        self._lines: list[str] = []
        self._app = app
        self._open = False
        self._state = "CLOSED"
        self._current_line = 1.0
        self._current_line_visually = 1.0
        self._opened_amount = 0.0
        self._ready_event = asyncio.Event()
        self._ready_event.set()

    def is_open(self) -> bool:
        return self._open
    
    def open(self):
        if not self.is_open():
            self._open = True
            self._ready_event.clear()
    
    def close(self):
        if self.is_open():
            self._cleanup()

    async def write(self, s):
        await self._ready_event.wait()
        self.set_speech(s)
        self.open()
        await self._ready_event.wait()

    def set_speech(self, speech: str):
        self._speech = speech
        self._lines = []
        self._current_line = 1.0
        self._current_line_visually = 1.0

    def _goto_start(self):
        if len(self._lines) == 0:
            self._cleanup()
        elif len(self._lines) == 1:
            self._current_line = 0.0
            self._current_line_visually = 0.0
        elif len(self._lines) == 2:
            self._current_line = 0.5
            self._current_line_visually = 0.5

    def update(self, delta: float):
        if self.is_open():
            if self._state == "CLOSED":
                self._state = "OPENING"
                self._opened_amount = 0.0
                self._goto_start()
                eventbus.on(ButtonDownEvent, self._handle_buttondown, self._app)
            if self._state == "OPENING":
                if self._opened_amount > 0.99:
                    self._opened_amount = 1.0
                    self._state = "OPEN"
                    return
                weight = math.pow(0.8, (delta/10))
                self._opened_amount = (self._opened_amount * (weight)) + (1-weight)
            elif self._state == "CLOSING":
                if self._opened_amount < 0.01:
                    self._opened_amount = 0.0
                    self._state = "CLOSED"
                    self._open = False
                    self._lines = []
                    self._ready_event.set()
                    return
                weight = math.pow(0.8, (delta/10))
                self._opened_amount = self._opened_amount * weight
            if self._current_line_visually != self._current_line:
                weight = math.pow(0.8, (delta/10))
                self._current_line_visually = (self._current_line_visually * (weight)) + (self._current_line * (1-weight))

    def _draw_focus_plane(self, ctx: Context, height: float):
        ctx.rgba(0.5, 0.5, 0.5, 0.5).rectangle(-120, (-BOX_HEIGHT)*height, 240, (BOX_HEIGHT*2)*height).fill()
        col = ctx.rgba(0.2, 0.2, 0.2, 0.5)
        col.move_to(-120,(-BOX_HEIGHT)*height).line_to(120,(-BOX_HEIGHT)*height).stroke()
        col.move_to(-120,(BOX_HEIGHT)*height).line_to(120,(BOX_HEIGHT)*height).stroke()
    def _draw_text(self, ctx: Context, line: str, ypos: int):
        ctx.gray(0).move_to(0, ypos).text(line)

    def draw(self, ctx: Context):
        if self.is_open():
            ctx.save()
            ctx.font_size = 25
            ctx.text_baseline = Context.MIDDLE
            ctx.text_align = Context.CENTER
            if not self._lines:
                line = ""
                for word in self._speech.split():
                    if ctx.text_width(line+" "+word) < MAX_LINE_WIDTH:
                        line = line + " " + word
                    else:
                        self._lines.append(line)
                        line = word
                if line != "":
                    self._lines.append(line)
                self._goto_start()
            self._draw_focus_plane(ctx, self._opened_amount)
            clip = ctx.rectangle(-120, (-BOX_HEIGHT)*self._opened_amount, 240, (BOX_HEIGHT*2)*self._opened_amount).clip()
            for i, line in enumerate(self._lines):
                ypos = (i-self._current_line_visually)*ctx.font_size
                self._draw_text(clip, line, ypos)
            ctx.restore()
            
    def _handle_buttondown(self, event: ButtonDownEvent):
        if len(self._lines) < 4:
            self._cleanup()
            return
        if self._current_line >= len(self._lines) -1:
            self._cleanup()
            return
        else:
            self._current_line += 1

    def _cleanup(self):
        eventbus.remove(ButtonDownEvent, self._handle_buttondown, self._app)
        self._state = "CLOSING"

class SpeechExample(App):
    def __init__(self):
        self._speech = SpeechDialog(
            app=self,
            speech="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        )
        eventbus.on(ButtonDownEvent, self._handle_buttondown, self)

    def _handle_buttondown(self, event: ButtonDownEvent):
        self._speech.open()

    def update(self, delta: float):
        self._speech.update(delta)

    def _draw_background(self, ctx: Context):
        ctx.gray(0.9).rectangle(-120, -120, 240, 240).fill()

    def draw(self, ctx: Context):
        self._draw_background(ctx)
        self._speech.draw(ctx)
