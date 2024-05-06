import socket
import struct
import threading
from typing import Tuple

# Constants defining the network protocol
MAGIC_COOKIE = b'\xab\xcd\xdc\xba'  # Magic cookie to identify valid packets
OFFER_MSG_TYPE = 2  # Type of message indicating an offer
UDP_PACKET_LEN = 39  # Length of UDP packets expected
BROADCAST_PORT = 13117  # Port for broadcasting game offers

# Constants for message handling
MSG_LEN_HEADER = 4  # Header length indicating the length of the following message
TIME_TO_SEND_ANS = 10  # Time allowed for sending an answer
END_GAME_MSG = "Game over!"  # Message prefix indicating the end of the game


# Function to wait for a game offer from the server
def wait_for_offer(udp_socket: socket.socket) -> Tuple[str, str, int]:
    # Bind the UDP socket to a specific address and port
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(("", BROADCAST_PORT))
    # Wait for the offer to the game and unpack it when received
    data, server_addr = udp_socket.recvfrom(UDP_PACKET_LEN)
    try:
        (magic_cookie, msg_type, server_name, server_port) = struct.unpack('!4sB32sH', data)
    except struct.error:
        raise InvalidOffer("Invalid UDP packet structure")
    # Check the magic cookie
    if magic_cookie != MAGIC_COOKIE:
        raise InvalidOffer("Invalid magic cookie")
    # Check the message type
    if msg_type != OFFER_MSG_TYPE:
        raise InvalidOffer("Invalid message type (not offer)")

    return server_name.decode().rstrip(), server_addr[0], server_port


# Function to connect to the game server over TCP
def connect_to_server(server_ip: str, server_port: int) -> socket.socket:
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((server_ip, server_port))
    return tcp_socket


# Function to handle the game
def play(tcp_socket: socket.socket, player_name: str) -> None:
    # Send player name to the server
    tcp_socket.sendall(f"{player_name}\n".encode())
    # Print game rules
    print("rules of the game:\n\tIf your answer is TRUE enter: Y / T / 1\n\tIf your answer is FALSE enter: N / F / 0")
    while True:
        # Receive message length header
        msg_len = tcp_socket.recv(MSG_LEN_HEADER)
        # Receive the message based on the received length
        msg = tcp_socket.recv(int.from_bytes(msg_len, byteorder='big'))
        print(msg)
        # Check if the game is over
        if msg[:len(END_GAME_MSG)] != END_GAME_MSG:
            # If not, process player answer
            process_player_answer(tcp_socket)
        else:
            break


# Function for getting and sending player's answer
def process_player_answer(tcp_socket):
    # Event for stopping the answer sending thread
    stop_flag = threading.Event()
    # Thread to send the answer
    send_key_t = threading.Thread(target=send_key, args=(tcp_socket, stop_flag))
    send_key_t.start()
    try:
        # Wait for TIME_TO_SEND_ANS seconds for the player to enter an answer
        send_key_t.join(timeout=TIME_TO_SEND_ANS)
        stop_flag.set()
    except threading.ThreadError:
        print("Error while joining thread")


# Function for sending the player's answer
def send_key(tcp_socket: socket.socket, stop_flag: threading.Event):
    # Get player input for the answer
    key = input("Please enter your answer:")
    # Validate the answer
    while not is_valid_key(key) and not stop_flag.is_set():
        print("Invalid answer")
        key = input("Please enter your answer:")
    if not stop_flag.is_set():
        # If the stop flag is not set (the timeout didn't happen), send the answer to the server
        tcp_socket.sendall(key.encode())


# Function to validate player answers
def is_valid_key(key: str) -> bool:
    return key in ['N', 'F', '0', 'Y', 'T', '1']


# Function to start the trivia client loop
def start() -> None:
    # Get player name
    player_name = input("please enter your name")
    print("Client started, listening for offer requests...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        while True:
            try:
                # Wait for a game offer
                server_name, server_ip, server_tcp_port = wait_for_offer(udp_socket)
                print(f"Received offer from server {server_name} at address {server_ip}, attempting to connect...")
                try:
                    # Connect to the server
                    tcp_socket = connect_to_server(server_ip, server_tcp_port)
                except (socket.error, socket.timeout) as e:
                    print('Could not connect to server:', str(e))
                    continue
                try:
                    # Play the game
                    with tcp_socket:
                        play(tcp_socket, player_name)
                        print("Server disconnected, listening for offer requests...")
                except (socket.error, socket.timeout) as e:
                    print(f"Communication error with the server: {e}")

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