import socket
import json
import threading
import sys
import time
from datetime import datetime
import select
import ssl
from cryptography.fernet import Fernet

def print_title():
    print("""\n ▄▄▄▄    ▄▄▄       ██▓      █████   ▄▄▄      
▓█████▄ ▒████▄    ▓██▒    ▒██▓  ██▒▒████▄    
▒██▒ ▄██▒██  ▀█▄  ▒██░    ▒██▒  ██░▒██  ▀█▄  
▒██░█▀  ░██▄▄▄▄██ ▒██░    ░██  █▀ ░░██▄▄▄▄██ 
░▓█  ▀█▓ ▓█   ▓██▒░██████▒░▒███▒█▄  ▓█   ▓██▒
░▒▓███▀▒ ▒▒   ▓▒█░░ ▒░▓  ░░░ ▒▒░ ▒  ▒▒   ▓▒█░
▒░▒   ░   ▒   ▒▒ ░░ ░ ▒  ░ ░ ▒░  ░   ▒   ▒▒ ░
 ░    ░   ░   ▒     ░ ░      ░   ░   ░   ▒   
 ░            ░  ░    ░  ░    ░          ░  ░
      ░       """)
    print("=" * 50)

class ChatClient:
    def __init__(self, host='localhost', port=5000):
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        
        self.host = host.replace('tcp://', '')
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        self.session_key = None
        print(f"\033[93mAttempting to connect to {self.host}:{self.port}\033[0m")

    def connect(self):
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            self.socket = context.wrap_socket(self.socket, server_hostname=self.host)
            self.socket.connect((self.host, self.port))
            
            self.session_key = self.socket.recv(1024)
            
            print("\033[92mSecure connection established!\033[0m")
            return True
        except Exception as e:
            print(f"\033[91mFailed to connect to server: {e}\033[0m")
            print("\033[93mPlease check if:")
            print("1. The server is running")
            print("2. The port number is correct")
            print("3. If using ngrok, the URL is correct and ngrok is running\033[0m")
            return False

    def encrypt_message(self, message):
        if self.session_key:
            f = Fernet(self.session_key)
            return f.encrypt(message.encode()).decode()
        return message

    def decrypt_message(self, encrypted_message):
        if self.session_key:
            f = Fernet(self.session_key)
            return f.decrypt(encrypted_message.encode()).decode()
        return encrypted_message

    def receive_messages(self):
        while True:
            try:
                message = self.socket.recv(1024).decode()
                if not message:
                    print("\033[91mDisconnected from server\033[0m")
                    break
                
                try:
                    decrypted_message = self.decrypt_message(message)
                    data = json.loads(decrypted_message)
                    
                    print('\r\033[K', end='')
                    
                    if data['type'] == 'system':
                        print(f"\n\033[90m[{data['timestamp']}] {data['message']}\033[0m")
                    else:
                        if data['username'] == self.username:
                            print(f"\n\033[95mYou\033[0m: {data['message']}")
                        else:
                            print(f"\n{data['color']}{data['username']}\033[0m: {data['message']}")
                    
                    print(f"\r\033[95mYou\033[0m: ", end='', flush=True)
                except json.JSONDecodeError as e:
                    print(f"\033[91mError decoding message: {e}\033[0m")
                    continue
                    
            except Exception as e:
                print(f"\033[91mError receiving message: {e}\033[0m")
                break

    def send_message(self, message):
        try:
            message_data = json.dumps({
                'type': 'message',
                'message': message
            })
            encrypted_message = self.encrypt_message(message_data)
            self.socket.send(encrypted_message.encode())
        except Exception as e:
            print(f"\033[91mError sending message: {e}\033[0m")

    def start(self):
        if not self.connect():
            return

        self.username = input("Enter your username: ")
        username_data = json.dumps({
            'type': 'username',
            'username': self.username
        })
        encrypted_username = self.encrypt_message(username_data)
        self.socket.send(encrypted_username.encode())

        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

        print("\nSecure chat started! Type your messages (press Ctrl+C to exit)")
        print("-" * 50)

        try:
            while True:
                print(f"\r\033[95mYou\033[0m: ", end='', flush=True)
                
                message = input()
                
                if message.strip():
                    self.send_message(message)
                    print(f"\r\033[95mYou\033[0m: ", end='', flush=True)
                
        except KeyboardInterrupt:
            print("\n\033[93mDisconnecting from server...\033[0m")
            self.socket.close()
            sys.exit()

if __name__ == "__main__":
    print_title()
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    
    client = ChatClient(host=host, port=port)
    client.start() 