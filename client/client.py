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

def main():
    while True:
        action = input("Bạn muốn tải lên (u) hay tải xuống (d) file? (u/d): ")
        if action.lower() == 'u':
            filename = input("Nhập tên file cần tải lên: ")
            send_file(filename)
        elif action.lower() == 'd':
            filename = input("Nhập tên file cần tải xuống: ")
            # Implement download function here
            pass
        else:
            print("Lựa chọn không hợp lệ.")

if __name__ == "__main__":
    main()
