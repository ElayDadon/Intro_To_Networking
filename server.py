import socket
from time import sleep

# Set the broadcast address and port
broadcast_address = '172.20.10.15' # this is the broadcast ip address on my iphone, it will need to change on another network
broadcast_port = 13117

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set the socket to broadcast mode
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(("", 0))
# Send the message to the broadcast address and port
message = b"your very important message"
while True:
    sock.sendto(message, (broadcast_address, broadcast_port))
    print("message sent!", flush=True)
    sleep(1)
print("closing")
# Close the socket
sock.close()