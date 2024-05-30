import asyncio

from ..protocol.queue import Queue

import aioble
import bluetooth

_BADGEMON_SERVICE = bluetooth.UUID('42616467-654d-6f6e-3545-7661723a3333')
_BADGEMON_COMM_CHAR = bluetooth.UUID(0x0001)


import sys
if sys.implementation.name == "micropython":
    pass
else:
    import uuid
    _BADGEMON_SERVICE = uuid.UUID('42616467-654d-6f6e-3545-7661723a3333')
    _BADGEMON_COMM_CHAR = uuid.UUID(int=0x0001)

_PERIPHERAL_STATE = 0
_CENTRAL_STATE = 1
_DISCONNECTED = 2


class BluetoothDevice:

    def __init__(self):
        self._input = Queue()
        self._output = Queue()
        self.connection = asyncio.Event()
        self.host = False
        self.conn_name = ""

    async def _send_task(self, conn, char, state: int) -> None:
        """

        @param conn: The current connection
        @param char: The characteristic to notify/write to
        @param state: Whether the device is a server or client
        @return:
        """
        while True:
            packet = await self._input.get()

            if state == _PERIPHERAL_STATE:
                char.notify(conn, packet)

            elif state == _CENTRAL_STATE:
                await char.write(packet)

    async def _recv_task(self, char, state):
        """

        @param char:
        @param state:
        @return:
        """
        while True:
            try:
                if state == _PERIPHERAL_STATE:
                    await char.written(timeout_ms=2000)
                    data = char.read()
                    char.write(b'')

                elif state == _CENTRAL_STATE:
                    data = await char.notified(timeout_ms=2000)

                else:
                    data = b''

                await self._output.put(data)
                print(data)

            except asyncio.TimeoutError:
                continue

    @staticmethod
    async def find_trainers():
        """
        Search for nearby trainers

        @return: List of names and devices
        """
        trainers = []
        async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
            async for result in scanner:
                if _BADGEMON_SERVICE in result.services():
                    trainers.append((result.name(), result.device))

        return trainers

    async def advertise(self):
        service = aioble.Service(_BADGEMON_SERVICE)
        char = aioble.Characteristic(service, _BADGEMON_COMM_CHAR, notify=True, write_no_response=True)
        aioble.register_services(service)
        while True:
            async with await aioble.advertise(
                    250000,
                    name="TrainerName",
                    services=[_BADGEMON_SERVICE],
                    appearance=0x0A82,
            ) as connection:
                print("Connection from", connection.device)
                self.conn_name = connection.name
                if not self.connection.is_set():
                    self.host = False
                    self.connection.set()
                    recv_task = asyncio.create_task(self._recv_task(char, _PERIPHERAL_STATE))
                    send_task = asyncio.create_task(self._send_task(connection, char, _PERIPHERAL_STATE))
                    disconnect_task = asyncio.create_task(connection.disconnected())
                    await asyncio.gather(send_task, recv_task, disconnect_task)
                    self.connection.clear()

    async def connect_peripheral(self, device):
        try:
            connection = await device.connect(timeout_ms=2000)
        except asyncio.TimeoutError:
            print("Timeout during connection")
            return

        async with connection:
            if not self.connection.is_set():
                self.host = True
                self.connection.set()
                try:
                    service = await connection.service(_BADGEMON_SERVICE)
                    char = await service.characteristic(_BADGEMON_COMM_CHAR)
                except asyncio.TimeoutError:
                    self.connection.clear()
                    return
                self.conn_name = connection.device.addr
                recv_task = asyncio.create_task(self._recv_task(char, _CENTRAL_STATE))
                send_task = asyncio.create_task(self._send_task(connection, char, _CENTRAL_STATE))
                disconnect_task = asyncio.create_task(connection.disconnected())
                await asyncio.gather(send_task, recv_task, disconnect_task)
                self.connection.clear()

    async def main(self):
        pass


if __name__ == '__main__':
    dev = BluetoothDevice()
    print(asyncio.run(dev.find_trainers()))
    asyncio.run(dev.main())
