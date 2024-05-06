# Trivia Game Client-Server Application

Welcome to our Trivia Game Client-Server Application! This project allows players to participate in a trivia contest where they receive random facts and must answer correctly as fast as possible. This README will guide you through setting up and running both the client and server applications.

## Table of Contents

1. [Introduction](#introduction)
2. [Requirements](#requirements)
3. [Server Application](#server-application)
    - [Usage](#usage-server)
4. [Client Application](#client-application)
    - [Usage](#usage-client)
5. [Bot Application](#bot-application)
    - [Usage](#usage-bot)
6. [Team Information](#team-information)
7. [Example Run](#example-run)

<a name="introduction"></a>
## Introduction

The Trivia Game Client-Server Application is designed for teams to participate in a trivia contest. The server manages the game, sends trivia questions to clients, and evaluates answers. Clients connect to the server, receive questions, and submit answers. The bot application behaves similarly to a client but automatically selects random answers.

<a name="requirements"></a>
## Requirements

- Python 3.x
- Knowledge of command line interface
- Basic understanding of networking concepts

<a name="server-application"></a>
## Server Application

The server application manages the trivia game, sends questions to clients, and evaluates answers.

<a name="usage-server"></a>
### Usage

1. Open a terminal window.
2. Navigate to the directory containing `server.py`.
3. Run the server application using the following command:

```
python server.py
```

4. Enter the server name when prompted.
5. The server will start and listen for incoming connections from clients.

<a name="client-application"></a>
## Client Application

The client application allows players to connect to the server, receive trivia questions, and submit answers.

<a name="usage-client"></a>
### Usage

1. Open a terminal window.
2. Navigate to the directory containing `client.py`.
3. Run the client application using the following command:

```
python client.py
```

4. Enter your name when prompted.
5. The client will listen for server offers and attempt to connect when an offer is received.

<a name="bot-application"></a>
## Bot Application

The bot application behaves like a client but automatically selects random answers to trivia questions.

<a name="usage-bot"></a>
### Usage

1. Open a terminal window.
2. Navigate to the directory containing `bot.py`.
3. Run the bot application using the following command:

```
python bot.py
```

4. The bot will automatically connect to the server, receive questions, and submit random answers.

<a name="team-information"></a>
## Team Information

- **Team Name:** ChocoChamps
- **Team Members:**
    - Elay Dadon
    - Yosef Avraham Hadad
    - Amit Levinz

<a name="example-run"></a>
## Example Run

Below is an example run of the Trivia Game Client-Server Application:

1. The server starts and begins broadcasting offers.
2. Clients receive the offer, connect to the server, and enter their names.
3. The game begins with a trivia question sent to all clients.
4. Clients submit answers, and the server evaluates them.
5. The game continues until a winner is determined.
6. The server sends a summary message with the winner's name.

Thank you for using our Trivia Game Client-Server Application! If you have any questions or feedback, please feel free to reach out to our team.
