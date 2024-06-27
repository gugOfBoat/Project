import tkinter as tk
from tkinter import filedialog
from gui import GUI
from network import NetworkManager

def main():
    root = tk.Tk()
    app = GUI(root)
    network_manager = NetworkManager(app)  # Tạo đối tượng quản lý mạng
    app.set_network_manager(network_manager)  # Gán cho GUI
    root.mainloop()

if __name__ == "__main__":
    main()
