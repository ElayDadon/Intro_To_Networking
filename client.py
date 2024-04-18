import socket
import sys
import select


class TriviaClient:
    MAGIC_COOKIE = '\xab\xcd\xdc\xba'
    OFFER_MSG_TYPE = 2
    BROADCAST_PORT = 13117

    def __init__(self):
        self.server_port = None

    def wait_for_offer(self, udp_socket):
        # Bind the UDP socket to a specific address and port
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(("", self.BROADCAST_PORT))
        print("Client started, listening for offer requests...")
        data, server_addr = udp_socket.recvfrom(1024)

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            while True:
                # wait for a game
                try:
                    self.wait_for_offer(udp_socket)
                except socket.timeout:
                    print('No server found')
                    continue
                self.server_port = 3
                server_port = int(data.decode())
                print(f'Found server at {server_addr[0]}:{server_port}')
                state = 'connecting_to_server'

                if state == 'connecting_to_server':
                    # Connect to the server
                    try:
                        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        tcp_socket.connect((server_addr[0], server_port))
                    except socket.error as e:
                        print('Could not connect to server:', str(e))
                        sys.exit()

                    # Set state to 'game_mode'
                    state = 'game_mode'

                elif state == 'game_mode':
                    # Game mode
                    # Collect characters from the keyboard and send them over TCP
                    # Collect data from the network and print it on screen
                    # Use select() to wait for both keyboard input and incoming data
                    readable, writable, exceptional = select.select([tcp_socket, sys.stdin], [], [tcp_socket])

                    for sock in readable:
                        if sock == tcp_socket:
                            # Handle incoming data
                            data = sock.recv(1024)
                            if not data:
                                print('Disconnected from server')
                                sys.exit()
                            else:
                                print('Received:', data.decode())

                        elif sock == sys.stdin:
                            # Handle keyboard input
                            message = sys.stdin.readline().strip()
                            tcp_socket.sendall(message.encode())


