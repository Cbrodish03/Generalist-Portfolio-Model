import tkinter as tk
import os
from tkinter import messagebox
from parser import SIPParser

# Retrieve SIP-compatible files from the data directory
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_FOLDER = os.path.join(BASE_DIR, "data")

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



def parse_button_click():
    """
    Parses the selected file from the options in the /data folder
    """
    selected = file_listbox.curselection()
    if not selected:
        messagebox.showwarning("No File Selected", "Please select a file from the identified list")
        return

    filename = file_listbox.get(selected[0])
    # path = os.path.join("data", filename)
    full_path = os.path.join(DATA_FOLDER, filename)
    print("Parsing file at path:", full_path)

    try:
        parser = SIPParser(full_path)
        investments = parser.investments
        summary_text = f"File: {filename}\n\nTotal investments: {len(investments)}\n"
        for inv in investments:
            meta = inv["metadata"]
            trials = inv["trials"]
            summary_text += "\n"
            summary_text += f"🔹 {meta['Name']} (Revenue: ${meta['ExpectedRevenue']}, " \
                            f"Unit: {meta['BusinessUnit']}, Type: {meta['ProductType']})\n"
            summary_text += f"   Trials: {len(trials)} total | First 5: {trials[:5]}\n"
            # print(summary_text)
        # update file info text box
        file_info_box.config(state=tk.NORMAL)
        file_info_box.delete(1.0, tk.END)
        file_info_box.insert(tk.END, summary_text)
        file_info_box.config(state=tk.DISABLED)


        messagebox.showinfo("Parse Successful", "Successfully parsed requested file.")
    except Exception as e:
        messagebox.showerror("Parse Failed", f"Error {str(e)} occurred while parsing.")


# Set window settings
root = tk.Tk()
root.title("SIP Analyzer UI")
root.configure(background="gray")
root.minsize(300, 300)
root.maxsize(1000, 800)
root.geometry("800x600") # default size

# Top labels
tk.Label(root, text="Welcome to the Generalist-Portfolio-Model!", bg="gray", fg="white", font=("Arial", 16)).pack(pady=20)
tk.Label(root, text="Please select a SIP file to parse", bg="gray", fg="white", font=("Arial", 12)).pack(pady=5)

# Middle frame: file list + parse button
selection_frame = tk.Frame(root, bg="gray")
selection_frame.pack(fill=tk.X, padx=10, pady=5)

# File list
list_frame = tk.Frame(selection_frame, bg="gray")
list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)

scrollbar = tk.Scrollbar(list_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 12), width=50, height=10)
file_listbox.pack(side=tk.LEFT, fill=tk.Y)
scrollbar.config(command=file_listbox.yview)

# Parse button beside the list
button_frame = tk.Frame(selection_frame, bg="gray")
button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

parse_button = tk.Button(button_frame, text="Parse selected file", command=parse_button_click,
                         font=("Arial", 12), bg="darkgreen", fg="white")
parse_button.pack(pady=10)

# Populate listbox with files
sip_files = get_sip_files()
for file in sip_files:
    file_listbox.insert(tk.END, os.path.basename(file))

# Bottom frame: file info output
file_info_frame = tk.LabelFrame(root, text="File Info", bg="gray", fg="white", font=("Arial", 12))
file_info_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

file_info_scrollbar = tk.Scrollbar(file_info_frame)
file_info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

file_info_box = tk.Text(file_info_frame, wrap=tk.WORD, font=("Arial", 11), bg="white", yscrollcommand=file_info_scrollbar.set)
file_info_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
file_info_scrollbar.config(command=file_info_box.yview)

file_info_box.config(state=tk.DISABLED)

# Start the application
root.mainloop()