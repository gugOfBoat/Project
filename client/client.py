import socket
import struct
import os
import threading
import hashlib
import logging

SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5000
BUFFER_SIZE = 1024 * 1024

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Client:
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

    def send_chunk(self, chunk_num, chunk_data):
        retries = 3  # Số lần thử lại tối đa
        while retries > 0:
            try:
                checksum = self.calculate_checksum(chunk_data)
                data_with_checksum = checksum.encode() + b'::' + chunk_data
                with self.lock:
                    self.send_data(data_with_checksum)
                    ack = self.receive_data()
                    if ack.decode() == "ACK":
                        logging.info(f"Chunk {chunk_num} uploaded successfully.")
                        return True  # Thành công, không cần thử lại nữa
            except Exception as e:
                logging.error(f"Error uploading chunk {chunk_num}: {e}")
                retries -= 1
        logging.error(f"Failed to upload chunk {chunk_num} after {retries} retries.")
        return False

    def receive_chunk(self, chunk_num):
        retries = 3  # Số lần thử lại tối đa
        while retries > 0:
            try:
                data_with_checksum = self.receive_data()
                if data_with_checksum:
                    received_checksum, chunk_data = data_with_checksum.split(b'::', 1)
                    calculated_checksum = self.calculate_checksum(chunk_data)
                    if received_checksum.decode() == calculated_checksum:
                        self.send_data(b"ACK")
                        logging.info(f"Received chunk {chunk_num} from server successfully.")
                        return chunk_data
            except Exception as e:
                logging.error(f"Error receiving chunk {chunk_num}: {e}")
                retries -= 1
        logging.error(f"Failed to receive chunk {chunk_num} after {retries} retries.")
        return None

    def upload_file(self, filepath):
        file_size = os.path.getsize(filepath)
        self.send_data(b'u')
        self.send_data(os.path.basename(filepath).encode())
        self.send_data(str(file_size).encode())

        threads = []
        with open(filepath, 'rb') as f:
            chunk_num = 0
            while True:
                chunk_data = f.read(BUFFER_SIZE)
                if not chunk_data:
                    break
                thread = threading.Thread(target=self.send_chunk, args=(chunk_num, chunk_data))
                thread.start()
                threads.append(thread)
                chunk_num += 1

        for thread in threads:
            thread.join()
        
        logging.info(f"File {filepath} uploaded successfully.")

    def download_file(self, filename, destination):
        self.send_data(b'd')
        self.send_data(filename.encode())

        threads = []
        file_chunks = []
        chunk_num = 0
        while True:
            chunk_data = self.receive_chunk(chunk_num)
            if not chunk_data:
                break
            file_chunks.append((chunk_num, chunk_data))
            chunk_num += 1

        with open(destination, 'wb') as f:
            for chunk_num, chunk_data in sorted(file_chunks):
                f.write(chunk_data)
        
        logging.info(f"File {filename} downloaded successfully to {destination}.")

if __name__ == "__main__":
    client = Client(SERVER_IP, SERVER_PORT)
    client.connect()

    action = input("Bạn muốn tải lên (u) hay tải xuống (d) file? (u/d): ").strip()
    if action == 'u':
        filepath = input("Nhập tên file cần tải lên: ").strip()
        client.upload_file(filepath)
    elif action == 'd':
        filename = input("Nhập tên file cần tải xuống: ").strip()
        destination = input("Nhập path lưu file tải xuống").strip()
        client.download_file(filename, destination)

    client.close()
