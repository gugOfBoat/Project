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

def send_chunk(client_socket, chunk_num, chunk_data):
    try:
        send_data(client_socket, chunk_data)
        print(f"Chunk {chunk_num} uploaded successfully.")
    except Exception as e:
        print(f"Error uploading chunk {chunk_num}: {e}")

def send_file(filename):
    try:
        filesize = os.path.getsize(filename)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, SERVER_PORT))

        # Send filename and filesize
        send_data(client_socket, filename.encode())
        send_data(client_socket, str(filesize).encode())

        threads = []
        with open(filename, 'rb') as f:
            chunk_num = 0
            while True:
                chunk_data = f.read(BUFFER_SIZE)
                if not chunk_data:
                    break
                thread = threading.Thread(target=send_chunk, args=(client_socket, chunk_num, chunk_data))
                thread.start()
                threads.append(thread)
                chunk_num += 1

        for thread in threads:
            thread.join()

        client_socket.close()
        print(f"File {filename} uploaded successfully.")

    except Exception as e:
        print(f"Error uploading file {filename}: {e}")

def receive_data(client_socket):
    try:
        data_len_bytes = client_socket.recv(4)
        if not data_len_bytes:
            return None
        data_len = struct.unpack('!I', data_len_bytes)[0]
        data = client_socket.recv(data_len)
        return data
    except Exception as e:
        print(f"Error receiving data: {e}")
        return None

def receive_chunk(client_socket, chunk_num):
    try:
        data_len_bytes = client_socket.recv(4)
        if not data_len_bytes:
            return None
        data_len = struct.unpack('!I', data_len_bytes)[0]
        chunk_data = client_socket.recv(data_len)
        print(f"Received chunk {chunk_num} from server.")
        return chunk_data
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

def download_file(filename):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, SERVER_PORT))

        # Send download request
        send_data(client_socket, b'd')  # Send 'd' to indicate download
        send_data(client_socket, filename.encode())

        # Receive filename from server
        filename_received = receive_data(client_socket)
        if filename_received:
            filename_received = filename_received.decode()
        else:
            raise Exception("Failed to receive filename from server.")

        # Receive filesize from server
        filesize_data = receive_data(client_socket)
        if filesize_data:
            filesize = int(filesize_data.decode())
        else:
            raise Exception("Failed to receive filesize from server.")

        print(f"Downloading file: {filename_received}, size: {filesize} bytes")

        # Receive file data in chunks and write to file
        receive_file(client_socket, filename_received, filesize)

        print(f"File {filename_received} downloaded successfully.")

    except Exception as e:
        print(f"Error downloading file {filename}: {e}")

    finally:
        client_socket.close()


def main():
    while True:
        action = input("Bạn muốn tải lên (u) hay tải xuống (d) file? (u/d): ")
        if action.lower() == 'u':
            filename = input("Nhập tên file cần tải lên: ")
            send_file(filename)
        elif action.lower() == 'd':
            filename = input("Nhập tên file cần tải xuống: ")
            download_file(filename)
        else:
            print("Lựa chọn không hợp lệ.")

if __name__ == "__main__":
    main()

