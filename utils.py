import os
import hashlib

def calculate_checksum(data):
    """
    Calculates the checksum of the given data using SHA-256.

    Args:
    - data (bytes): The data for which to calculate the checksum.

    Returns:
    - str: The hexadecimal checksum of the data.
    """
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()

def split_file(file_path, chunk_size):
    """
    Splits a file into chunks of specified size.

    Args:
    - file_path (str): The path to the file to be split.
    - chunk_size (int): The size of each chunk in bytes.

    Returns:
    - list of str: List of paths to the chunk files.
    """
    chunk_files = []
    file_size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        chunk_number = 0
        while True:
            chunk_data = f.read(chunk_size)
            if not chunk_data:
                break
            chunk_file_path = f"{file_path}.chunk{chunk_number}"
            with open(chunk_file_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)
            chunk_files.append(chunk_file_path)
            chunk_number += 1
    return chunk_files