import socket
import struct
import os
import threading
import hashlib

SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5000
BUFFER_SIZE = 1024 * 1024 

def receive_data(client_socket):
    data_len_bytes = client_socket.recv(4)
    if not data_len_bytes:
        return None
    data_len = struct.unpack('!I', data_len_bytes)[0]
    data = b''
    while len(data) < data_len:
        packet = client_socket.recv(data_len - len(data))
        if not packet:
            return None
        data += packet
    return data

def send_data(client_socket, data):
    data_len = len(data)
    client_socket.sendall(struct.pack('!I', data_len))
    client_socket.sendall(data)

def calculate_checksum(data):
    checksum = hashlib.sha256(data).hexdigest()
    return checksum

def send_chunk(client_socket, chunk_num, chunk_data, lock):
    try:
        checksum = calculate_checksum(chunk_data)
        data_with_checksum = checksum.encode() + b'::' + chunk_data
        with lock:
            send_data(client_socket, data_with_checksum)
        print(f"Chunk {chunk_num} sent to client successfully.")
    except Exception as e:
        print(f"Error sending chunk {chunk_num}: {e}")

def receive_chunk(client_socket, chunk_num, lock):
    retries = 3  # Số lần thử lại tối đa
    while retries > 0:
        try:
            data_with_checksum = receive_data(client_socket)
            if data_with_checksum:
                received_checksum, chunk_data = data_with_checksum.split(b'::', 1)
                calculated_checksum = calculate_checksum(chunk_data)
                if received_checksum.decode() == calculated_checksum:
                    print(f"Received chunk {chunk_num} from client.")
                    return chunk_data
                else:
                    print(f"Checksum mismatch for chunk {chunk_num}.")
                    # Send chunk again upon request (NACK received)
                    if receive_data(client_socket) == b'NACK':
                        send_chunk(client_socket, chunk_num, chunk_data, lock)
            else:
                print(f"Failed to receive chunk {chunk_num} from client.")
        except Exception as e:
            print(f"Error receiving chunk {chunk_num}: {e}")
        
        retries -= 1

    print(f"Failed to receive chunk {chunk_num} after {retries} retries.")
    return None

def receive_file(client_socket, filename, filesize):
    try:
        with open(filename, 'wb') as f:
            chunk_num = 0
            lock = threading.Lock()
            while True:
                chunk_data = receive_chunk(client_socket, chunk_num, lock)
                if not chunk_data:
                    break
                f.write(chunk_data)
                chunk_num += 1
            print(f"File {filename} received and saved.")
    except Exception as e:
        print(f"Error receiving file {filename}: {e}")

def send_file(client_socket, filename):
    try:
        filesize = os.path.getsize(filename)
        send_data(client_socket, str(filesize).encode())

        threads = []
        lock = threading.Lock()
        with open(filename, 'rb') as f:
            chunk_num = 0
            while True:
                chunk_data = f.read(BUFFER_SIZE)
                if not chunk_data:
                    break
                thread = threading.Thread(target=send_chunk, args=(client_socket, chunk_num, chunk_data, lock))
                thread.start()
                threads.append(thread)
                chunk_num += 1

        for thread in threads:
            thread.join()
        
        print(f"File {filename} sent to client successfully.")
    except Exception as e:
        print(f"Error sending file {filename}: {e}")

def handle_client(client_socket):
    try:
        action = receive_data(client_socket).decode()
        if action == 'u':
            filename = receive_data(client_socket).decode()
            filesize = int(receive_data(client_socket).decode())
            print(f"Received request to upload file: {filename}, size: {filesize}")
            receive_file(client_socket, filename, filesize)
        elif action == 'd':
            filename = receive_data(client_socket).decode()
            print(f"Received request to download file: {filename}")
            send_file(client_socket, filename)
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
