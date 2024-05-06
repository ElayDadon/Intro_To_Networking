from client import TriviaClient
import random


class Bot(TriviaClient):
    # Override function for sending random key
    def process_player_answer(self):
        key = random.choice(self.KEYS)
        self.tcp_socket.sendall(key.encode())


if __name__ == '__main__':
    bot = Bot()
    bot.start()
