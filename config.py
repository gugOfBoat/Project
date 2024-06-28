# Cấu hình chung cho cả client và server
SERVER_IP = socket.gethostbyname(socket.gethostname())  # Địa chỉ IP của server (localhost trong ví dụ này)
SERVER_PORT = 6666      # Cổng kết nối
SERVER_ADDR =  (IP, PORT)
CHUNK_SIZE = 1024 * 1024  # Kích thước chunk: 1MB
TIMEOUT = 1             # Thời gian timeout (giây)
FORMAT = "utf-8"
