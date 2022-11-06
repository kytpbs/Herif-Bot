import tkinter as tk

window = tk.Tk()
window.geometry("480x360")
window.title("Discord")
receive = tk.Text(height=5, width=52)
send = tk.Text(height=10, width=52)
send_button = tk.Button(height=2, width=5)
reply_button = tk.Button(height=2, width=5)
receive.pack()
send.pack()
send_button.pack()
reply_button.pack()
