import socket
import config

class Client:
    def __init__(self):
        self.sock = None

    def connect_to_server(self):
        """
        Establishes a TCP connection to the server.
        """
        try:
            # Create a socket object
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(config.TIMEOUT)
            
            # Connect to the server
            self.sock.connect(config.SERVER_ADDR)
            
            # Send a test message
            test_message = "Hello, Server!"
            self.sock.sendall(test_message.encode(config.FORMAT))
            
            # Receive a response
            response = self.sock.recv(1024)
            print(f"Received from server: {response.decode(config.FORMAT)}")
            
            return True
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return False

# Example usage
if __name__ == "__main__":
    client = Client()
    if client.connect_to_server():
        print("Connection established successfully.")
    else:
        print("Connection failed.")
