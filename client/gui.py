import os
from customtkinter import *
import client
import socket
from PIL import Image, ImageTk

SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5000

def upload(client1):
    filepath = filedialog.askopenfilename()
    if filepath:
        client1.upload_file(filepath)
        refresh(client1, file_display_frame)

def get_file_icon(file_name):
    extension = os.path.splitext(file_name)[1].lower()
    if extension in ['.jpg', '.jpeg', '.png', '.gif']:
        return Image.open('client/image_icon.png')
    elif extension in ['.pdf']:
        return Image.open('client/pdf_icon.png')
    elif extension in ['.txt']:
        return Image.open('client/txt_icon.png')
    elif extension in ['.mp3']:
        return Image.open('client/audio_icon.png')
    else:
        return Image.open('client/file_icon.png')
    
def cut_string(filename):
    if len(filename) > 35:
        return filename[0:35] + "..."
    return filename

def filesize(filesize):
    size = int(filesize)
    pre = size
    byte_tail = ["B", "KB", "MB", "GB"]
    track = 0
    while size // 1024 > 0:
        if track == 3:
            break
        pre = size
        size= round(size/1024, 1)
        track += 1
    return f"{pre} {byte_tail[track]}"

def refresh(client1, frame):
    # Clear existing widgets
    for widget in frame.winfo_children():
        widget.destroy()
    
    # Configure columns to expand evenly
    frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

    # Fetch the list of files from client1
    files = client1.list()

    if not files:
        # If no files, show an upload button or a message
        cat_unknown = CTkImage(dark_image=Image.open('client/upload_new.png'), light_image=Image.open('client/upload_new.png'), size=(50, 50))
        upload_button = CTkButton(master=frame, text="  UPLOAD  \nNEW FILE", height=150, width=150, fg_color="#DCEDF8", image=cat_unknown, compound='top', font=('Archivo Black', 16, 'bold'), text_color="#011320", command=lambda: upload(client1), corner_radius=8, hover_color="#B5CDDD")
        upload_button.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        return

    # Calculate number of rows needed based on files count
    num_cols = 4
    num_rows = (len(files) + num_cols - 1) // num_cols  # Ceiling division for rows
    col = 0
    row = 0
    # Iterate over files to display them in a grid
    for index, (file_name, file_size) in enumerate(files):
        col = index % num_cols
        row = index // num_cols

        # Get file icon (assuming you have a function `get_file_icon`)
        file_icon_image = get_file_icon(file_name)
        file_icon = CTkImage(light_image=file_icon_image, dark_image=file_icon_image, size=(50, 50))

        # Create a frame for each file
        file_frame = CTkFrame(master=frame, width=150, height=150, fg_color="#DCEDF8")
        file_frame.pack_propagate(False)

        # Determine padding based on column position
        if col == 0:
            if row == num_rows - 1 and len(files) % 4 != 0:
                file_frame.grid(row=row, column=col, padx=(20, 10), pady=20)
            else:
                file_frame.grid(row=row, column=col, padx=(20, 10), pady=(20, 0))
        elif col == 3:
            if row == num_rows - 1 and len(files) % 4 != 0:
                file_frame.grid(row=row, column=col, padx=(10, 20), pady=20)
            else:
                file_frame.grid(row=row, column=col, padx=(10, 20), pady=(20, 0))
        else:
            if row == num_rows - 1 and len(files) % 4 != 0:
                file_frame.grid(row=row, column=col, padx=(10, 10), pady=20)
            else:
                file_frame.grid(row=row, column=col, padx=(10, 10), pady=(20, 0))
        
        # Display file icon
        icon_label = CTkLabel(master=file_frame, image=file_icon, text="")
        icon_label.image = file_icon  # Keep a reference to avoid garbage collection
        icon_label.pack(pady=(20, 5))

        # Display file name
        name_label = CTkLabel(master=file_frame, text=cut_string(file_name), font=('Archivo', 10), wraplength=100, text_color="#011320")
        name_label.pack(pady=0)

        # Display file size
        size_label = CTkLabel(master=file_frame, text=filesize(file_size), font=('Archivo', 8), text_color="#011320")
        size_label.pack(pady=0)

        menu_var = StringVar(value=" ")  # Default value
        menu = CTkOptionMenu(master=file_frame, variable=menu_var, values=["DOWNLOAD", "DELETE"], dropdown_font=('Archivo', 10), font=('Archivo', 12), 
                             command=lambda action, fn=file_name: on_select(action, fn, client1), fg_color="#DCEDF8", button_color="#DCEDF8", 
                             button_hover_color="#B5CDDD", dropdown_fg_color="#DCEDF8", dropdown_hover_color="#B5CDDD", dropdown_text_color="#011320",
                             text_color="#011320", anchor="e", height=30, corner_radius=0)
        menu.pack(pady=(0, 5))

    
    if col == 3:
        col = 0
        row += 1
    else:
        col += 1

    cat_unknown = CTkImage(dark_image=Image.open('client/upload_new.png'), light_image=Image.open('client/upload_new.png'), size=(50, 50))
    upload_button = CTkButton(master=frame, text="  UPLOAD  \nNEW FILE", height=150, width=150, fg_color="#DCEDF8", image=cat_unknown, compound='top', font=('Archivo Black', 16, 'bold'), text_color="#011320", command=lambda: upload(client1), corner_radius=8, hover_color="#B5CDDD")
    if col == 0:
        upload_button.grid(row=row, column=col, padx=(20, 10), pady=20)
    elif col == 3:
        upload_button.grid(row=row, column=col, padx=(10, 20), pady=20)
    else:
        upload_button.grid(row=row, column=col, padx=(10, 10), pady=20)
    
    col+=1
    while col % 4 != 0:
        clear_frame = CTkFrame(master=frame, corner_radius=0, fg_color="#F7FDFF", height=150, width=150)
        if col == num_cols - 1:
            clear_frame.grid(row=row, column=col, padx=(10, 20), pady=20)
        else:
            clear_frame.grid(row=row, column=col, padx=(10, 10), pady=20)
        col += 1


