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
        self.server_folder = server_folder
        self.ui = ui
        self.server_socket = None
        self.client_sockets = []
        self.lock = threading.Lock()
        self.client_count = 0
        self.running = False

    def start(self):
        if self.running:
            self.ui.log_message("Server is already running.")
            return

        if not os.path.exists(self.server_folder):
            os.makedirs(self.server_folder)
            self.ui.log_message(f"\"{self.server_folder}\" Created")
        else:
            self.ui.log_message(f"\"{self.server_folder}\" Found")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(5)
        self.ui.log_message(f"Server listening on {self.server_ip}:{self.server_port}")

        self.running = True

        def accept_connections():
            try:
                while self.running:
                    client_socket, address = self.server_socket.accept()
                    with self.lock:
                        self.client_sockets.append((client_socket, address))
                    self.ui.log_message(f"Accepted connection from {address[0]}:{address[1]}")
                    self.client_count += 1
                    self.ui.update_client_count(self.client_count)
                    client_handler = threading.Thread(target=self.handle_client, args=(client_socket, address))
                    client_handler.start()
            except OSError as e:
                if e.errno == 9:  # Bad file descriptor error, which is expected when the server socket is closed
                    self.ui.log_message("Server stopped.")
                else:
                    logging.error(f"Error accepting connections: {e}")
            except Exception as e:
                logging.error(f"Error accepting connections: {e}")
            finally:
                if self.server_socket:
                    self.server_socket.close()

        threading.Thread(target=accept_connections, daemon=True).start()

    def stop(self):
        if not self.running:
            self.ui.log_message("Server is not running.")
            return

        if self.client_count > 0:
            self.ui.log_message("Cannot stop the server: There are still clients connected.")
            logging.warning("Attempted to stop the server while clients are still connected.")
            return

        self.running = False
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None

        with self.lock:
            for client_socket, _ in self.client_sockets:
                client_socket.close()
            self.client_sockets = []

        self.ui.log_message("Server stopped.")

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
        retries = 3  # Maximum retry attempts
        while retries > 0:
            try:
                checksum = self.calculate_checksum(chunk_data)
                data_with_checksum_chunk_num = checksum.encode() + b'::' + str(chunk_num).encode() + b'::' + chunk_data
                with self.lock:
                    self.send_data(client_socket, data_with_checksum_chunk_num)
                    ack = self.receive_data(client_socket)
                    if ack.decode() == "ACK":
                        client_address = next(addr for sock, addr in self.client_sockets if sock == client_socket)
                        self.ui.log_message(f"Chunk {chunk_num} uploaded successfully to {client_address[0]}:{client_address[1]} at {datetime.now()}.")
                        return True  # Success, no need to retry
            except Exception as e:
                self.ui.log_message(f"Error uploading chunk {chunk_num}: {e}")
                retries -= 1
        client_address = next(addr for sock, addr in self.client_sockets if sock == client_socket)
        self.ui.log_message(f"Failed to upload chunk {chunk_num} after {retries} retries to {client_address[0]}:{client_address[1]} at {datetime.now()}.")
        return False

    def receive_chunk(self, client_socket):
        retries = 3  # Maximum retry attempts
        while retries > 0:
            try:
                data_with_checksum = self.receive_data(client_socket)
                if data_with_checksum:
                    received_checksum, chunk_num, chunk_data = data_with_checksum.split(b'::', 2)
                    calculated_checksum = self.calculate_checksum(chunk_data)
                    if received_checksum.decode() == calculated_checksum:
                        self.send_data(client_socket, b"ACK")
                        client_address = next(addr for sock, addr in self.client_sockets if sock == client_socket)
                        self.ui.log_message(f"Chunk {chunk_num.decode()} received successfully from {client_address[0]}:{client_address[1]} at {datetime.now()}.")
                        return chunk_num, chunk_data
            except Exception as e:
                self.ui.log_message(f"Error receiving chunk: {e}")
                retries -= 1
        client_address = next(addr for sock, addr in self.client_sockets if sock == client_socket)
        self.ui.log_message(f"Failed to receive chunk after {retries} retries from {client_address[0]}:{client_address[1]} at {datetime.now()}.")
        return None

    def receive_file(self, client_socket, filename):
        file_chunks = []
        while True:
            chunk_num, chunk_data = self.receive_chunk(client_socket)
            if not chunk_data:
                break
            file_chunks.append((int(chunk_num.decode()), chunk_data))

        filename = os.path.join(self.server_folder, filename)
        with open(filename, 'wb') as f:
            for chunk_num, chunk_data in sorted(file_chunks):
                f.write(chunk_data)

        client_address = next(addr for sock, addr in self.client_sockets if sock == client_socket)
        self.ui.log_message(f"File {os.path.basename(filename)} received successfully from {client_address[0]}:{client_address[1]} at {datetime.now()}.")

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

            client_address = next(addr for sock, addr in self.client_sockets if sock == client_socket)
            self.ui.log_message(f"File {os.path.basename(filename)} sent successfully to {client_address[0]}:{client_address[1]} at {datetime.now()}.")
        except FileNotFoundError:
            self.ui.log_message(f"File {os.path.basename(filename)} not found at {datetime.now()}.")
            self.send_data(client_socket, b'File not found.')

    def list(self, client_socket):
        no_files = len([name for name in os.listdir(self.server_folder) if os.path.isfile(os.path.join(self.server_folder, name))])
        self.send_data(client_socket, str(no_files).encode())

        for filename in os.listdir(self.server_folder):
            filepath = os.path.join(self.server_folder, filename)
            file_size = os.path.getsize(filepath)
            data = filename.encode() + b'::' + str(file_size).encode()
            self.send_data(client_socket, data)

    def delete_file(self, client_socket, filename):
        try:
            os.remove(os.path.join(self.server_folder, filename))
            self.ui.log_message(f"Deleted file {filename} successfully at {datetime.now()}.")
            self.send_data(client_socket, b"success")
        except Exception as e:
            self.ui.log_message(f"Failed to delete file {filename}: {e} at {datetime.now()}.")
            self.send_data(client_socket, b"failure")

    def handle_client(self, client_socket, address):
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
                    filename = os.path.join(self.server_folder, filename)
                    self.send_file(client_socket, filename)
                elif action == b'r':
                    self.list(client_socket)
                elif action == b'x':
                    filename = self.receive_data(client_socket).decode()
                    self.delete_file(client_socket, filename)
                elif action == b'e':
                    self.ui.log_message(f"Client {address[0]}:{address[1]} connection closed at {datetime.now()}.")
        except Exception as e:
            self.ui.log_message(f"Error handling client {address[0]}:{address[1]}: {e} at {datetime.now()}.")
        finally:
            client_socket.close()
            with self.lock:
                self.client_count -= 1
                self.client_sockets = [(sock, addr) for sock, addr in self.client_sockets if addr != address]
            self.ui.update_client_count(self.client_count)
            self.ui.log_message(f"Client {address[0]}:{address[1]} connection closed at {datetime.now()}.")


class ServerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Upload/Download Server")
        self.root.resizable(False, False)  # Lock window size

        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10)

        self.label_ip = tk.Label(self.frame, text="Server IP:", font=("Helvetica", 14))
        self.label_ip.grid(row=0, column=0, sticky="e")

        self.entry_ip = tk.Entry(self.frame, font=("Helvetica", 14), width=20)
        self.entry_ip.grid(row=0, column=1)
        self.entry_ip.insert(0, SERVER_IP)
          # Allow copying

        self.label_port = tk.Label(self.frame, text="Server PORT:", font=("Helvetica", 14))
        self.label_port.grid(row=1, column=0, sticky="e")

        self.entry_port = tk.Entry(self.frame, font=("Helvetica", 14), width=20)
        self.entry_port.grid(row=1, column=1)
        self.entry_port.insert(0, str(SERVER_PORT))
        self.entry_port.config(state="readonly")  # Allow copying

        self.start_button = tk.Button(self.frame, text="Start Server", command=self.start_server, font=("Helvetica", 14))
        self.start_button.grid(row=2, column=0, pady=10)

        self.stop_button = tk.Button(self.frame, text="Stop Server", command=self.stop_server, font=("Helvetica", 14))
        self.stop_button.grid(row=2, column=1, pady=10)
        self.stop_button.config(state="disabled")

        self.text_area = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, height=20, width=80, font=("Helvetica", 12), state='disabled')
        self.text_area.grid(row=3, column=0, columnspan=2)

        self.label_clients = tk.Label(self.frame, text="Connected Clients:", font=("Helvetica", 14))
        self.label_clients.grid(row=4, column=0, sticky="e")

        self.client_count = tk.Label(self.frame, text="0", font=("Helvetica", 14))
        self.client_count.grid(row=4, column=1)

        self.server = None

    def start_server(self):
        if not self.server or not self.server.running:
            self.server = Server(self.entry_ip.get(), int(self.entry_port.get()), SERVER_FOLDER, self)
            self.server.start()
            self.entry_ip.config(state="readonly")
            self.entry_port.config(state="readonly")
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.log_message("Server started.")
        else:
            self.log_message("Server is already running.")

    def stop_server(self):
        if self.server and self.server.running:
            if self.server.client_count > 0:
                self.log_message("Cannot stop the server: There are still clients connected.")
                logging.warning("Attempted to stop the server while clients are still connected.")
                return

            self.server.stop()
            self.entry_ip.config(state="normal")
            self.entry_port.config(state="normal")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.log_message("Server stopped.")
        else:
            self.log_message("Server is not running.")

    def log_message(self, message):
        self.text_area.config(state="normal")
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.text_area.insert(tk.END, f"[{current_time}] {message}\n")
        self.text_area.yview(tk.END)
        self.text_area.config(state="disabled")

    def update_client_count(self, count):
        self.client_count.config(text=str(count))

    def on_closing(self):
        if self.server and self.server.client_count > 0:
            self.log_message("Cannot close the server: There are still clients connected.")
            logging.warning("Attempted to close the server while clients are still connected.")
            return
        
        if self.server:
            self.server.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    ui = ServerUI(root)
    root.iconbitmap('img/server_icon.ico')
    root.protocol("WM_DELETE_WINDOW", ui.on_closing)
    root.mainloop()
