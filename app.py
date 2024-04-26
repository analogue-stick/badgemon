import asyncio
from machine import Pin
import sys
import select

try:
    from typing import List, Callable, Optional
    import gc9a01
except ImportError:
    pass


class Context:
    ctx: 'Context'

    def __init__(self):
        Context.ctx = self
        self.screen: Optional[gc9a01.GC9A01] = None
        self.player = None
        self.bluetooth_device = None
        self.input_handler = None
        self.tasks = set()

        self.shutdown = asyncio.Event()


class InputHandler:

    def __init__(self):
        self.task: Optional[asyncio.Task] = None
        self.button_callbacks: List[Optional[Callable]] = [
            lambda: print('Button 0 Pressed'),
            lambda: print('Button 1 Pressed'),
            lambda: print('Button 2 Pressed'),
            lambda: print('Button 3 Pressed'),
            lambda: print('Button 4 Pressed'),
            lambda: print('Button 5 Pressed'),
        ]

        self.buttons: List[Pin] = [
            Pin(0, Pin.IN, Pin.PULL_DOWN),
            Pin(0, Pin.IN, Pin.PULL_DOWN),
            Pin(0, Pin.IN, Pin.PULL_DOWN),
            Pin(0, Pin.IN, Pin.PULL_DOWN),
            Pin(0, Pin.IN, Pin.PULL_DOWN),
            Pin(0, Pin.IN, Pin.PULL_DOWN),
        ]

        # Stupid bits for REPL testing
        self.spoll = select.poll()
        self.spoll.register(sys.stdin, select.POLLIN)

    def start(self):
        self.task = asyncio.create_task(self.mainloop())

    async def mainloop(self):
        try:
            while True:
                # Stand in code because I don't have physical buttons to test with, this will ultimately look something
                # like this:

                # for button, handler in zip(self.buttons, self.button_callbacks):
                #     if button.value() and handler is not None:
                #         handler()
                # await asyncio.sleep_ms(33)

                res = ''
                while res == '':
                    while self.spoll.poll(0):
                        res += sys.stdin.read(1)

                    await asyncio.sleep_ms(10)

                if res not in list('012345'):
                    continue

                handler = self.button_callbacks[int(res)]
                if handler is not None:
                    handler()

        finally:
            pass

