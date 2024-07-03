import socket
import struct
import os
import threading
import hashlib

SERVER_IP = socket.gethostbyname(socket.gethostname())
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

def calculate_checksum(data):
    checksum = hashlib.sha256(data).hexdigest()
    return checksum

def send_chunk(client_socket, chunk_num, chunk_data, lock):
    retries = 3  # Số lần thử lại tối đa
    while retries > 0:
        try:
            checksum = calculate_checksum(chunk_data)
            data_with_checksum = checksum.encode() + b'::' + chunk_data
            with lock:
                send_data(client_socket, data_with_checksum)
            print(f"Chunk {chunk_num} uploaded successfully.")
            return True  # Thành công, không cần thử lại nữa
        except Exception as e:
            print(f"Error uploading chunk {chunk_num}: {e}")
            retries -= 1

    print(f"Failed to upload chunk {chunk_num} after {retries} retries.")
    return False

def receive_chunk(client_socket, chunk_num):
    retries = 3  # Số lần thử lại tối đa
    while retries > 0:
        try:
            data_with_checksum = receive_data(client_socket)
            if data_with_checksum:
                received_checksum, chunk_data = data_with_checksum.split(b'::', 1)
                calculated_checksum = calculate_checksum(chunk_data)
                if received_checksum.decode() == calculated_checksum:
                    print(f"Received chunk {chunk_num} from server.")
                    return chunk_data
                else:
                    print(f"Checksum mismatch for chunk {chunk_num}. Requesting retransmission...")
                    # Send NACK to server for retransmission
                    send_data(client_socket, b'NACK')
            else:
                print(f"Failed to receive chunk {chunk_num} from server.")
        except Exception as e:
            print(f"Error receiving chunk {chunk_num}: {e}")
        
        retries -= 1

    print(f"Failed to receive chunk {chunk_num} after {retries} retries.")
    return None


def send_file(filename):
    try:
        filesize = os.path.getsize(filename)
        filepath = filename.split("/")[-1]
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, SERVER_PORT))

        # Send upload request
        action = 'u'
        send_data(client_socket, action.encode())
        
        # Send filename and filesize
        send_data(client_socket, filepath.encode())
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
