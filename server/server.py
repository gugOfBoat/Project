import socket
import os
import json
import hashlib 
import base64
import threading

SERVER_IP = '192.168.100.100'
SERVER_PORT = 5000
BUFFER_SIZE = 5 * 1024 * 1024

file_data = {}

def handle_upload_chunk(client_socket, address, filename, filesize):
    try:
        # Calculate number of chunks
        num_chunks = (filesize + BUFFER_SIZE - 1) // BUFFER_SIZE

        file_data[filename] = []

        for chunk_num in range(num_chunks):
            if chunk_num == num_chunks - 1:
                # Last chunk may be smaller than BUFFER_SIZE
                chunk_size = filesize % BUFFER_SIZE
            else:
                chunk_size = BUFFER_SIZE

            data = client_socket.recv(chunk_size)
            if not data:
                break
            
            chunk_info = json.loads(data.decode())
            received_chunk_num = chunk_info['chunk_num']
            checksum = chunk_info['checksum']
            encoded_chunk = chunk_info['data']

            # Decode chunk from base64
            chunk = base64.b64decode(encoded_chunk)

            if hashlib.sha256(chunk).hexdigest() == checksum:
                file_data[filename].append({'chunk_num': received_chunk_num, 'data': chunk})
                client_socket.send(json.dumps({'ack': received_chunk_num}).encode())
                print(f"Received chunk {received_chunk_num} from {address}")
            else:
                client_socket.send(json.dumps({'nack': received_chunk_num}).encode())
                print(f"Received corrupted chunk {received_chunk_num} from {address}. Retrying...")

        # Merge chunks into original file
        with open(filename, 'wb') as f:
            for chunk_info in sorted(file_data[filename], key=lambda x: x['chunk_num']):
                f.write(chunk_info['data'])

        print(f"File {filename} uploaded successfully from {address}")

    except Exception as e:
        print(f"Error handling client {address}: {e}")

    finally:
        client_socket.close()


def handle_download_chunk(client_socket, address, filename):
    try:
        if os.path.exists(filename):
            filesize = os.path.getsize(filename)
            client_socket.send(json.dumps({'filesize': filesize}).encode())

            with open(filename, 'rb') as f:
                while True:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    client_socket.send(chunk)
        else:
            client_socket.send(json.dumps({'error': 'File not found'}).encode())
    except Exception as e:
        print(f"Error handling download for {filename}: {str(e)}")
    finally:
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
        except:
            pass

def handle_client(client_socket, address):
    try:
        while True:
            request = client_socket.recv(1024).decode()
            request_json = json.loads(request)

            if request_json['type'] == 'upload':
                filename = request_json['filename']
                filesize = request_json['filesize']
                handle_upload_chunk(client_socket, address, filename, filesize)

            elif request_json['type'] == 'download':
                filename = request_json['filename']
                handle_download_chunk(client_socket, address, filename)

    except Exception as e:
        print(f"Error handling client {address}: {e}")
    finally:
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
        except:
            pass

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

    while True:
        client_socket, address = server_socket.accept()
        print(f"Accepted connection from {address}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket, address))
        client_handler.start()

if __name__ == "__main__":
    start_server()
