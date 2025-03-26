# Secure Terminal Chat

A secure, terminal-based chat application with end-to-end encryption and real-time typing indicators.

## Features

- End-to-end encryption using Fernet (symmetric encryption)
- SSL/TLS secure connection
- Real-time typing indicators
- Colored usernames
- Timestamp for messages
- System messages for user join/leave events

## Prerequisites

- Python 3.x
- pip (Python package installer)
- OpenSSL (for generating SSL certificates)

## Installation

1. Clone the repository:
```bash
git clone  https://github.com/BataJini/ChatUnix
cd ChatUnix
```

2. Install required packages:
```bash
pip3 install -r requirements.txt
```

3. Generate SSL certificates:
```bash
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes
```

## Usage

1. Start the server:
```bash
python3 server.py 8081
```

2. Start a client (in a new terminal):
```bash
python3 client.py localhost 8081
```

3. Start another client (in another terminal):
```bash
python3 client.py localhost 8081
```

4. For remote connections, use ngrok:
```bash
# Start ngrok
ngrok tcp 8081

# Connect using the ngrok URL
python3 client.py your-ngrok-url 8081
```

## Security Features

- SSL/TLS encryption for the connection
- End-to-end encryption for messages using Fernet
- Unique session keys for each client
- Protection against:
  - Man-in-the-middle attacks
  - Message interception
  - Message tampering
  - Eavesdropping

