import socket
import struct
import os
import threading
import hashlib
import logging
import time
from customtkinter import *
from tkinter import filedialog, messagebox

SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5000

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Client:
    BUFFER_SIZE = 1024 * 1024

    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock = threading.Lock()

    def connect(self):
        self.client_socket.connect((self.server_ip, self.server_port))

    def close(self):
        self.client_socket.close()
        
    def send_data(self, data):
        data_len = len(data)
        self.client_socket.sendall(struct.pack('!I', data_len))
        self.client_socket.sendall(data)

    def receive_data(self):
        data_len_bytes = self.client_socket.recv(4)
        if not data_len_bytes:
            return None
        data_len = struct.unpack('!I', data_len_bytes)[0]
        data = b''
        while len(data) < data_len:
            packet = self.client_socket.recv(data_len - len(data))
            if not packet:
                return None
            data += packet
        return data

    def calculate_checksum(self, data):
        return hashlib.sha256(data).hexdigest()

    def send_chunk(self, chunk_num, chunk_data, ch = False, share_queue = None):
        retries = 3  # Số lần thử lại tối đa
        while retries > 0:
            try:
                checksum = self.calculate_checksum(chunk_data)
                data_with_checksum_chunk_num = checksum.encode() + b'::' + str(chunk_num).encode() + b'::' + chunk_data
                with self.lock:
                    self.send_data(data_with_checksum_chunk_num)
                    ack = self.receive_data()
                    if ack.decode() == "ACK":
                        if ch == True:
                            share_queue.put(len(chunk_data))
                        logging.info(f"Chunk {chunk_num} uploaded successfully.")
                        return True  # Thành công, không cần thử lại nữa
            except Exception as e:
                logging.error(f"Error uploading chunk {chunk_num}: {e}")
                retries -= 1
        logging.error(f"Failed to upload chunk {chunk_num} after {retries} retries.")
        return False

    def receive_chunk(self):
        retries = 3  # Số lần thử lại tối đa
        while retries > 0:
            try:
                data_with_checksum = self.receive_data()
                if data_with_checksum:
                    received_checksum, chunk_num, chunk_data = data_with_checksum.split(b'::', 2)
                    calculated_checksum = self.calculate_checksum(chunk_data)
                    if received_checksum.decode() == calculated_checksum:
                        self.send_data(b"ACK")
                        logging.info(f"Chunk {chunk_num.decode()} received successfully.")
                        return chunk_num, chunk_data
            except Exception as e:
                logging.error(f"Error receiving chunk: {e}")
                retries -= 1
        logging.error(f"Failed to receive chunk after {retries} retries.")
        return None

    def upload_file(self, filepath, ch = False, share_queue = None):
        self.send_data(b'u')
        self.send_data(os.path.basename(filepath).encode())

        threads = []
        with open(filepath, 'rb') as f:
            chunk_num = 0
            while True:
                chunk_data = f.read(self.BUFFER_SIZE)
                if not chunk_data:
                    time.sleep(0.2)
                    thread = threading.Thread(target=self.send_chunk, args=(chunk_num, "".encode()))
                    thread.start()
                    threads.append(thread)
                    break
                #time.sleep(0.5)
                thread = threading.Thread(target=self.send_chunk, args=(chunk_num, chunk_data, ch, share_queue))
                thread.start()
                threads.append(thread)
                chunk_num += 1

        for thread in threads:
            thread.join()

        logging.info(f"File {os.path.basename(filepath)} uploaded successfully.")

    def download_file(self, filename, destination, ch = False, share_queue = None):
        self.send_data(b'd')
        self.send_data(filename.encode())
        filesize = self.receive_data().decode()
        if ch == True:
            share_queue.put(int(filesize))

        file_chunks = []
        while True:
            chunk_num, chunk_data = self.receive_chunk()
            if not chunk_data:
                break
            if ch == True:
                share_queue.put(len(chunk_data))
            # time.sleep(0.5)
            file_chunks.append((int(chunk_num.decode()), chunk_data))


        filepath = os.path.join(destination, filename)
        with open(filepath, 'wb') as f:
            for chunk_num, chunk_data in sorted(file_chunks):
                f.write(chunk_data)

        logging.info(f"File {os.path.basename(filename)} received successfully.")

    def list(self):
        list_file = []
        try:
            self.send_data(b'r')
        except Exception as e :
            logging.error(f"Error connecting: {e}")
            raise
        no_files = self.receive_data()
        for i in range(0, int(no_files.decode())):
            file_name, file_size = self.receive_data().split(b'::', 1)
            list_file.append((file_name.decode(), file_size.decode()))
        return list_file

    def delete_file(self, filename):
        try:
            self.send_data(b'x')
        except Exception as e :
            logging.error(f"Error connecting: {e}")
            return
        self.send_data(filename.encode())
        response = self.receive_data()
        if response.decode() == "success":
            logging.info(f"Deleted file: {filename}")
        else:
            logging.error(f"Failed to delete file: {filename}")

if __name__ == "__main__":
    client = Client(SERVER_IP, SERVER_PORT)
    client.connect()

    while True:
        action = input("Bạn muốn tải lên (u), tải xuống (d), liệt kê (r) hay xóa (x) file? (u/d/r/x): ").strip()
        if action == 'u':
            filepath = input("Nhập tên file cần tải lên: ").strip()
            client.upload_file(filepath)
        elif action == 'd':
            filename = input("Nhập tên file cần tải xuống: ").strip()
            destination = input("Nhập path lưu file tải xuống: ").strip()
            client.download_file(filename, destination)
        elif action == 'r':
            files = client.list()
            for file in files:
                print(f"{file[0]}: {file[1]} bytes")
        elif action == 'x':
            filename = input("Nhập tên file cần xóa: ").strip()
            client.delete_file(filename)
        elif action == 'l':
            break

    client.close()