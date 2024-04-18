import socket


def get_my_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)
