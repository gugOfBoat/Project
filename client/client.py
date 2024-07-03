import socket
import struct
import os
import threading

SERVER_IP = '192.168.100.100'
SERVER_PORT = 5000
BUFFER_SIZE = 1024 * 1024

def send_data(client_socket, data):
    data_len = len(data)
    client_socket.sendall(struct.pack('!I', data_len))
    client_socket.sendall(data)

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

def send_chunk(client_socket, chunk_num, chunk_data, lock):
    try:
        with lock:
            send_data(client_socket, chunk_data)
        print(f"Chunk {chunk_num} uploaded successfully.")
    except Exception as e:
        print(f"Error uploading chunk {chunk_num}: {e}")

def receive_chunk(client_socket, chunk_num):
    try:
        chunk_data = receive_data(client_socket)
        if chunk_data:
            print(f"Received chunk {chunk_num} from server.")
            return chunk_data
        else:
            print(f"Failed to receive chunk {chunk_num} from server.")
            return None
    except Exception as e:
        print(f"Error receiving chunk {chunk_num}: {e}")
        return None

def send_file(filename):
    try:
        filesize = os.path.getsize(filename)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, SERVER_PORT))

        # Send upload request
        action = 'u'
        send_data(client_socket, action.encode())
        
        # Send filename and filesize
        send_data(client_socket, filename.encode())
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

        client_socket.close()
        print(f"File {filename} uploaded successfully.")

    except Exception as e:
        print(f"Error uploading file {filename}: {e}")

def receive_file(filename):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, SERVER_PORT))

        # Send download request
        action = 'd'
        send_data(client_socket, action.encode())
        send_data(client_socket, filename.encode())

        filesize = int(receive_data(client_socket).decode())
        print(f"File size: {filesize}")

        threads = []
        with open(filename, 'wb') as f:
            chunk_num = 0
            while True:
                chunk_data = receive_chunk(client_socket, chunk_num)
                if not chunk_data:
                    break
                thread = threading.Thread(target=f.write, args=(chunk_data,))
                thread.start()
                threads.append(thread)
                chunk_num += 1

        for thread in threads:
            thread.join()

        client_socket.close()
        print(f"File {filename} downloaded successfully.")

    except Exception as e:
        print(f"Error downloading file {filename}: {e}")

def main():
    while True:
        action = input("Bạn muốn tải lên (u) hay tải xuống (d) file? (u/d): ")
        if action.lower() == 'u':
            filename = input("Nhập tên file cần tải lên: ")
            send_file(filename)
        elif action.lower() == 'd':
            filename = input("Nhập tên file cần tải xuống: ")
            receive_file(filename)
        else:
            print("Lựa chọn không hợp lệ.")

if __name__ == "__main__":
    main()
