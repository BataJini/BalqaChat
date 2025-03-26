
## BalqaChat

BalqaChat is terminal based messaging platform


## Installation

1. Clone the repository:
```bash
git clone  https://github.com/BataJini/BalqaChat
cd BalqaChat
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

