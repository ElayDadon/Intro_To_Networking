import socket
import threading
import time
import struct
import ipaddress
import netifaces as ni
import random

# Set the broadcast address and port
broadcast_address = 0  # Change this to the appropriate broadcast address
server_address = 0
broadcast_port = 13117

# Global variables
server_name = ""
UDP_PORT = 13117
ANSWER_TIMEOUT = 11  # Timeout for receiving answers in seconds
MAGIC_COOKIE = b'\xab\xcd\xdc\xba'
MESSAGE_TYPE = 2

# Define a list to hold connected clients
clients = []
client_lock = threading.Lock()

subject_1 = "production of coffee mugs in China"
questions_1 = [
    {"question": "China is the largest producer of coffee mugs in the world", "is_true": True},
    {"question": "All coffee mugs produced in China are handmade", "is_true": False},
    {"question": "Porcelain is a common material used in the production of coffee mugs in China", "is_true": True},
    {"question": "The production of coffee mugs in China has no environmental impact", "is_true": False},
    {"question": "The city of Jingdezhen in China is known as the 'Porcelain Capital' and produces coffee mugs",
     "is_true": True},
    {"question": "Coffee mugs production in China is only for domestic use", "is_true": False},
    {"question": "Quality control is an important step in the production of coffee mugs in China", "is_true": True},
    {"question": "All coffee mugs produced in China are exported to the United States", "is_true": False}
]

subject_2 = "tactics and similarities in the 16th and 21st centuries"
questions_2 = [
    {"question": "The 16th and 21st centuries saw similar technological advancements", "is_true": False},
    {"question": "Globalization was a common phenomenon in both the 16th and 21st centuries", "is_true": True},
    {"question": "The tactics used in warfare were similar in the 16th and 21st centuries", "is_true": False},
    {"question": "Both the 16th and 21st centuries experienced significant religious reforms", "is_true": False},
    {"question": "The 16th and 21st centuries were marked by major pandemics", "is_true": True},
    {"question": "Art and culture flourished similarly in the 16th and 21st centuries", "is_true": False},
    {"question": "The 16th and 21st centuries saw similar patterns in migration", "is_true": False},
    {"question": "Both the 16th and 21st centuries were characterized by major political shifts", "is_true": True}
]
subject_3 = "cultivation of Poaceae(grass family) in Europe and the Americas as a means of establishing social status"
questions_3 = [
    {"question": "In the 16th century, was the cultivation of Poaceae in Europe a symbol of wealth?", "is_true": True},
    {"question": "Did the type of Poaceae cultivated in the Americas reflect the social hierarchy?", "is_true": True},
    {"question": "Is the cultivation of Poaceae still used as a status symbol in modern Europe?", "is_true": False},
    {"question": "Were ornamental gardens with Poaceae exclusive to the nobility in the 16th century?",
     "is_true": True},
    {"question": "Did the Americas adopt the European practice of using Poaceae for social distinction?",
     "is_true": True},
    {"question": "Has the symbolic value of Poaceae cultivation diminished in the 21st century?", "is_true": True},
    {"question": "Was the cultivation of Poaceae in public spaces a common practice for social status?",
     "is_true": False},
    {"question": "Did the 21st century see a resurgence in Poaceae cultivation for social status?", "is_true": False}
]

# Define a dictionary to hold the global variable
global_vars = {"TCP_PORT": 0, "last_tcp_connection": time.time()}  # will be assigned later


def set_tcp_port(port):
    # Modify the value inside the dictionary
    global_vars["TCP_PORT"] = port


def get_tcp_port():
    return global_vars["TCP_PORT"]


def update_last_tcp_connection():
    global_vars["last_tcp_connection"] = time.time()


# Function to handle UDP broadcast
def udp_broadcast(server_name):
    try:
        # Create a UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while True:
            # Check if 10 seconds have passed since the last TCP connection
            if time.time() - global_vars["last_tcp_connection"] > ANSWER_TIMEOUT:
                start_game()
                break

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
        update_last_tcp_connection()  # Update the last TCP connection time

    except Exception as e:
        print("Error handling client:", e)
        client_socket.close()
        with client_lock:
            clients.remove((player_name, client_socket))


def start_game():
    if not clients:
        print("No clients connected")
        return

    subjects = [subject_1, subject_2, subject_3]
    questions_sets = [questions_1, questions_2, questions_3]

    if subjects:
        random_number = random.randint(0, 2)
        subject = subjects[random_number]
        questions = questions_sets[random_number]

    welcome_message = f"Welcome to the {server_name} server, where we are answering trivia questions about {subject}\n"
    for i, (client, _) in enumerate(clients):
        welcome_message += f"Player {i + 1}: {client}\n"
    welcome_message += "==\n"

    for i, question in enumerate(questions):
        # Send the question to all clients
        send_question(clients, question)

        # Wait for 11 seconds
        time.sleep(ANSWER_TIMEOUT)

        # Gather answers from all clients
        answers = collect_answers(clients)

        # Evaluate answers and prepare result message
        results = evaluate_answers(answers, question)

        # Prepare the next question
        next_question = questions[i + 1] if i + 1 < len(questions) else None

        # Send result message to each client
        send_results(clients, results, next_question)


def send_results(clients, results, next_question):
    for client, socket in clients:
        result_message = ''
        for c, r in results:
            if c == client:
                result_message += r + '\n'
        if next_question:
            result_message += f"Next question: {next_question['question']}\n"
        length = len(result_message)
        socket.sendall(length.to_bytes(4, byteorder='big'))
        socket.sendall(result_message.encode('utf-8'))


def send_question(clients, question):
    question_message = f"True or false: {question['question']}\n"
    for _, socket in clients:
        length = len(question_message)
        socket.sendall(length.to_bytes(4, byteorder='big'))
        socket.sendall(question_message.encode('utf-8'))


def collect_answers(clients):
    answers = []
    for client, socket in clients:
        try:
            answer = socket.recv(1).decode('utf-8')  # Receive only one character
            answers.append((client, answer))
        except:
            pass
    return answers


def collect_answer(client, socket, event):
    try:
        answer = socket.recv(4)
        setattr(threading.current_thread(), 'answers', [(client, answer)])
    except:
        pass
    event.set()  # Signal that the answer has been received


def evaluate_answers(answers, question):
    results = []
    for i, (client, answer) in enumerate(answers):
        if answer in ('T', 'Y', '1') and question['is_true']:
            results.append((client, f'is Right! (Question {i + 1})'))
        elif answer in ('N', 'F', '0') and not question['is_true']:
            results.append((client, f'is Right! (Question {i + 1})'))
        else:
            results.append((client, f'is Wrong! (Question {i + 1})'))
    return results


# Main function to run the server
def main():
    global server_name
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
        # get the TCP_PORT that was allocated dynamically
        TCP_PORT = tcp_socket.getsockname()[1]
        set_tcp_port(TCP_PORT)
        # Listen for incoming connections
        tcp_socket.listen()

        # Get the dynamically assigned TCP port

        # Start UDP broadcast thread after TCP port assignment
        update_last_tcp_connection()
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
