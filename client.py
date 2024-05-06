import socket
import struct
import threading
from typing import Tuple
import colors


class TriviaClient:
    # Constants defining the network protocol
    MAGIC_COOKIE = b'\xab\xcd\xdc\xba'  # Magic cookie to identify valid packets
    OFFER_MSG_TYPE = 2  # Type of message indicating an offer
    UDP_PACKET_LEN = 39  # Length of UDP packets expected
    BROADCAST_PORT = 13117  # Port for broadcasting game offers

    # Constants for message handling
    MSG_LEN_HEADER = 4  # Header length indicating the length of the following message
    TIME_TO_SEND_ANS = 10  # Time allowed for sending an answer
    END_GAME_MSG = "Game over!"  # Message prefix indicating the end of the game
    # Message contained in the last summary message that indicates that it's the last summary (the game is over)
    END_GAME_SUMMARY = "Wins!"
    KEYS = ['N', 'F', '0', 'Y', 'T', '1']

    # Function to wait for a game offer from the server
    def wait_for_offer(self, udp_socket: socket.socket) -> Tuple[str, str, int]:
        # Bind the UDP socket to a specific address and port
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(("", self.BROADCAST_PORT))
        # Wait for the offer to the game and unpack it when received
        data, server_addr = udp_socket.recvfrom(self.UDP_PACKET_LEN)
        try:
            (magic_cookie, msg_type, server_name, server_port) = struct.unpack('!4sB32sH', data)
        except struct.error:
            raise InvalidOffer("Invalid UDP packet structure")
        # Check the magic cookie
        if magic_cookie != self.MAGIC_COOKIE:
            raise InvalidOffer("Invalid magic cookie")
        # Check the message type
        if msg_type != self.OFFER_MSG_TYPE:
            raise InvalidOffer("Invalid message type (not offer)")

        return server_name.decode().rstrip(), server_addr[0], server_port

    # Function to connect the game server over TCP and updating tcp_socket of client
    def connect_to_server(self, server_ip: str, server_port: int) -> socket.socket:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((server_ip, server_port))
        self.tcp_socket = tcp_socket

    # Function to handle the game
    def play(self, player_name: str) -> None:
        # Send player name to the server
        self.tcp_socket.sendall(f"{player_name}\n".encode())
        # Print game rules
        print(colors.BOLD_CYAN + "RULES OF THE GAME:\n\tIf your answer is TRUE enter: Y / T / 1\n\t"
              "If your answer is FALSE enter: N / F / 0\n\t"
              "IMPORTANT: If you didn't answer on a question, but you're still\n\t\t\t   "
              "in the game, enter TWO keys - one for the last question (which will not be considered),\n\t\t\t   "
              "and one for the current" + colors.RESET)
        while True:
            # Receive message length header
            msg_len = self.tcp_socket.recv(self.MSG_LEN_HEADER)
            # Receive the message based on the received length
            msg = self.tcp_socket.recv(int.from_bytes(msg_len, byteorder='big'))
            print(colors.Bold_Blue + msg.decode() + colors.RESET)
            # Check if the game is over
            if msg[:len(self.END_GAME_MSG)] != self.END_GAME_MSG:
                # If not, process player answer
                self.process_player_answer()
                self.receive_summary()
            else:
                break

    # Function for getting and sending player's answer
    def process_player_answer(self):
        # Event for stopping the answer sending thread
        stop_flag = threading.Event()
        # Thread to send the answer
        send_key_t = threading.Thread(target=self.send_key, args=(stop_flag,))
        send_key_t.start()
        try:
            # Wait for TIME_TO_SEND_ANS seconds for the player to enter an answer
            send_key_t.join(timeout=self.TIME_TO_SEND_ANS)
            stop_flag.set()
        except threading.ThreadError:
            print(colors.RED + "Error while joining thread" + colors.RESET)

    # Function for sending the player's answer
    def send_key(self, stop_flag: threading.Event) -> None:
        # Get player input for the answer
        key = input(colors.BOLD_CYAN + "Please enter your answer:" + colors.RESET)
        # Validate the answer
        while not self.is_valid_key(key) and not stop_flag.is_set():
            print("Invalid answer")
            key = input(colors.BOLD_CYAN + "Please enter your answer:" + colors.RESET)
        if not stop_flag.is_set():
            # If the stop flag is not set (the timeout didn't happen), send the answer to the server
            self.tcp_socket.sendall(key.encode())

    # Function to validate player answers
    def is_valid_key(self, key: str) -> bool:
        return key in self.KEYS

    # Function to receive the summary from the server
    def receive_summary(self):
        # Receive message length header
        summary_len = self.tcp_socket.recv(self.MSG_LEN_HEADER)
        # Receive the message based on the received length
        summary = self.tcp_socket.recv(int.from_bytes(summary_len, byteorder='big'))
        print(colors.LIGHT_GREEN + summary.decode() + colors.RESET)

    # Function to start the trivia client loop
    def start(self) -> None:
        # Get player name
        player_name = input("please enter your name:")
        print("Client started, listening for offer requests...")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            while True:
                try:
                    # Wait for a game offer
                    server_name, server_ip, server_tcp_port = self.wait_for_offer(udp_socket)
                    print(colors.GREEN + f"Received offer from server {server_name} at address {server_ip}, attempting to connect..." + colors.RESET)
                    try:
                        # Connect to the server
                        self.connect_to_server(server_ip, server_tcp_port)
                    except (socket.error, socket.timeout) as e:
                        print(colors.RED + 'Could not connect to server:' + str(e) + colors.RESET)
                        continue
                    try:
                        # Play the game
                        with self.tcp_socket:
                            self.play(player_name)
                            print(colors.BOLD_CYAN + "Server disconnected, listening for offer requests..." + colors.RESET)
                    except (socket.error, socket.timeout) as e:
                        print(colors.RED + f"Communication error with the server: {e}" + colors.RESET)

                except socket.timeout:
                    print(colors.RED + 'No server found' + colors.RESET)
                    continue
                except InvalidOffer as e:
                    print(colors.RED + e.message + colors.RESET)
                    continue

    def __init__(self):
        self.tcp_socket = None




class InvalidOffer(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


if __name__ == '__main__':
    trivia_client = TriviaClient()
    trivia_client.start()