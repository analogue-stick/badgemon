"""
Aha, the Protocol!

This will describe the two player protocol, I intend to model it over TCP first, then move to BLE. Only because it's
more "normal". I've written stuff for BLE before and it gets messy.

Also since this is a prototype we'd only be getting lost in the specific implementation of the python-bleak library
instead of working on a protocol
"""
from struct import pack, unpack_from
from ..game.player import Player
from ..game.mons import Mon


class API:
    CHALLENGE_REQUEST = 1
    CHALLENGE_ACCEPT = 2
    CHALLENGE_DENY = 3

    SEND_ATTACK = 1
    SEND_MON = 2
    SEND_ITEM = 3
    SEND_ESCAPE = 4


def challenge_req_packet(challenger: Player, seed: int):
    packet = pack(">I", seed) + challenger.serialise()
    header = pack('>BH', API.CHALLENGE_REQUEST, len(packet))
    return header + packet

def challenge_res_packet(defender: Player, turn):
    packet = defender.serialise()
    header = pack('>BH', API.CHALLENGE_ACCEPT, len(packet))
    return header + packet

def attack_packet(move_opcode: int, move_operand: int):
    packet = pack('>BB', move_opcode, move_operand)
    header = pack('>BH', API.SEND_ATTACK, len(packet))
    return header + packet

def decode_packet(packet: bytes, player: Player, mon: Mon):
    type = packet[0]
    length = unpack_from(">H", packet, 1)[0]
    offset = 3
    if type == API.CHALLENGE_REQUEST:
        seed = unpack_from(">I", packet, offset)[0]
        offset += 4
        player = Player.deserialise(packet[offset:offset+length-4])
        return (player, seed)
    if type == API.CHALLENGE_ACCEPT:
        player = Player.deserialise(packet[offset:offset+length])
        return player
    if type == API.SEND_ATTACK:
        move_opcode = packet[offset]
        offset += 1
        move_operand = packet[offset]
        if move_opcode == API.SEND_ATTACK:
            move = mon.moves[move_operand]
            return move
        if move_opcode == API.SEND_MON:
            mon = player.badgemon[move_opcode]
            return mon
        if move_opcode == API.SEND_ITEM:
            item = player.inventory[move_operand]
            return item
        if move_opcode == API.SEND_ESCAPE:
            return None