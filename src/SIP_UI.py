import tkinter as tk
import os

if os.environ.get('DISPLAY', '') == '':
    os.environ.__setitem__('DISPLAY', ':0.0')

root = tk.Tk()

# Retrieve SIP-compatible files from the data directory
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
def get_sip_files():
    """
    Retrieves all SIP-compatible files from the data directory.
    Currently supports files of type: .xlsx
    """
    sip_files = []
    for file in os.listdir(data_dir):
        if file.endswith('.xlsx'):
            sip_files.append(os.path.join(data_dir, file))
    return sip_files

# Set window settings
root.title("SIP Analyzer UI")
root.configure(background="gray")
root.minsize(300, 300)
root.maxsize(800, 600)
root.geometry("800x600") # default size

# Create labels for welcome message and instructions
welcome_label = tk.Label(root, text="Welcome to the SIP UI", bg="gray", fg="white", font=("Arial", 16))
welcome_label.pack(pady=20)

instructions_label = tk.Label(root, text="Please select a file to parse", bg="gray", fg="white", font=("Arial", 12))
instructions_label.pack(pady=5)

# Frame and scrollbar for file list
list_frame = tk.Frame(root, bg="gray")
list_frame.pack(pady=10, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(list_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 12), width=80, height=20)
file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=file_listbox.yview)

# Populate the listbox with SIP files
sip_files = get_sip_files()
for file in sip_files:
    file_listbox.insert(tk.END, os.path.basename(file))

root.mainloop()