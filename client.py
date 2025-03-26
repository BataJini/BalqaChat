import socket
import json
import threading
import sys
import time
from datetime import datetime
import select
import ssl
from cryptography.fernet import Fernet

class ChatClient:
    def __init__(self, host='localhost', port=5000):
        # Handle ngrok URL format
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        
        self.host = host.replace('tcp://', '')
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        self.typing = False
        self.last_typing_update = 0
        self.typing_update_interval = 0.5  # seconds
        self.session_key = None
        print(f"\033[93mAttempting to connect to {self.host}:{self.port}\033[0m")

    def connect(self):
        """Connect to the server"""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and wrap with SSL
            self.socket = context.wrap_socket(self.socket, server_hostname=self.host)
            self.socket.connect((self.host, self.port))
            
            # Receive session key
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
        """Encrypt message using session key"""
        if self.session_key:
            f = Fernet(self.session_key)
            return f.encrypt(message.encode()).decode()
        return message

    def decrypt_message(self, encrypted_message):
        """Decrypt message using session key"""
        if self.session_key:
            f = Fernet(self.session_key)
            return f.decrypt(encrypted_message.encode()).decode()
        return encrypted_message

    def send_typing_status(self, is_typing):
        """Send typing status to server"""
        try:
            message = json.dumps({
                'type': 'typing',
                'is_typing': is_typing
            })
            encrypted_message = self.encrypt_message(message)
            self.socket.send(encrypted_message.encode())
        except Exception as e:
            print(f"\033[91mError sending typing status: {e}\033[0m")

    def receive_messages(self):
        """Receive and display messages from the server"""
        while True:
            try:
                message = self.socket.recv(1024).decode()
                if not message:
                    print("\033[91mDisconnected from server\033[0m")
                    break
                
                try:
                    decrypted_message = self.decrypt_message(message)
                    data = json.loads(decrypted_message)
                    
                    # Clear typing indicator line
                    print('\033[K', end='\r')
                    
                    if data['type'] == 'system':
                        print(f"\n\033[90m[{data['timestamp']}] {data['message']}\033[0m")
                    elif data['type'] == 'typing_status':
                        if data['message']:
                            print(f"\r\033[90m{data['message']}\033[0m", end='', flush=True)
                        else:
                            print('\r\033[K', end='', flush=True)
                    else:  # Regular message
                        if data['username'] == self.username:
                            print(f"\n\033[90m[{data['timestamp']}] \033[95mYou\033[0m: {data['message']}")
                        else:
                            print(f"\n\033[90m[{data['timestamp']}] {data['color']}{data['username']}\033[0m: {data['message']}")
                except json.JSONDecodeError as e:
                    print(f"\033[91mError decoding message: {e}\033[0m")
                    continue
                    
            except Exception as e:
                print(f"\033[91mError receiving message: {e}\033[0m")
                break

    def send_message(self, message):
        """Send message to the server"""
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
        """Start the chat client"""
        if not self.connect():
            return

        # Get username and send it to server
        self.username = input("Enter your username: ")
        username_data = json.dumps({
            'type': 'username',
            'username': self.username
        })
        encrypted_username = self.encrypt_message(username_data)
        self.socket.send(encrypted_username.encode())

        # Start receiving messages in a separate thread
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

        print("\nSecure chat started! Type your messages (press Ctrl+C to exit)")
        print("-" * 50)

        # Main loop for sending messages
        try:
            while True:
                # Check if there's input available
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    # User is typing
                    if not self.typing:
                        self.typing = True
                        self.send_typing_status(True)
                    self.last_typing_update = time.time()
                
                # Update typing status
                if self.typing and time.time() - self.last_typing_update > self.typing_update_interval:
                    self.typing = False
                    self.send_typing_status(False)
                
                # Show typing prompt
                print(f"\r\033[95mYou\033[0m: ", end='', flush=True)
                
                # Get message input
                message = input()
                if self.typing:
                    self.typing = False
                    self.send_typing_status(False)
                self.send_message(message)
                
        except KeyboardInterrupt:
            print("\n\033[93mDisconnecting from server...\033[0m")
            self.socket.close()
            sys.exit()

if __name__ == "__main__":
    # Get host and port from command line arguments or use defaults
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    
    client = ChatClient(host=host, port=port)
    client.start() 