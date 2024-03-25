"""
Aha, the Protocol!

This will describe the two player protocol, I intend to model it over TCP first, then move to BLE. Only because it's
more "normal". I've written stuff for BLE before and it gets messy.

Also since this is a prototype we'd only be getting lost in the specific implementation of the python-bleak library
instead of working on a protocol
"""


class API:
    CHALLENGE = 1
    SEND_PARTY = 2
    SEND_MOVE = 3


class Protocol:
    def __init__(self, address: str, port: int):
        pass
