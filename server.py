import socket
import threading
import time
import struct
import ipaddress
import netifaces as ni

# Set the broadcast address and port
broadcast_address = 0  # Change this to the appropriate broadcast address
server_address = 0
broadcast_port = 13117


# Global variables
UDP_PORT = 13117
ANSWER_TIMEOUT = 10  # Timeout for receiving answers in seconds
MAGIC_COOKIE = b'\xab\xcd\xdc\xba'
MESSAGE_TYPE = 2

# Define a list to hold connected clients
clients = []
client_lock = threading.Lock()

# Define a dictionary to hold the global variable
global_vars = {"TCP_PORT": 0}  # will be assigned later


def set_tcp_port(port):
    # Modify the value inside the dictionary
    global_vars["TCP_PORT"] = port


def get_tcp_port():
    return global_vars["TCP_PORT"]


# Function to handle UDP broadcast
def udp_broadcast(server_name):
    try:
        # Create a UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while True:
            # Pack the server name and port into the offer message
            offer_message = struct.pack('!4sB32sH', MAGIC_COOKIE, MESSAGE_TYPE, server_name.encode('utf-8').ljust(32),
                                        get_tcp_port())

            # Broadcast offer message
            udp_socket.sendto(offer_message, (broadcast_address, UDP_PORT))
            time.sleep(1)  # Broadcast every second

    except Exception as e:
        print("Error in UDP broadcast:", e)


# function to handle getting the broadcast address
def get_server_ip():
    global server_address
    hostname = socket.gethostname()  # Get the host name of the machine
    ip_address = socket.gethostbyname(hostname)  # Get the IP address associated with the hostname
    server_address = str(ip_address)


def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


def get_network_mask():
    interfaces = ni.interfaces()
    for i in interfaces:
        try:
            ip = ni.ifaddresses(i)[ni.AF_INET][0]['addr']
            netmask = ni.ifaddresses(i)[ni.AF_INET][0]['netmask']
            if ip == get_ip_address():
                return netmask
        except KeyError:
            pass
    return None


def get_broadcast_ip():
    global broadcast_address

    IP = get_ip_address()
    MASK = get_network_mask()
    net = ipaddress.IPv4Network(IP + '/' + MASK, False)
    broadcast_address = str(net.broadcast_address)


# Function to handle TCP connections from clients
def handle_client(client_socket, client_address):
    try:
        # Receive player name from client
        player_name = client_socket.recv(1024).decode('utf-8').strip()
        print(player_name)
        with client_lock:
            clients.append((player_name, client_socket))

        # Handle game logic for this client
        # You can implement this part based on the task requirements

    except Exception as e:
        print("Error handling client:", e)
    finally:
        # Close client socket
        client_socket.close()
        with client_lock:
            clients.remove((player_name, client_socket))


# Main function to run the server
def main():
    try:
        get_broadcast_ip()
        get_server_ip()
        print(broadcast_address)
        # Get server name from user input
        server_name = input("Enter server name: ")

        # Create a TCP socket
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to a port
        tcp_socket.bind(('0.0.0.0', 0))
        #get the TCP_PORT that was allocated dynamically
        TCP_PORT = tcp_socket.getsockname()[1]
        set_tcp_port(TCP_PORT)
        # Listen for incoming connections
        tcp_socket.listen()

        # Get the dynamically assigned TCP port

        # Start UDP broadcast thread after TCP port assignment
        udp_thread = threading.Thread(target=udp_broadcast, args=(server_name,))
        udp_thread.daemon = True
        udp_thread.start()

        print("Server started, listening on IP address", server_address)

        # Accept incoming connections and handle clients
        while True:
            client_socket, client_address = tcp_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()

    except Exception as e:
        print("Error in server:", e)
    finally:
        tcp_socket.close()


# Entry point
if __name__ == "__main__":
    main()
