import socket
import threading
import time
from time import sleep


# Set the broadcast address and port
broadcast_address = '172.20.10.15' # this is the broadcast ip address on my iphone, it will need to change on another network
broadcast_port = 13117

# Global variables
UDP_PORT = 13117
TCP_PORT = 0  # Will be assigned dynamically
MAX_CLIENTS = 3
ANSWER_TIMEOUT = 10  # Timeout for receiving answers in seconds

# Define a list of trivia questions
# You can replace these with your own set of questions
TRIVIA_QUESTIONS = [
    {
        "question": "Question 1: [Your question here]",
        "answer": True
    },
    {
        "question": "Question 2: [Your question here]",
        "answer": False
    },
    # Add more questions as needed
]

# Define a list to hold connected clients
clients = []
client_lock = threading.Lock()



# Function to handle UDP broadcast
# Function to handle UDP broadcast
def udp_broadcast(server_name):
    try:
        # Create a UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while True:
            # Broadcast offer message
            offer_message = b'\xab\xcd\xdc\xba\x02' + server_name.ljust(32).encode('utf-8') + \
                            TCP_PORT.to_bytes(2, byteorder='big')
            udp_socket.sendto(offer_message, ('<broadcast>', UDP_PORT))
            time.sleep(1)  # Broadcast every second

    except Exception as e:
        print("Error in UDP broadcast:", e)


# Function to handle TCP connections from clients
def handle_client(client_socket, client_address):
    try:
        # Receive player name from client
        player_name = client_socket.recv(1024).decode('utf-8').strip()
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
    global TCP_PORT
    try:
        # Get server name from user input
        server_name = input("Enter server name: ")

        # Start UDP broadcast thread
        udp_thread = threading.Thread(target=udp_broadcast, args=(server_name,))
        udp_thread.daemon = True
        udp_thread.start()

        print("Server started, listening on IP address" + broadcast_address)

        # Wait for a brief period before creating TCP socket
        time.sleep(2)

        # Create a TCP socket
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind the socket to a port
        tcp_socket.bind(('0.0.0.0', TCP_PORT))

        # Listen for incoming connections
        tcp_socket.listen(MAX_CLIENTS)

        # Get the dynamically assigned TCP port

        TCP_PORT = tcp_socket.getsockname()[1]

        print("TCP server ready to accept connections on port:", TCP_PORT)

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