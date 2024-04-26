import asyncio
import app


class BaseScene:

    def __init__(self):
        self._exit = asyncio.Event()
        self._ctx = app.Context.ctx
        self._frame = 0
        self.task = None

    async def tick(self):
        pass

    def setup(self):
        pass

    def stop(self):
        self._exit.set()

    async def main_loop(self):
        try:
            while True:
                await self.tick()
                await asyncio.sleep_ms(33)
                self._frame += 1
        finally:
            self._ctx.tasks.remove(self.task)

    def run(self):
        self.setup()
        self.task = asyncio.create_task(self.main_loop())
        self._ctx.tasks.add(self.task)
