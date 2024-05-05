import socket
import struct
from ip import get_my_ip

MAGIC_COOKIE = b'\xab\xcd\xdc\xba'
OFFER_MSG_TYPE = 2
BROADCAST_PORT = 13117


def wait_for_offer(udp_socket):
    # Bind the UDP socket to a specific address and port
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(("", BROADCAST_PORT))
    print("Client started, listening for offer requests...")
    data, server_addr = udp_socket.recvfrom(1024)
    (magic_cookie, msg_type, server_name, server_port) = struct.unpack('!4sB32sH', data)

    # Check the magic cookie
    if magic_cookie != MAGIC_COOKIE:
        raise InvalidOffer("Invalid magic cookie")
    # Check the message type
    if msg_type != OFFER_MSG_TYPE:
        raise InvalidOffer("Invalid message type (not offer)")

    return server_name.decode().rstrip(), server_addr[0], server_port


def connect_to_server(server_ip, server_port):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((server_ip, server_port))
    return tcp_socket

def play(tcp_socket, player_name):
    with tcp_socket:
        tcp_socket.sendall(f"{player_name}\n".encode())

def start():
    player_name = input("please enter your name")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        while True:
            # wait for a game
            try:
                server_name, server_ip, server_tcp_port = wait_for_offer(udp_socket)
                print(f"Received offer from server {server_name} at address {server_ip}, attempting to connect...")
                try:
                    tcp_socket = connect_to_server(server_ip, server_tcp_port)
                except (socket.error, socket.timeout) as e:
                    print('Could not connect to server:', str(e))
                    continue
                try:
                    play(tcp_socket, player_name)

            except socket.timeout:
                print('No server found')
                continue
            except InvalidOffer as e:
                print(e.message)
                continue




class InvalidOffer(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


if __name__ == '__main__':
    start()