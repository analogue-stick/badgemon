from socket import socket
from struct import unpack
from typing import List, Optional

from badgemon import Player, BadgeMon, Moves, Battle
from protocol import API, Protocol
from argparse import ArgumentParser


class TCPPlayer(Player):
    def __init__(self, name: str, party: List[BadgeMon]):
        super().__init__(name, party)
        self.conn: Optional[socket] = None
        self.buffer = bytearray()

    def get_data(self, length):
        while length > len(self.buffer):
            res = self.conn.recv(4096)
            self.buffer += res
        packet = self.buffer[:length]
        self.buffer = self.buffer[length:]
        return packet

    def parse_res(self):
        header = self.get_data(2)
        code, packet_len = unpack('>BB', header)
        return code, packet_len

    def get_player(self, length):
        packet = self.get_data(length)
        player = Player.deserialise(packet)
        remote_player = RemotePlayer(player)
        remote_player.conn = self.conn
        return remote_player

    def get_attack(self, length):
        packet = self.get_data(length)
        move_id, = unpack('>B', packet)
        return move_id

    def send_challenge(self):
        self.conn.sendall(Protocol.challenge_req_packet(self))

    def send_challenge_response(self, accept):
        self.conn.sendall(Protocol.challenge_res_packet(accept, self))

    def send_move(self, move):
        self.conn.sendall(Protocol.attack_packet(move))


class RemotePlayer(TCPPlayer):

    def __init__(self, player: Player):
        super().__init__(player.name, player.party)

    def make_move(self, mon: BadgeMon, target: BadgeMon):
        code, length = self.parse_res()
        print(code)
        if code == API.SEND_ATTACK:
            move_id = self.get_attack(length)
            print(f'[*] Opponent used {Moves.MOVES_ID[move_id].name}')
            mon.do_move(move_id, target)


class LocalPlayer(TCPPlayer):
    def make_move(self, mon: BadgeMon, target: BadgeMon):
        i = input("[*] What would you like to do?\n- (a)ttack\n: ")
        if i == 'a':
            moves = mon.list_moves()
            pretty_print = '\n- ' + '\n- '.join(moves)
            i = input(f"[*] Your available moves are:{pretty_print}\n: ")
            for move in mon.move_set:
                name = Moves.MOVES_ID[move].name
                if name == i:
                    mon.do_move(move, target)
                    self.send_move(move)


class Defender(LocalPlayer):

    def defend(self):
        s = socket()
        s.bind(('0.0.0.0', 1337))
        s.listen()

        print('[*] Now waiting for connection from challenger')
        self.conn, addr = s.accept()
        print(f'[*] Incoming connection from {addr}')

        code, length = self.parse_res()
        if code == API.CHALLENGE_REQUEST:
            opponent = self.get_player(length)
            i = input(f'[*] Incoming challenge from {opponent.name}\nAccept? (y/N): ')
            if i in 'yY':
                self.send_challenge_response(True)
                return opponent
            else:
                self.send_challenge_response(False)
                return None
        else:
            print(f'[*] Incorrect challenge code. Connect failed')
            return None


class Attacker(LocalPlayer):
    def attack(self, ip):
        self.conn = socket()

        print(f'[*] Attempting to challenge {ip}')
        self.conn.connect((ip, 1337))

        print(f'[*] Connect successful, sending challenge')
        self.send_challenge()

        code, length = self.parse_res()
        if code == API.CHALLENGE_ACCEPT:
            opponent = self.get_player(length)
            print(f'[*] Defender {opponent.name} accepted the challenge')
            return opponent
        elif code == API.CHALLENGE_DENY:
            raise Exception('Defender refused the challenge')
        else:
            raise Exception('Incorrect challenge code. Connect failed')


LILGUY = BadgeMon("Lil guy", [Moves.HIT, Moves.SCRATCH, Moves.BITE, Moves.MAIM])
BIGGUY = BadgeMon("Big guy", [Moves.HIT, Moves.SCRATCH, Moves.BITE, Moves.MAIM])

if __name__ == '__main__':
    parser = ArgumentParser(prog="TCP BadgeMon Game",
                            description="A prototype version of the BadgeMon game played over TCP instead of BLE")

    parser.add_argument('name')
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--attack', type=str, help="Attack an IP address")
    g.add_argument('--defend', action='store_true', help="Defend on your IP address")

    args = parser.parse_args()
    print(args.attack, args.defend)
    if args.defend:
        player = Defender(args.name, [LILGUY])
        opponent = player.defend()
        battle = Battle(opponent, player)

    else:
        player = Attacker(args.name, [BIGGUY])
        opponent = player.attack(args.attack)
        battle = Battle(player, opponent)
    try:
        battle.do_battle()
    except KeyboardInterrupt:
        player.conn.close()
        raise KeyboardInterrupt
