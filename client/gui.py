from customtkinter import *
import client
import socket
from PIL import Image

SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5000

def upload():
    filepath = filedialog.askopenfilename()
    client1.upload_file(filepath)

def start(app):
    framel = CTkFrame(master=app, width=500, height=500, corner_radius=0)
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

    confirm_button = CTkButton(master=framer, height=27, width=180, font=('Archivo Black', 14, 'bold'), text_color="#DCEDF8", fg_color="#052F4E", corner_radius=4, text="CONFIRM")
    confirm_button.place(x=35, y=330)

if __name__ == "__main__":

    app = CTk()
    app.geometry("750x500")
    app.iconbitmap('client/icon.ico')
    app.title("Upload/Download")
    app.resizable(width=False, height=False)

    start(app)

    


    client1 = client.Client(SERVER_IP, SERVER_PORT)
    # client1.connect()

    

    # r = 0 
    # c = 0
    # for filename, filesize in file_list:
    #     lable = CTkLabel(master=framer, text= f"{filename}: {filesize}", text_color= "black")
    #     lable.grid(row = r, column = c)
    #     c += 1
    #     if c == 3:
    #         c = 0
    #         r += 1


    

    app.mainloop()

    client1.close()
