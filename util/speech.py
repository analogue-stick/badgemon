import asyncio
import display
import gc
import math

from system.eventbus import eventbus
from events.input import ButtonDownEvent

class SpeechDialog:
    def __init__(self, app, speech: str):
        self.speech = speech
        self.lines = []
        self.app = app
        self.open = False
        self.state = "CLOSED"

    def update(self, delta):
        if self.open:
            if self.state == "CLOSED":
                self.state = "OPENING"
                self.opened_amount = 0.0

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
                    return
                weight = math.pow(0.8, (delta/10000))
                self.opened_amount = self.opened_amount * weight
            elif self.selected_visually != self.selected:
                weight = math.pow(0.8, (delta/10000))
                self.selected_visually = (self.selected_visually * (weight)) + (self.selected * (1-weight))

    def draw_focus_plane(self, ctx, width):
        ctx.rgba(0.5, 0.5, 0.5, 0.5).rectangle((-80)*width, -120, (160)*width, 240).fill()
    def draw_header_plane(self, ctx, width):
        ctx.rgba(0.1, 0.1, 0.1, 0.5).rectangle((-80)*width, -110, (160)*width, 40).fill()

    def draw_text(self, ctx, choice: str, ypos: int, select: bool, header: bool=False):
        text_width = ctx.text_width(choice)
        text_height = ctx.font_size
        
        if select:
            col = ctx.rgb(1.0,0.3,0.0)
        elif header:
            col = ctx.rgb(1.0,0.9,0.9)
        else:
            col = ctx.gray(0)
        col.move_to(0 - text_width / 2, text_height / 8 + ypos)\
            .text(choice)

    def draw(self, ctx):
        if self.open:
            if not self.lines:
                line = ""
                for word in self.speech.split():
                    if ctx.
                    
            if self.state == "OPENING" or self.state == "CLOSING":
                self.draw_focus_plane(ctx, self.opened_amount)
                if self.current_header != "":
                    self.draw_header_plane(ctx, self.opened_amount)
            else:
                self.draw_focus_plane(ctx, self.opened_amount)
                for i, choice in enumerate(self.current_tree):
                    ypos = (i-self.selected_visually)*30
                    self.draw_text(ctx, choice[0], ypos, self.selected == i)
                if self.current_header != "":
                    self.draw_header_plane(ctx, self.opened_amount)
                    self.draw_text(ctx, self.current_header, -80, False, header=True)

    def _handle_buttondown(self, event: ButtonDownEvent):
        if event.button == 0:
            self.selected = (self.selected - 1 + len(self.current_tree)) % len(self.current_tree)
        if event.button == 3:
            self.selected = (self.selected + 1 + len(self.current_tree)) % len(self.current_tree)
        if 0 < event.button < 3:
            c = self.current_tree[self.selected][1]
            if isinstance(c, FunctionType):
                c(self.app)
                self._cleanup()
                return
            self.previous_trees.append(self.current_tree)
            self.previous_headers.append(self.current_header)
            self.current_header = self.current_tree[self.selected][0]
            self.current_tree = c
            self.selected = 0
        if 3 < event.button < 6:
            if self.previous_trees:
                self.current_tree = self.previous_trees.pop()
                self.current_header = self.previous_headers.pop()
                self.selected = 0
                return
            self._cleanup()
            return

    def _cleanup(self):
        eventbus.remove(ButtonDownEvent, self._handle_buttondown, self.app)
        self.state = "CLOSING"

class SpeechExample():
    def __init__(self):
        self.speecn = SpeechDialog(
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
        self.speech.draw(ctx)