def on_select(action, file_name, client1):
    if action == "DOWNLOAD":
        des = filedialog.askdirectory()
        client1.download_file(file_name, des)
    elif action == "DELETE":
        client1.delete_file(file_name)
        refresh(client1, file_display_frame)  # Assuming file_display_frame is your frame to refresh

def quit_app(app):
    app.destroy()

def start(app):
    def confirm():
        ip = ip_entry.get().strip()
        port = port_entry.get().strip()
        if ip and port:
            try:
                global SERVER_IP, SERVER_PORT
                SERVER_IP = ip
                SERVER_PORT = int(port)
                client1 = client.Client(SERVER_IP, SERVER_PORT)
                client1.connect()
                print("Connected to the server")
                show_main_app(client1)
            except Exception as e:
                print(f"Error: {e}") #Nếu sai thì nên làm gì?
                label_incorrect.configure(text_color='#F36666')
                

    framel = CTkFrame(master=app, width=750, height=500, corner_radius=0)
    framel.place(x=0, y=0)
    cat_image = CTkImage(light_image=Image.open('client/catlogin.png'), dark_image=Image.open('client/catlogin.png'), size=(500, 500))
    label = CTkLabel(master=framel, text="", image=cat_image, width=500, height=500)
    label.place(x=0, y=0)

    framer = CTkFrame(master=app, width=250, height=500, corner_radius=0, fg_color="#F7FDFF")
    framer.place(x=500, y=0)
    font = CTkFont('Archivo Black', 23, 'bold')
    paw_image = CTkImage(light_image=Image.open('client/paw.png'), dark_image=Image.open('client/paw.png'), size=(27, 27))
    welcome_label = CTkLabel(master=framer, text="WELCOME!", font=font, text_color="#011320")
    welcome_label.place(x=35, y=125)
    paw_label = CTkLabel(master=framer, text="", image=paw_image)
    paw_label.place(x=165, y=122)

    ip_label = CTkLabel(master=framer, text="IP:", font=('Archivo', 12), text_color='#8C8C8C')
    ip_label.place(x=35, y=185)
    ip_entry = CTkEntry(master=framer, height=27, width=180, font=('Archivo', 14), corner_radius=4, text_color="#011320", fg_color="#DCEDF8", border_color="#DCEDF8")
    ip_entry.place(x=35, y=210)

    port_label = CTkLabel(master=framer, text="PORT:", font=('Archivo', 12), text_color='#8C8C8C')
    port_label.place(x=35, y=245)
    port_entry = CTkEntry(master=framer, height=27, width=180, font=('Archivo', 14), corner_radius=4, text_color="#011320", fg_color="#DCEDF8", border_color="#DCEDF8")
    port_entry.place(x=35, y=270)

    label_incorrect = CTkLabel(master=framer, text="SERVER NOT FOUND. TRY AGAIN", font=('Archivo', 11, 'bold'), text_color='#F7FDFF')
    label_incorrect.place(x=35, y= 305)

    confirm_button = CTkButton(master=framer, height=27, width=180, font=('Archivo Black', 14, 'bold'), text_color="#DCEDF8", fg_color="#052F4E", corner_radius=4, text="CONFIRM", command=confirm)
    confirm_button.place(x=35, y=330)

