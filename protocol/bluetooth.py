import bluetooth
import aioble
import asyncio

_BADGEMON_SERVICE = bluetooth.UUID('42616467-654d-6f6e-3545-7661723a3333')
_BADGEMON_COMM_CHAR = bluetooth.UUID(0x0001)

_PERIPHERAL_STATE = 0
_CENTRAL_STATE = 1
_DISCONNECTED = 2


class BluetoothDevice:

    def __init__(self):

        self._conn = None
        self._comm = None
        self._state = _DISCONNECTED

        service = aioble.Service(_BADGEMON_SERVICE)
        self._server_char = aioble.Characteristic(service, _BADGEMON_COMM_CHAR, notify=True, write_no_response=True)
        aioble.register_services(service)

    async def send_message(self, packet):
        """
        Sends a message to the currently connected device

        @param packet:
        @return: None
        """
        if self._state == _PERIPHERAL_STATE:
            self._server_char.notify(self._conn, packet)
        elif self._state == _CENTRAL_STATE:
            await self._comm.write(packet)

    async def recv_message(self):
        """
        Receives a message

        @return: The message
        """
        while True:
            try:
                if self._state == _PERIPHERAL_STATE:
                    await self._server_char.written(timeout_ms=2000)
                    data = self._server_char.read()
                    self._server_char.write(b'')
                    print(data)

                elif self._state == _CENTRAL_STATE:
                    data = await self._comm.notified(timeout_ms=2000)
                    print(data)
                else:
                    await asyncio.sleep(2)
            except asyncio.TimeoutError:
                continue

    async def find_trainers(self):
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

    def start_server(self):
        service = aioble.Service(_BADGEMON_SERVICE)
        self._comm = aioble.Characteristic(service, _BADGEMON_COMM_CHAR, notify=True, write_no_response=True)
        aioble.register_services(service)

    async def advertise(self):
        while True:
            if self._state == _CENTRAL_STATE:
                await asyncio.sleep(10)
                continue
            async with await aioble.advertise(
                    250000,
                    name="TrainerName",
                    services=[_BADGEMON_SERVICE],
                    appearance=0x0A82,
            ) as connection:
                print("Connection from", connection.device)
                self._state = _PERIPHERAL_STATE
                self._conn = connection
                await connection.disconnected()
                self._state = _DISCONNECTED

    async def connect_peripheral(self, device):
        """
        Connect to a peripheral device

        @param device: an aioble Device()
        @return: True if connection was successful, else false
        """
        try:
            self._conn = await device.connect(timeout_ms=2000)
            service = await self._conn.service(_BADGEMON_SERVICE)

            self._comm = await service.characteristic(_BADGEMON_COMM_CHAR)
            self._state = _CENTRAL_STATE
            return True

        except asyncio.TimeoutError:
            return False

    async def main(self):
        server_thread = asyncio.create_task(self.advertise())
        recv_thread = asyncio.create_task(self.recv_message())
        await asyncio.gather(server_thread, recv_thread)


if __name__ == '__main__':
    dev = BluetoothDevice()
    print(asyncio.run(dev.find_trainers()))
    asyncio.run(dev.main())
