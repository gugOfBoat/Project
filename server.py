import socket
import struct
import os
import threading
import hashlib
import logging
import time
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5000
BUFFER_SIZE = 1024 * 1024
SERVER_FOLDER = "server"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Server:
    def __init__(self, server_ip, server_port, server_folder, ui):
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock = threading.Lock()
        self.folder = server_folder
        self.ui = ui
        self.client_count = 0

    def start(self):
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
            self.ui.log_message(f"\"{self.folder}\" Created")
        else:
            self.ui.log_message(f"\"{self.folder}\" Found")

        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(5)
        self.ui.log_message(f"Server listening on {self.server_ip}:{self.server_port}")

        try:
            while True:
                client_socket, address = self.server_socket.accept()
                self.ui.log_message(f"Accepted connection from {address}")
                self.client_count += 1
                self.ui.update_client_count(self.client_count)
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
                data_with_checksum_chunk_num = checksum.encode() + b'::' + str(chunk_num).encode() + b'::' + chunk_data
                with self.lock:
                    self.send_data(client_socket, data_with_checksum_chunk_num)
                    ack = self.receive_data(client_socket)
                    if ack.decode() == "ACK":
                        self.ui.log_message(f"Chunk {chunk_num} uploaded successfully at {datetime.now()}.")
                        self.ui.update_chunk_number(chunk_num)
                        return True  # Thành công, không cần thử lại nữa
            except Exception as e:
                self.ui.log_message(f"Error uploading chunk {chunk_num}: {e}")
                retries -= 1
        self.ui.log_message(f"Failed to upload chunk {chunk_num} after {retries} retries at {datetime.now()}.")
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
                        self.ui.log_message(f"Chunk {chunk_num.decode()} received successfully at {datetime.now()}.")
                        self.ui.update_chunk_number(int(chunk_num.decode()))
                        return chunk_num, chunk_data
            except Exception as e:
                self.ui.log_message(f"Error receiving chunk: {e}")
                retries -= 1
        self.ui.log_message(f"Failed to receive chunk after {retries} retries at {datetime.now()}.")
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

        self.ui.log_message(f"File {os.path.basename(filename)} received successfully at {datetime.now()}.")

    def send_file(self, client_socket, filename):
        try:
            self.send_data(client_socket, str(os.path.getsize(filename)).encode())
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

            self.ui.log_message(f"File {os.path.basename(filename)} sent successfully at {datetime.now()}.")
        except FileNotFoundError:
            self.ui.log_message(f"File {os.path.basename(filename)} not found at {datetime.now()}.")
            self.send_data(client_socket, b'File not found.')

    def list(self, client_socket):
        no_files = len([name for name in os.listdir(self.folder) if os.path.isfile(os.path.join(self.folder, name))])
        self.send_data(client_socket, str(no_files).encode())

        for filename in os.listdir(self.folder):
            filepath = os.path.join(self.folder, filename)
            file_size = os.path.getsize(filepath)
            data = filename.encode() + b'::' + str(file_size).encode()
            self.send_data(client_socket, data)

    def delete_file(self, client_socket, filename):
        try:
            os.remove(os.path.join(self.folder, filename))
            self.send_data(client_socket, b"success")
        except Exception as e:
            self.ui.log_message(f"Failed to delete file {filename}: {e} at {datetime.now()}.")
            self.send_data(client_socket, b"failure")

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
                elif action == b'x':
                    filename = self.receive_data(client_socket).decode()
                    self.delete_file(client_socket, filename)
                elif action == b'e':
                    self.ui.log_message(f"Client connection closed at {datetime.now()}.")
        except Exception as e:
            self.ui.log_message(f"Error handling client: {e} at {datetime.now()}.")
        finally:
            client_socket.close()
            self.client_count -= 1
            self.ui.update_client_count(self.client_count)
            self.ui.log_message(f"Client connection closed at {datetime.now()}.")


class ServerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Transfer Server")

        self.label_ip = tk.Label(root, text=f"Server IP: {SERVER_IP}", font=("Helvetica", 14))
        self.label_ip.pack()

        self.label_port = tk.Label(root, text=f"Server PORT: {SERVER_PORT}", font=("Helvetica", 14))
        self.label_port.pack()

        self.label_client_count = tk.Label(root, text="Clients Connected: 0", font=("Helvetica", 14))
        self.label_client_count.pack()

        self.log_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20, font=("Helvetica", 10))
        self.log_text.pack()

        self.server = Server(SERVER_IP, SERVER_PORT, SERVER_FOLDER, self)
        threading.Thread(target=self.server.start).start()

    def log_message(self, message):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.insert(tk.END, f"[{current_time}] {message}\n")
        self.log_text.yview(tk.END)

    def update_client_count(self, count):
        self.label_client_count.config(text=f"Clients Connected: {count}")



if __name__ == "__main__":
    root = tk.Tk()
    ui = ServerUI(root)
    root.mainloop()
