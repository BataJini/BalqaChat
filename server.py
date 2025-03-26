import socket
import threading
import json
import sys
from datetime import datetime
import ssl
import hashlib
import secrets
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ChatServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Create SSL context
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.load_cert_chain(certfile="server.crt", keyfile="server.key")
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"\033[92mSecure server started successfully on {host}:{port}\033[0m")
            print(f"\033[93mWaiting for secure connections...\033[0m")
        except Exception as e:
            print(f"\033[91mError starting server: {e}\033[0m")
            sys.exit(1)
            
        self.clients = {}  # Dictionary to store client connections and their usernames
        self.typing_users = set()  # Set to track who is typing
        self.colors = {
            0: '\033[91m',  # Red
            1: '\033[92m',  # Green
            2: '\033[94m',  # Blue
        }
        self.color_reset = '\033[0m'  # Reset color
        self.session_keys = {}  # Store encryption keys for each client

    def generate_session_key(self):
        """Generate a secure session key"""
        return Fernet.generate_key()

    def encrypt_message(self, message, client_socket):
        """Encrypt message for specific client"""
        if client_socket in self.session_keys:
            f = Fernet(self.session_keys[client_socket])
            return f.encrypt(message.encode()).decode()
        return message

    def decrypt_message(self, encrypted_message, client_socket):
        """Decrypt message from specific client"""
        if client_socket in self.session_keys:
            f = Fernet(self.session_keys[client_socket])
            return f.decrypt(encrypted_message.encode()).decode()
        return encrypted_message

    def broadcast(self, message, sender=None):
        """Broadcast message to all connected clients except the sender"""
        for client in self.clients:
            if client != sender:
                try:
                    encrypted_message = self.encrypt_message(json.dumps(message), client)
                    client.send(encrypted_message.encode())
                except Exception as e:
                    print(f"\033[91mError broadcasting to client: {e}\033[0m")
                    self.remove_client(client)

    def handle_client(self, client_socket, address):
        """Handle individual client connections"""
        try:
            print(f"\033[93mNew secure connection attempt from {address}\033[0m")
            
            # Wrap socket with SSL
            secure_socket = self.context.wrap_socket(client_socket, server_side=True)
            
            # Generate and send session key
            session_key = self.generate_session_key()
            secure_socket.send(session_key)
            self.session_keys[secure_socket] = session_key
            
            # Get username from client
            username_data = secure_socket.recv(1024).decode()
            username_data = json.loads(self.decrypt_message(username_data, secure_socket))
            username = username_data['username']
            
            self.clients[secure_socket] = username
            print(f"\033[92mSecure client connected: {username} from {address}\033[0m")
            
            # Assign color based on number of connected clients
            color_index = len(self.clients) - 1
            user_color = self.colors.get(color_index, self.color_reset)
            
            # Send welcome message
            welcome_message = {
                'type': 'system',
                'message': f"Welcome to the secure chat, {user_color}{username}{self.color_reset}!",
                'timestamp': datetime.now().strftime("%H:%M:%S")
            }
            secure_socket.send(self.encrypt_message(json.dumps(welcome_message), secure_socket).encode())
            
            # Broadcast new user joined
            self.broadcast({
                'type': 'system',
                'message': f"{user_color}{username}{self.color_reset} joined the chat",
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })

            while True:
                try:
                    message = secure_socket.recv(1024).decode()
                    if not message:
                        print(f"\033[93mClient disconnected: {username}\033[0m")
                        break
                    
                    decrypted_message = self.decrypt_message(message, secure_socket)
                    data = json.loads(decrypted_message)
                    
                    if data['type'] == 'typing':
                        if data['is_typing']:
                            self.typing_users.add(username)
                        else:
                            self.typing_users.discard(username)
                        
                        typing_list = list(self.typing_users)
                        if typing_list:
                            typing_message = f"{', '.join(typing_list)} {'is' if len(typing_list) == 1 else 'are'} typing..."
                        else:
                            typing_message = ""
                        
                        self.broadcast({
                            'type': 'typing_status',
                            'message': typing_message
                        })
                    
                    else:  # Regular message
                        self.broadcast({
                            'type': 'message',
                            'username': username,
                            'message': data['message'],
                            'color': user_color,
                            'timestamp': datetime.now().strftime("%H:%M:%S")
                        }, secure_socket)
                except json.JSONDecodeError as e:
                    print(f"\033[91mError decoding message from {username}: {e}\033[0m")
                    continue
                except Exception as e:
                    print(f"\033[91mError handling message from {username}: {e}\033[0m")
                    continue

        except Exception as e:
            print(f"\033[91mError handling client {address}: {e}\033[0m")
        finally:
            self.remove_client(secure_socket)

    def remove_client(self, client_socket):
        """Remove client from the connected clients list"""
        if client_socket in self.clients:
            username = self.clients[client_socket]
            self.typing_users.discard(username)
            if client_socket in self.session_keys:
                del self.session_keys[client_socket]
            del self.clients[client_socket]
            client_socket.close()
            print(f"\033[93mClient removed: {username}\033[0m")
            self.broadcast({
                'type': 'system',
                'message': f"{username} left the chat",
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })

    def start(self):
        """Start the server and accept connections"""
        while True:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"\033[93mNew connection from {address}\033[0m")
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.start()
            except Exception as e:
                print(f"\033[91mError accepting connection: {e}\033[0m")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    server = ChatServer(port=port)
    server.start() 