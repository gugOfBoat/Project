import socket
import struct
import os
import threading
import hashlib
import logging
import time

SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5000
BUFFER_SIZE = 1024 * 1024
SERVER_FOLDER = "server"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Server:
    def __init__(self, server_ip, server_port, server_folder):
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock = threading.Lock()
        self.folder = server_folder
        

    def start(self):
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
            print(f"\"{self.folder}\" Created")
        else:
            print(f"\"{self.folder}\" Found")

        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(5)
        logging.info(f"Server listening on {self.server_ip}:{self.server_port}")

        try:
            while True:
                client_socket, address = self.server_socket.accept()
                logging.info(f"Accepted connection from {address}")
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_handler.start()
        except Exception as e:
            logging.error(f"Error accepting connections: {e}")
        finally:
            self.server_socket.close()

    def send_data(self, client_socket, data):
        data_len = len(data)
        client_socket.sendall(struct.pack('!I', data_len))
        client_socket.sendall(data)

    def receive_data(self, client_socket):
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

    def calculate_checksum(self, data):
        return hashlib.sha256(data).hexdigest()
    
    def send_chunk(self, client_socket, chunk_num, chunk_data):
        retries = 3  # Số lần thử lại tối đa
        while retries > 0:
            try:
                checksum = self.calculate_checksum(chunk_data)
                data_with_checksum_chunk_num = checksum.encode() + b'::' + str(chunk_num).encode() +  b'::' + chunk_data
                with self.lock:
                    self.send_data(client_socket, data_with_checksum_chunk_num)
                    ack = self.receive_data(client_socket)
                    if ack.decode() == "ACK":
                        logging.info(f"Chunk {chunk_num} uploaded successfully.")
                        return True  # Thành công, không cần thử lại nữa
            except Exception as e:
                logging.error(f"Error uploading chunk {chunk_num}: {e}")
                retries -= 1
        logging.error(f"Failed to upload chunk {chunk_num} after {retries} retries.")
        return False

    def receive_chunk(self, client_socket):
        retries = 3  # Số lần thử lại tối đa
        while retries > 0:
            try:
                data_with_checksum = self.receive_data(client_socket)
                if data_with_checksum:
                    received_checksum, chunk_num, chunk_data = data_with_checksum.split(b'::', 2)
                    calculated_checksum = self.calculate_checksum(chunk_data)
                    if received_checksum.decode() == calculated_checksum:
                        self.send_data(client_socket, b"ACK")
                        logging.info(f"Chunk {chunk_num.decode()} received successfully.")
                        return chunk_num, chunk_data
            except Exception as e:
                logging.error(f"Error receiving chunk: {e}")
                retries -= 1
        logging.error(f"Failed to receive chunk after {retries} retries.")
        return None

    def receive_file(self, client_socket, filename):

        file_chunks = []
        while True:
            chunk_num, chunk_data = self.receive_chunk(client_socket)
            if not chunk_data:
                break
            file_chunks.append((int(chunk_num.decode()), chunk_data))

        filename = os.path.join(self.folder, filename)
        with open(filename, 'wb') as f:
            for chunk_num, chunk_data in sorted(file_chunks):
                f.write(chunk_data)
        
        logging.info(f"File {os.path.basename(filename)} received successfully.")

    def send_file(self, client_socket, filename):
        try:
            threads = []
            with open(filename, 'rb') as f:
                chunk_num = 0
                while True:
                    chunk_data = f.read(BUFFER_SIZE)
                    if not chunk_data:
                        time.sleep(0.2)
                        thread = threading.Thread(target=self.send_chunk, args=(client_socket, chunk_num, "".encode()))
                        thread.start()
                        threads.append(thread)
                        break
                    thread = threading.Thread(target=self.send_chunk, args=(client_socket, chunk_num, chunk_data))
                    thread.start()
                    threads.append(thread)
                    chunk_num += 1

            for thread in threads:
                thread.join()

            logging.info(f"File {os.path.basename(filename)} sent successfully.")
        except FileNotFoundError:
            logging.error(f"File {os.path.basename(filename)} not found.")
            self.send_data(client_socket, b'File not found.')

    def list(self, client_socket):
        no_files = len([name for name in os.listdir(self.folder) if os.path.isfile(os.path.join(self.folder,name))])
        self.send_data(client_socket, str(no_files).encode())

        for filename in os.listdir(self.folder):
            filepath = os.path.join(self.folder, filename)
            file_size = os.path.getsize(filepath)
            data = filename.encode() + b'::' + str(file_size).encode()
            self.send_data(client_socket, data)


    def handle_client(self, client_socket):
        try:
            while True:
                action = self.receive_data(client_socket)
                if action is None:
                    break

                if action == b'u':
                    filename = self.receive_data(client_socket).decode()
                    self.receive_file(client_socket, filename)
                elif action == b'd':
                    filename = self.receive_data(client_socket).decode()
                    filename = os.path.join(self.folder, filename)
                    self.send_file(client_socket, filename)
                elif action == b'r':
                    self.list(client_socket)
        except Exception as e:
            logging.error(f"Error handling client: {e}")
        finally:
            client_socket.close()
            logging.info("Client connection closed.")

if __name__ == "__main__":
    server = Server(SERVER_IP, SERVER_PORT, SERVER_FOLDER)
    server.start()
