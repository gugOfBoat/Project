import socket
import os
import json
import hashlib
import base64
import threading

SERVER_IP = '192.168.100.100'
SERVER_PORT = 5000
BUFFER_SIZE = 1 * 1024 * 1024  # 5MB chunk size

def send_chunk(client_socket, chunk_num, chunk_data, checksum):
    try:
        client_socket.sendall(json.dumps({
            'chunk_num': chunk_num,
            'checksum': checksum,
            'data': base64.b64encode(chunk_data).decode('utf-8')
        }).encode())
        response = client_socket.recv(1024).decode()
        response_json = json.loads(response)
        if 'ack' in response_json and response_json['ack'] == chunk_num:
            print(f"Chunk {chunk_num} uploaded successfully.")
        else:
            print(f"Failed to upload chunk {chunk_num}. Retrying...")
    except Exception as e:
        print(f"Error uploading chunk {chunk_num}: {str(e)}")

def send_file(filename):
    filesize = os.path.getsize(filename)
    num_chunks = (filesize + BUFFER_SIZE - 1) // BUFFER_SIZE

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    client_socket.send(json.dumps({'type': 'upload', 'filename': filename, 'filesize': filesize}).encode())

    threads = []
    try:
        with open(filename, 'rb') as f:
            for chunk_num in range(num_chunks):
                if chunk_num == num_chunks - 1:
                    # Last chunk may be smaller than BUFFER_SIZE
                    chunk_data = f.read(filesize % BUFFER_SIZE)
                else:
                    chunk_data = f.read(BUFFER_SIZE)
                
                if not chunk_data:
                    break
                
                checksum = hashlib.sha256(chunk_data).hexdigest()

                # Create thread to send each chunk
                thread = threading.Thread(target=send_chunk, args=(client_socket, chunk_num, chunk_data, checksum))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

    except Exception as e:
        print(f"Error preparing file {filename} for upload: {str(e)}")
    
    finally:
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
        except Exception as e:
            print(f"Error closing socket: {str(e)}")


def receive_file(client_socket, filename, filesize):
    try:
        with open(filename, 'wb') as f:
            received_bytes = 0
            while received_bytes < filesize:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)
                received_bytes += len(data)
            print(f"File {filename} downloaded successfully.")
    except Exception as e:
        print(f"Error downloading file {filename}: {str(e)}")

def download_file(filename):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    client_socket.send(json.dumps({'type': 'download', 'filename': filename}).encode())

    response = client_socket.recv(1024).decode()
    response_json = json.loads(response)

    if 'filesize' in response_json:
        filesize = response_json['filesize']
        receive_file(client_socket, filename, filesize)
    else:
        print(f"File {filename} not found on server.")

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
