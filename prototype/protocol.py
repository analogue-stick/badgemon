"""
Aha, the Protocol!

This will describe the two player protocol, I intend to model it over TCP first, then move to BLE. Only because it's
more "normal". I've written stuff for BLE before and it gets messy.

Also since this is a prototype we'd only be getting lost in the specific implementation of the python-bleak library
instead of working on a protocol
"""
from socket import socket
from struct import pack, unpack
from badgemon import Player, BadgeMon


class API:
    CHALLENGE_REQUEST = 1
    CHALLENGE_ACCEPT = 2
    CHALLENGE_DENY = 3

    SEND_ATTACK = 4


class Protocol:

    @staticmethod
    def challenge_req_packet(challenger: Player):
        packet = challenger.serialise()
        header = pack('>BB', API.CHALLENGE_REQUEST, len(packet))
        return header + packet

    @staticmethod
    def challenge_res_packet(accept: bool, defender: Player):
        if not accept:
            header = pack('>BB', API.CHALLENGE_DENY, 0)
            return header
        packet = defender.serialise()
        header = pack('>BB', API.CHALLENGE_ACCEPT, len(packet))
        return header + packet

    @staticmethod
    def attack_packet(move_id: int):
        packet = pack('>B', move_id)
        header = pack('>BB', API.SEND_ATTACK, len(packet))
        return header + packet


def __init__(self, conn):
    pass