def show_main_app(client1):
    # Clear existing widgets
    for widget in app.winfo_children():
        widget.destroy()

    set_appearance_mode("dark")
    frame = CTkFrame(master=app, width=50, height=500, fg_color="#DCEDF8", corner_radius=0)
    frame.place(x=0, y=0)

    upload_button_image = CTkImage(light_image=Image.open('client/upload_button.png'), dark_image=Image.open('client/upload_button.png'), size=(18, 10.59))
    upload_button = CTkButton(master=frame, image=upload_button_image, width=30, height=30, fg_color="#052F4E", command=lambda: upload(client1), text = "", corner_radius=5)
    upload_button.place(x=10, y=65)

    refresh_button_image = CTkImage(light_image=Image.open('client/refresh.png'), dark_image=Image.open('client/refresh.png'), size=(16, 15))
    refresh_button = CTkButton(master=frame, image=refresh_button_image, width=30, height=30, fg_color="#052F4E", command=lambda: refresh(client1, file_display_frame), text="", corner_radius=5)
    refresh_button.place(x=10, y=105)

    question_button_image = CTkImage(light_image=Image.open('client/chamhoi.png'), dark_image=Image.open('client/chamhoi.png'), size=(10.47, 15))
    question_button = CTkButton(master=frame, image=question_button_image, width=30, height=30, fg_color="#466479", corner_radius=5, text="")
    question_button.place(x=10, y=400)

    quit_button_image = CTkImage(light_image=Image.open('client/quit.png'), dark_image=Image.open('client/quit.png'), size=(12.91, 17))
    quit_button = CTkButton(master=frame, image=quit_button_image, width=30, height=30, fg_color="#466479", corner_radius=5, command=lambda: quit_app(app), text="")
    quit_button.place(x=10, y=440)



    global file_display_frame
    file_display_frame = CTkScrollableFrame(master=app, width=700, height=500, fg_color="#F7FDFF", corner_radius=0, scrollbar_button_color="#052F4E")
    file_display_frame.place(x=50, y=0)

    refresh(client1, file_display_frame)
    print("Main app UI displayed")

if __name__ == "__main__":
    app = CTk()
    app.geometry("750x500")
    app.iconbitmap('client/icon.ico')
    app.title("Upload/Download")
    app.resizable(width=False, height=False)

    start(app)

    app.mainloop()
