import socket
import threading
import time
import struct
import random
import select
from config import Colors, Subjects
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
active_clients = []
client_lock = threading.Lock()
# Initialize statistics variables
games_played = 0
players_played = 0
winners = 0
# Define a dictionary to hold the global variable
global_vars = {"TCP_PORT": 0, "last_tcp_connection": float('inf')}  # will be assigned later


def set_tcp_port(port):
    # Modify the value inside the dictionary
    global_vars["TCP_PORT"] = port


def get_tcp_port():
    return global_vars["TCP_PORT"]


def update_last_tcp_connection():
    global_vars["last_tcp_connection"] = time.time()


# Function to handle UDP broadcast
def udp_broadcast():
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
            udp_socket.sendto(offer_message, ('<broadcast>', UDP_PORT))
            time.sleep(1)  # Broadcast every second

    except Exception as e:
        print(Colors.RED + "Error in UDP broadcast:" + str(e) + Colors.RESET)


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


# Function to handle TCP connections from clients
def handle_client(client_socket, client_address):
    player_name = None
    try:
        # Receive player name from client
        player_name = client_socket.recv(1024).decode('utf-8').strip()
        with client_lock:
            clients.append((player_name, client_socket))
        update_last_tcp_connection()  # Update the last TCP connection time

    except Exception as e:
        print(Colors.RED + "Error handling client:" + str(e) + Colors.RESET)
        client_socket.close()
        with client_lock:
            clients.remove((player_name, client_socket))


def start_game():
    global active_clients
    if not clients:
        print(Colors.RED + "No clients connected" + Colors.RESET)
        return

    subject = None
    questions = None
    subjects = [Subjects.subject_0, Subjects.subject_1, Subjects.subject_2, Subjects.subject_3, Subjects.subject_4, Subjects.subject_5,
                Subjects.subject_6, Subjects.subject_7]
    questions_sets = [Subjects.questions_0, Subjects.questions_1, Subjects.questions_2, Subjects.questions_3, Subjects.questions_4,
                     Subjects.questions_5, Subjects.questions_6, Subjects.questions_7]

    if subjects:
        random_number = random.randint(0, 7)
        subject = subjects[random_number]
        questions = questions_sets[random_number]

    welcome_message = f"Welcome to the {server_name} server, where we are answering trivia questions about {subject}\n"
    for i, (client, _) in enumerate(clients):
        welcome_message += f"Player {i + 1}: {client}\n"
    welcome_message += "==\n"
    indicator = 0
    active_clients = clients.copy()  # Initialize active clients as all clients
    for i, question in enumerate(questions):
        # Send the question to all clients
        # if we removed a player that disconncted mid-game, we need to remove him also
        if indicator == 0:
            question_for_start = welcome_message + "\nTrue or false:" + question['question']
            send_question(clients, question_for_start)

        # Wait for 11 seconds
        time.sleep(ANSWER_TIMEOUT)

        # Gather answers from all clients
        answers = collect_answers(active_clients)

        active_users = active_clients.copy()
        # Evaluate answers and prepare result message
        results, active_clients = evaluate_answers(answers, question)  # Update active clients based on answers

        # set the indicator to not add the welcome massage
        indicator = 1

        # Prepare the next question
        next_question = "True or false: " + questions[i + 1]['question'] if i + 1 < len(questions) else None

        # Send result message to each client
        if len(active_clients) == 1:
            send_results(active_users, results)
            send_summary(clients, active_clients[0])
            break
        elif len(active_clients) == 0 and not len(clients) == 0:
            active_clients = active_users
            send_results(active_clients, results)
            send_question(active_clients, next_question)
        elif len(active_clients) == 0 and len(clients) == 0:
            #no clients are connected
            clean_Vars()
            start_of_server()
        else:
            send_results(active_users, results)
            send_question(active_clients, next_question)
    if len(active_clients) == 1:
        update_statistics(len(clients), len(active_clients))
        print_statistics()
        clean_Vars()
        start_of_server()
    else:
        send_summary_mult_winners(clients, active_clients)
        update_statistics(len(clients), len(active_clients))
        print_statistics()
        clean_Vars()
        start_of_server()


def update_statistics(num_players, num_winners):
    global games_played
    global players_played
    global winners

    games_played += 1
    players_played += num_players
    winners += num_winners


def print_statistics():
    print(Colors.LIGHT_YELLOW + "Statistics: " + Colors.RESET)
    print(Colors.GOLDEN_YELLOW + f"Games played: {games_played}" + Colors.RESET)
    print(Colors.GOLDEN_YELLOW + f"Players played: {players_played}" + Colors.RESET)
    print(Colors.YELLOW + f"Winners: {winners}" + Colors.RESET)


def send_results(Round_players, results):
    Round_players_cache = Round_players.copy()
    for client, Player_Socket in Round_players_cache:
        result_message = ''
        for r in results:
            result_message += r + '\n'
        try:
            length = len(result_message)
            Player_Socket.sendall(length.to_bytes(4, byteorder='big'))
            Player_Socket.sendall(result_message.encode('utf-8'))
        except ConnectionResetError:
            print(Colors.BOLD_CYAN + "Client disconnected" + Colors.RESET)
            clients.remove((client, Player_Socket))  # Remove the client from the list
            active_clients.remove((client, Player_Socket))
    print(Colors.BOLD_CYAN + result_message + Colors.RESET)


