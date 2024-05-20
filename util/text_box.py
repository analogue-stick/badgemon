import asyncio
import string
import math

from ..scenes.scene import Scene
from system.eventbus import eventbus
from events.input import ButtonDownEvent, BUTTON_TYPES
from app import App
import time

from ctx import Context
from ..util.misc import *

VALID_CHAR = string.ascii_uppercase
SPECIAL_CHAR = 2

class TextDialog:            
    def __init__(self, app: App, name: str, no_exit = False):
        self._name = name
        self._app = app
        self._open = False
        self._state = "CLOSED"
        
        self.result = ""

        self._selected = 0
        self._selected_visually = 0
        self._opened_amount = 0.0
        self._no_exit = no_exit
        self.opened_event = asyncio.Event()
        self.closed_event = asyncio.Event()
        self.closed_event.set()

        self._time_since_down = 0
        self._time_since_up = 0

    def is_open(self):
        return self._open
    
    def open(self):
        if not self.is_open():
            self._open = True
    
    def close(self):
        if self.is_open():
            self._cleanup()

    async def open_and_wait(self):
        await self.closed_event.wait()
        self._open = True
        await self.opened_event.wait()
    
    async def close_and_wait(self):
        await self.opened_event.wait()
        self._cleanup()
        await self.closed_event.wait()

    def set_name(self, name: str, no_exit = False):
        self._name = name
        if self._state != "CLOSED":
            self.result = ""
            self._selected = 0
            self._selected_visually = 0
        self._no_exit = no_exit
        if no_exit:
            self.open()

    def update(self, delta: float):
        if self.is_open():
            if self._state == "CLOSED":
                self._selected = 0
                self._selected_visually = 0
                self._state = "OPENING"
                self.closed_event.clear()
                self.opened_event.clear()
                self._opened_amount = 0.0
                eventbus.on(ButtonDownEvent, self._handle_buttondown, self._app)
            if self._state == "OPENING":
                if self._opened_amount > 0.99:
                    self._opened_amount = 1.0
                    self._state = "OPEN"
                    self.opened_event.set()
                    return
                weight = math.pow(0.8, (delta/10))
                self._opened_amount = (self._opened_amount * (weight)) + (1-weight)
            elif self._state == "CLOSING":
                if self._opened_amount < 0.01:
                    self._opened_amount = 0.0
                    self._state = "CLOSED"
                    self._open = False
                    self.closed_event.set()
                    return
                weight = math.pow(0.8, (delta/10))
                self._opened_amount = self._opened_amount * weight
            else:
                if self._app._button_states.get(BUTTON_TYPES["DOWN"]):
                    if time.ticks_diff(time.ticks_ms(), self._time_since_down) > 300:
                        self._selected = (self._selected + 1 + len(VALID_CHAR)+SPECIAL_CHAR) % (len(VALID_CHAR)+SPECIAL_CHAR)
                        self._time_since_down = time.ticks_add(self._time_since_down, 80)
                if self._app._button_states.get(BUTTON_TYPES["UP"]):
                    if time.ticks_diff(time.ticks_ms(), self._time_since_up) > 300:
                        self._selected = (self._selected - 1 + len(VALID_CHAR)+SPECIAL_CHAR) % (len(VALID_CHAR)+SPECIAL_CHAR)
                        self._time_since_up = time.ticks_add(self._time_since_up, 80)
                ypos = self._selected * 30
                if self._selected_visually != ypos:
                    weight = math.pow(0.8, (delta/10))
                    self._selected_visually = (self._selected_visually * (weight)) + (ypos * (1-weight))

    def _draw_focus_plane(self, ctx: Context, width: float):
        ctx.rgba(0.3, 0.3, 0.3, 0.8).rectangle((-80)*width, -120, (160)*width, 240).fill()
        col = ctx.rgba(0.2, 0.2, 0.2, 0.8)
        col.move_to((-80)*width,-120).line_to((-80)*width,120).stroke()
        col.move_to((80)*width,-120).line_to((80)*width,120).stroke()
    def _draw_header_plane(self, ctx: Context, width: float, ypos: float = 0):
        ctx.rgba(0.1, 0.1, 0.1, 0.5).rectangle((-80)*width, -100+ypos, (160)*width, 40).fill()

    def _draw_text(self, ctx: Context, choice: str, ypos: int, select: bool, header: bool=False):        
        if select:
            col = ctx.rgb(1.0,0.3,0.0)
        elif header:
            col = ctx.rgb(1.0,0.9,0.9)
        else:
            col = ctx.gray(0.8)
        col.move_to(0, ypos)\
            .text(choice)

    def draw(self, ctx: Context):
        if self.is_open():
            ctx.save()
            ctx.text_baseline = Context.MIDDLE
            ctx.text_align = Context.CENTER
            self._draw_focus_plane(ctx, self._opened_amount)
            current_header = self._name
            if not current_header is None:
                ctx.rectangle((-80)*self._opened_amount, -120, (160)*self._opened_amount, 240).clip()
                self._draw_header_plane(ctx, self._opened_amount)
                shrink_until_fit(ctx, current_header, 150, 30)
                self._draw_text(ctx, current_header, -80, False, header=True)
            self._draw_header_plane(ctx, self._opened_amount, 40)
            shrink_until_fit(ctx, self.result, 150, 30)
            self._draw_text(ctx, self.result, -40, False, header=True)
            ctx.rectangle((-80)*self._opened_amount, -20, (160)*self._opened_amount, 180).clip()
            ctx.font_size = 30
            if len(self.result) == 12:
                self._draw_text(ctx, "Confirm", 40, True)
            else:
                for i, choice in enumerate(["Confirm", "Space"] + list(string.ascii_uppercase)):
                    ypos = (i*30)-self._selected_visually+40
                    if ypos < -20:
                        continue
                    if ypos > 120:
                        break
                    self._draw_text(ctx, choice, ypos, self._selected == i)
            ctx.restore()

    def _handle_buttondown(self, event: ButtonDownEvent):
        if self.is_open():
            if BUTTON_TYPES["UP"] in event.button:
                self._selected = (self._selected - 1 + len(VALID_CHAR)+SPECIAL_CHAR) % (len(VALID_CHAR)+SPECIAL_CHAR)
                self._time_since_up = time.ticks_ms()
            if BUTTON_TYPES["DOWN"] in event.button:
                self._selected = (self._selected + 1 + len(VALID_CHAR)+SPECIAL_CHAR) % (len(VALID_CHAR)+SPECIAL_CHAR)
                self._time_since_down = time.ticks_ms()
            if BUTTON_TYPES["CONFIRM"] in event.button or BUTTON_TYPES["RIGHT"] in event.button:
                if len(self.result) == 12:
                    self._cleanup()
                else:
                    if self._selected == 0:
                        self._cleanup()
                    elif self._selected == 1:
                        self.result += " "
                    else:
                        self.result += VALID_CHAR[self._selected-2]
            if BUTTON_TYPES["CANCEL"] in event.button or BUTTON_TYPES["LEFT"] in event.button:
                if len(self.result) > 0:
                    self.result = self.result[0:-1]
                elif not self._no_exit:
                    self._cleanup()
                return

    def _cleanup(self):
        eventbus.remove(ButtonDownEvent, self._handle_buttondown, self._app)
        self._state = "CLOSING"
        self.closed_event.clear()
        self.opened_event.clear()

class TextExample(Scene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text = TextDialog(
            app=self.sm,
            name="Test Text"
        )

    def handle_buttondown(self, event: ButtonDownEvent):
        self._text.open()

    def update(self, delta: float):
        #print(f"ANSWER: {self._text.result}")
        self._text.update(delta)

    async def background_task(self):
        while True:
            await asyncio.sleep(100)

    def draw(self, ctx: Context):
        super().draw(ctx)
        self._text.draw(ctx)
