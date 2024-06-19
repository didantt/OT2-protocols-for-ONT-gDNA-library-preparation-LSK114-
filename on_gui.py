# https://likegeeks.com/python-gui-examples-tkinter-tutorial/ 2024-03-11
# https://stackoverflow.com/a/665598 2024-03-11
 
from tkinter import filedialog
from tkinter import *
from os import popen
import subprocess

root = Tk()

root.title("OpenPore GUI")
root.geometry('400x400')

ip_lbl = Label(root, text="Robot wired IP:")
ip_lbl.grid(column=0, row=0)

ip_txt = Entry(root, width=15)
ip_txt.grid(column=1, row=0)


# Gets terminal printout of current ip connections, and looks for a dynamic ip with a specific physical address.
networks = os.popen('arp -a').readlines()
physical_address = "b8-27-eb-18-10-29"
for row in networks:
    if physical_address and "dynamic" in row:
        ip_txt.insert(INSERT, row[0:17].strip())
        break

if ip_txt.get() == "":    
    ip_txt.insert(INSERT, '169.254.')

filepath_lbl = Label(root, text="Path of file: ")
filepath_lbl.grid(column=0, row=2)

filepath_text = Entry(root, width=15)
filepath_text.grid(column=1, row=2)


def filepathClick():
    filepath = filedialog.askopenfilename(filetypes=(("Text files", "*.txt"), ("All files","*.*")))
    filepath_text.insert(INSERT, filepath)
    return

filepath_btn = Button(root, text='Choose file', command=filepathClick)
filepath_btn.grid(column=2, row=2)


def uploadClick():
    robot_ip = ip_txt.get()
    filepath = filepath_text.get()



    subprocess.call(f'C:\\Windows\\system32\\WindowsPowerShell\\v1.0\\powershell.exe scp -i ot2_ssh_key {filepath} root@{robot_ip}:/var/lib/jupyter/notebooks', shell=True)



upload_lbl = Label(root, text="Upload file to robot")
upload_btn = Button(root, text='Upload', command=uploadClick)

upload_lbl.grid(column=0,row=4)
upload_btn.grid(column=1,row=4)













root.mainloop()