def send_summary_mult_winners(All_The_Clients, winners):
    Round_players_cache = All_The_Clients.copy()
    result_message = "Game over!\nCongratulations to the winners:"
    for client, _ in winners:
        result_message += client[0] + ","
    result_message = result_message[0:-1]
    for client, Client_sock in Round_players_cache:
        try:
            length = len(result_message)
            Client_sock.sendall(length.to_bytes(4, byteorder='big'))
            Client_sock.sendall(result_message.encode('utf-8'))
        except ConnectionResetError:
            print(Colors.BOLD_CYAN + "Client disconnected" + Colors.RESET)
            clients.remove((client, Client_sock))  # Remove the client from the list
            active_clients.remove((client, Client_sock))
    print(Colors.BOLD_CYAN + result_message + Colors.RESET)


def send_summary(All_The_Clients, winner):
    Round_players_cache = All_The_Clients.copy()
    for client, client_sock in Round_players_cache:
        try:
            result_message = "Game over!\nCongratulations to the winner:" + winner[0] + "\n"
            length = len(result_message)
            client_sock.sendall(length.to_bytes(4, byteorder='big'))
            client_sock.sendall(result_message.encode('utf-8'))
        except ConnectionResetError:
            print(Colors.BOLD_CYAN + "Client disconnected" + Colors.RESET)
            clients.remove((client, client_sock))  # Remove the client from the list
            active_clients.remove((client, client_sock))
    print(Colors.BOLD_CYAN + result_message + Colors.RESET)


def send_question(Players, question):
    players_cache = Players.copy()
    question_message = f"{question}\n"
    print(Colors.BOLD_CYAN + question_message + "Played by:" + Colors.RESET)
    for client, player_socket in players_cache:
        try:
            print(Colors.BOLD_CYAN + client +" " + Colors.RESET)
            length = len(question_message)
            player_socket.sendall(length.to_bytes(4, byteorder='big'))
            player_socket.sendall(question_message.encode('utf-8'))
        except ConnectionResetError:
            print(Colors.BOLD_CYAN + "Client disconnected" + Colors.RESET)
            clients.remove((client, player_socket))  # Remove the client from the list
            active_clients.remove((client, player_socket))


def collect_answers(Players):
    answers = []
    players_cache = Players.copy()
    # Prepare lists for select
    read_sockets = [Player_Sock for _, Player_Sock in Players]
    write_sockets = [Player_Sock for _, Player_Sock in Players]
    error_sockets = []

    # Use select to get the list of sockets ready for reading
    ready_to_read, ready_to_write, _ = select.select(read_sockets, write_sockets, error_sockets, 1)  # Timeout of 1 second

    for client_name, player_socket in players_cache:
        if player_socket in ready_to_read:
            try:
                answer = player_socket.recv(1).decode('utf-8')  # Receive only one character
                if answer == "":
                    print(Colors.RED + "player: " + client_name + " Disconnected in the middle of the game!(without input)\n" + Colors.RESET)
                    clients.remove((client_name, player_socket))  # Remove the client from the list
                    active_clients.remove((client_name, player_socket))
                else:
                    answers.append(((client_name, player_socket), answer))  # Keep track of the full client tuple
            except Exception as e:
                print(Colors.RED + f"An error occurred: {e}\n" + Colors.RESET)
                clients.remove((client_name, player_socket))  # Remove the client from the list
                active_clients.remove((client_name, player_socket))
        else:
            print(Colors.BOLD_CYAN + f"No answer received from {client_name}" + Colors.RESET)
            answers.append(((client_name, player_socket), None))  # Append None if no answer received

    return answers


def evaluate_answers(answers, question):
    results = []
    for i, (client, answer) in enumerate(answers):
        if answer in ('T', 'Y', '1') and question['is_true']:
            results.append(f'{client[0]} is Right!')  # client[0] is the client's name
        elif answer in ('N', 'F', '0') and not question['is_true']:
            results.append(f'{client[0]} is Right!')
        else:
            results.append(f'{client[0]} is Wrong!')
            active_clients.remove(client)  # Now client is the full tuple, so it can be removed from active_clients
    return results, active_clients


# Main function to run the server
def main():
    global server_name
    try:
        get_server_ip()
        # Get server name from user input
        server_name = input("Enter server name: ")
        start_of_server()

    except Exception as e:
        print(Colors.RED + "Error in server:" + str(e) + Colors.RESET)


def start_of_server():
    # Create a TCP socket
    global_vars["last_tcp_connection"] = float('inf')
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
    udp_thread = threading.Thread(target=udp_broadcast)
    udp_thread.daemon = True
    udp_thread.start()

    print(Colors.BOLD_CYAN + "Server started, listening on IP address " + server_address + Colors.RESET)

    # Accept incoming connections and handle clients
    while True:
        client_socket, client_address = tcp_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()


def clean_Vars():
    global clients
    global active_clients
    for client, Clean_The_Sock in clients:
        Clean_The_Sock.close()
    for client, Clean_The_Sock in active_clients:
        Clean_The_Sock.close()
    clients = []
    active_clients = []


# Entry point
if __name__ == "__main__":
    main()