import socket
import struct
import os
import threading

SERVER_IP = '192.168.100.100'
SERVER_PORT = 5000
BUFFER_SIZE = 1024 * 1024 

def receive_data(client_socket):
    data_len_bytes = client_socket.recv(4)
    if not data_len_bytes:
        return None
    data_len = struct.unpack('!I', data_len_bytes)[0]
    data = client_socket.recv(data_len)
    return data

def receive_chunk(client_socket, chunk_num):
    try:
        chunk_data = receive_data(client_socket)
        if chunk_data:
            print(f"Received chunk {chunk_num} from client.")
            return chunk_data
        else:
            print(f"Failed to receive chunk {chunk_num} from client.")
            return None
    except Exception as e:
        print(f"Error receiving chunk {chunk_num}: {e}")
        return None

def receive_file(client_socket, filename, filesize):
    try:
        with open(filename, 'wb') as f:
            chunk_num = 0
            while True:
                chunk_data = receive_chunk(client_socket, chunk_num)
                if not chunk_data:
                    break
                f.write(chunk_data)
                chunk_num += 1
            print(f"File {filename} received and saved.")
    except Exception as e:
        print(f"Error receiving file {filename}: {e}")

def send_data(client_socket, data):
    data_len = len(data)
    client_socket.sendall(struct.pack('!I', data_len))
    client_socket.sendall(data)

def send_chunk(client_socket, chunk_data):
    try:
        send_data(client_socket, chunk_data)
    except Exception as e:
        print(f"Error sending chunk: {e}")

def send_file(client_socket, filename):
    try:
        filesize = os.path.getsize(filename)
        with open(filename, 'rb') as f:
            while True:
                chunk_data = f.read(BUFFER_SIZE)
                if not chunk_data:
                    break
                send_chunk(client_socket, chunk_data)
    except Exception as e:
        print(f"Error sending file: {e}")

def handle_client(client_socket):
    try:
        # Receive client's request (upload or download)
        action = receive_data(client_socket).decode()
        if action == 'u':
            # Upload file from client to server
            filename = receive_data(client_socket).decode()
            filesize = int(receive_data(client_socket).decode())
            print(f"Received request to upload file: {filename}, size: {filesize} bytes")

            receive_file(client_socket, filename, filesize)

        elif action == 'd':
            # Download file from server to client
            filename = receive_data(client_socket).decode()
            print(f"Received request to download file: {filename}")

            send_data(client_socket, filename.encode())

            # Ensure file exists
            if os.path.exists(filename):
                send_data(client_socket, str(os.path.getsize(filename)).encode())
                send_file(client_socket, filename)
            else:
                print(f"File {filename} does not exist.")
                send_data(client_socket, b'0')  # Send 0 as file size to indicate file not found

        else:
            print("Invalid action received from client.")

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

    try:
        while True:
            client_socket, address = server_socket.accept()
            print(f"Accepted connection from {address}")
            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()
    except Exception as e:
        print(f"Error accepting connections: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
