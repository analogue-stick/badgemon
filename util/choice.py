import asyncio
import display
import gc
import math

from typing import List, Tuple
from types import FunctionType
from system.eventbus import eventbus
from events.input import ButtonDownEvent

from ctx import Context

ChoiceTree = List[Tuple[str, 'ChoiceTree' | FunctionType]]

class ChoiceDialog:
    def __init__(self, app, choices: ChoiceTree=[], header = ""):
        self._tree = choices
        self._app = app
        self._header = header
        self._open = False
        self._state = "CLOSED"

    def is_open(self):
        return self._open
    
    def open(self):
        if not self.is_open():
            self._open = True
    
    def close(self):
        if self.is_open():
            self._cleanup()

    def set_choices(self, choices: ChoiceTree=[], header: str | None = None):
        self._tree = choices
        if header is not None:
            self._header = header
        if self._state != "CLOSED":
            self._previous_trees = []
            self._current_tree = self._tree
            self._selected = 0
            self._selected_visually = 0
            self._previous_headers = []
            self._current_header = self._header

    def update(self, delta: float):
        if self.is_open():
            if self._state == "CLOSED":
                self._previous_trees = []
                self._current_tree = self._tree
                self._selected = 0
                self._selected_visually = 0
                self._state = "OPENING"
                self._opened_amount = 0.0
                self._previous_headers = []
                self._current_header = self._header
                eventbus.on(ButtonDownEvent, self._handle_buttondown, self._app)
            if self._state == "OPENING":
                if self._opened_amount > 0.99:
                    self._opened_amount = 1.0
                    self._state = "OPEN"
                    return
                weight = math.pow(0.8, (delta/10000))
                self._opened_amount = (self._opened_amount * (weight)) + (1-weight)
            elif self._state == "CLOSING":
                if self._opened_amount < 0.01:
                    self._opened_amount = 0.0
                    self._state = "CLOSED"
                    self._open = False
                    return
                weight = math.pow(0.8, (delta/10000))
                self._opened_amount = self._opened_amount * weight
            if self._selected_visually != self._selected:
                weight = math.pow(0.8, (delta/10000))
                self._selected_visually = (self._selected_visually * (weight)) + (self._selected * (1-weight))

    def _draw_focus_plane(self, ctx: Context, width: float):
        ctx.rgba(0.5, 0.5, 0.5, 0.5).rectangle((-80)*width, -120, (160)*width, 240).fill()
        col = ctx.rgba(0.2, 0.2, 0.2, 0.5)
        col.move_to((-80)*width,-120).line_to((-80)*width,120).stroke()
        col.move_to((80)*width,-120).line_to((80)*width,120).stroke()
    def _draw_header_plane(self, ctx: Context, width: float):
        ctx.rgba(0.1, 0.1, 0.1, 0.5).rectangle((-80)*width, -110, (160)*width, 40).fill()

    def _draw_text(self, ctx: Context, choice: str, ypos: int, select: bool, header: bool=False):
        text_width = ctx.text_width(choice)
        text_height = ctx.font_size
        
        if select:
            col = ctx.rgb(1.0,0.3,0.0)
        elif header:
            col = ctx.rgb(1.0,0.9,0.9)
        else:
            col = ctx.gray(0)
        col.move_to(0, ypos)\
            .text(choice)

    def draw(self, ctx: Context):
        if self.is_open():
            ctx.save()
            ctx.font_size = 30
            ctx.text_baseline = Context.MIDDLE
            ctx.text_align = Context.CENTER
            clip = ctx.rectangle((-80)*self._opened_amount, -120, (160)*self._opened_amount, 240).clip()
            self._draw_focus_plane(ctx, self._opened_amount)
            for i, choice in enumerate(self._current_tree):
                ypos = (i-self._selected_visually)*ctx.font_size
                self._draw_text(clip, choice[0], ypos, self._selected == i)
            if self._current_header != "":
                self._draw_header_plane(ctx, self._opened_amount)
                self._draw_text(clip, self._current_header, -80, False, header=True)
            ctx.restore()

    def _handle_buttondown(self, event: ButtonDownEvent):
        if event.button == 0:
            self._selected = (self._selected - 1 + len(self._current_tree)) % len(self._current_tree)
        if event.button == 3:
            self._selected = (self._selected + 1 + len(self._current_tree)) % len(self._current_tree)
        if 0 < event.button < 3:
            c = self._current_tree[self._selected][1]
            if isinstance(c, FunctionType):
                c(self._app)
                self._cleanup()
                return
            self._previous_trees.append(self._current_tree)
            self._previous_headers.append(self._current_header)
            self._current_header = self._current_tree[self._selected][0]
            self._current_tree = c
            self._selected = 0
        if 3 < event.button < 6:
            if self._previous_trees:
                self._current_tree = self._previous_trees.pop()
                self._current_header = self._previous_headers.pop()
                self._selected = 0
                return
            self._cleanup()
            return

    def _cleanup(self):
        eventbus.remove(ButtonDownEvent, self._handle_buttondown, self._app)
        self._state = "CLOSING"

class ChoiceExample():
    def __init__(self):
        self._choice = ChoiceDialog(
            app=self,
            choices=[("thing 1", lambda a: a._set_answer("1")),
                     ("thing 2", lambda a: a._set_answer("2")),
                     ("thing 3", lambda a: a._set_answer("3")),
                     ("more", [("thing 41", lambda a: a._set_answer("41")),
                               ("thing 42", lambda a: a._set_answer("42"))])],
            header="Choice Test"
        )
        self._answer = ""
        eventbus.on(ButtonDownEvent, self._handle_buttondown, self)

    def _handle_buttondown(self, event: ButtonDownEvent):
        self._choice.open()

    def _set_answer(self, str: str):
        self._answer = str

    def update(self, delta: float):
        print(f"ANSWER: {self.answer}")
        self._choice.update(delta)

    async def background_update(self):
        while True:
            await asyncio.sleep(1)
            print("fps:", display.get_fps(), f"mem used: {gc.mem_alloc()}, mem free:{gc.mem_free()}")

    def _draw_background(self, ctx: Context):
        ctx.gray(0.9).rectangle(-120, -120, 240, 240).fill()

    def draw(self, ctx: Context):
        self._draw_background(ctx)
        self._choice.draw(ctx)
