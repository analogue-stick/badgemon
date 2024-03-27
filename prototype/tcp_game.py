from socket import socket
from struct import unpack

from badgemon import Player, BadgeMon, Moves
from protocol import API, Protocol


class TCPPlayer(Player):
    def __init__(self, name: str, party: [BadgeMon]):
        super().__init__(name, party)
        self.conn: socket = None

    def parse_res(self):
        header = self.conn.recv(2)
        code, packet_len = unpack('>BB', header)
        return code, packet_len

    def get_player(self, length):
        packet = self.conn.recv(length)
        player = Player.deserialise(packet)
        return player

    def send_move(self, move):
        self.conn.send(Protocol.attack_packet(move))


class Defender(TCPPlayer):
    def __init__(self, name: str, party: [BadgeMon]):
        super().__init__(name, party)

    def search(self):
        s = socket()
        s.bind(('0.0.0.0', 1337))
        s.listen()

        print('[*] Now waiting for connection from challenger')
        self.conn, addr = s.accept()
        print(f'[*] Incoming connection from {addr}')

        code, length = self.parse_res()
        if code == API.CHALLENGE_REQUEST:
            opponent = self.get_player(length)
            i = input(f'[*] Incoming challenge from {opponent.name}\nAccept? (y/n): ')
            if i in 'yY':
                return opponent
            else:

                return None
        else:
            print(f'[*] Incorrect challenge code. Connect failed')
            return None

    def make_move(self, mon: BadgeMon, target: BadgeMon):
        i = input("[*] What would you like to do?\n- (a)ttack\n- (r)un away\n- (u)se an item\n: ")
        if i == 'a':
            moves = mon.list_moves()
            pretty_print = '\n- ' + '\n- '.join(moves)
            i = input(f"[*] Your available moves are:{pretty_print}\n: ")
            for move in mon.move_set:
                name = Moves.MOVES_ID[move].name
                if name == i:
                    mon.do_move(move, target)
                    self.send_move(move)
