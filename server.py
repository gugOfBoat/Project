import socket
import config

def start_server():
    """
    Starts a simple TCP server that sends a response to any received message.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind(config.SERVER_ADDR)
        server_sock.listen()
        print(f"Server listening on {config.SERVER_IP}:{config.SERVER_PORT}")

        conn, addr = server_sock.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"Received from client: {data.decode(config.FORMAT)}")
                conn.sendall(b"Hello, Client!")

# Example usage
if __name__ == "__main__":
    start_server()
