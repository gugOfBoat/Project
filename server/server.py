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

def handle_client(client_socket):
    try:
        filename = receive_data(client_socket).decode()
        filesize = int(receive_data(client_socket).decode())
        print(f"Received request to upload file: {filename}, size: {filesize}")

        receive_file(client_socket, filename, filesize)
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
