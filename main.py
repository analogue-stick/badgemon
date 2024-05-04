import asyncio
from machine import Pin, SPI
import app
import protocol
import scenes


async def main():
    ctx = app.Context()
    try:
        # set up the screen and bluetooth
        ctx.bluetooth_device = protocol.BluetoothDevice()

        ctx.screen = None
        ctx.screen.init()

        # set up and run the input handler
        ctx.input_handler = app.InputHandler()
        ctx.input_handler.start()
        ctx.tasks.add(ctx.input_handler.task)

        # load the start screen
        main_scene = scenes.MainMenuScene()
        main_scene.setup()
        await main_scene.main_loop()

        print('\n\n\n', ctx.tasks, '\n\n\n')
        # Wait for shutdown signal
        await ctx.shutdown.wait()


    finally:
        # Gracefully shutdown
        ctx.input_handler.task.cancel()


if __name__ == '__main__':
    asyncio.run(main())
