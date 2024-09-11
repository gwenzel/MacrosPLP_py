import tkinter as tk
from tkinter import filedialog, scrolledtext
import tkinter.ttk as ttk

# Dummy server data
servers = ["Server 1", "Server 2", "Server 3"]

# Inputs that can be generated (Checkbox lists for A and B)
input_options_A = ["Input A1", "Input A2", "Input A3"]
input_options_B = ["Input B1", "Input B2", "Input B3"]

# Functions to interact with remote server
def generate_inputs_A():
    selected_inputs = [input_options_A[i] for i, var in enumerate(input_vars_A) if var.get()]
    log_message(f"Generating Inputs A: {', '.join(selected_inputs)}")
    # Actual logic to generate the selected inputs for A

def generate_inputs_B():
    selected_inputs = [input_options_B[i] for i, var in enumerate(input_vars_B) if var.get()]
    log_message(f"Generating Inputs B: {', '.join(selected_inputs)}")
    # Actual logic to generate the selected inputs for B

def create_folder():
    server = server_selector.get()
    log_message(f"Creating folder on {server}")
    # Logic to create folder on the remote server

def transfer_files():
    log_message("Transferring files to remote server...")
    # Logic to transfer files

def run_program():
    log_message("Running program on remote server...")
    # Logic to run the program on the server

def fetch_results():
    log_message("Fetching results from remote server...")
    # Logic to fetch results

def check_disk_space():
    log_message("Checking disk space on remote server...")
    # Logic to check disk space

def browse_file():
    filename = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if filename:
        file_path.set(filename)
        log_message(f"File selected: {filename}")
    else:
        log_message("File selection cancelled.")

# Toggle visibility of input checkboxes for A
def toggle_checkboxes_A():
    if checkbox_frame_A.winfo_viewable():
        checkbox_frame_A.grid_remove()
        toggle_button_A.config(text="Show Inputs A")
    else:
        checkbox_frame_A.grid()
        toggle_button_A.config(text="Hide Inputs A")

# Toggle visibility of input checkboxes for B
def toggle_checkboxes_B():
    if checkbox_frame_B.winfo_viewable():
        checkbox_frame_B.grid_remove()
        toggle_button_B.config(text="Show Inputs B")
    else:
        checkbox_frame_B.grid()
        toggle_button_B.config(text="Hide Inputs B")

# Select or deselect all checkboxes for Inputs A
def select_all_A():
    for var in input_vars_A:
        var.set(True)

def deselect_all_A():
    for var in input_vars_A:
        var.set(False)

# Select or deselect all checkboxes for Inputs B
def select_all_B():
    for var in input_vars_B:
        var.set(True)

def deselect_all_B():
    for var in input_vars_B:
        var.set(False)

# Logger for the text box
def log_message(message):
    log_box.insert(tk.END, message + '\n')
    log_box.see(tk.END)

# Tkinter setup
root = tk.Tk()
root.title("Remote Server Interface")

# ================== Input Section ==================
input_frame = tk.LabelFrame(root, text="Input Selection", padx=10, pady=10)
input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# File selection frame
file_frame = tk.Frame(input_frame)
file_frame.grid(row=0, column=0, padx=10, pady=10, columnspan=2)

file_path = tk.StringVar()
file_entry = tk.Entry(file_frame, textvariable=file_path, width=50)
file_entry.grid(row=0, column=0, padx=5, pady=5)

browse_button = tk.Button(file_frame, text="Browse", command=browse_file)
browse_button.grid(row=0, column=1, padx=5, pady=5)

# Left side frame for Inputs A, Right side frame for Inputs B

# Left side: Inputs A
left_frame = tk.LabelFrame(input_frame, text="PLP Inputs", padx=10, pady=10)
left_frame.grid(row=1, column=0, padx=10, pady=10)

# Button to toggle visibility of the checkboxes for Inputs A
toggle_button_A = tk.Button(left_frame, text="Show Inputs A", command=toggle_checkboxes_A)
toggle_button_A.grid(row=0, column=0, padx=5, pady=5)

# Generate inputs button for Inputs A
generate_button_A = tk.Button(left_frame, text="Generate Inputs A", command=generate_inputs_A)
generate_button_A.grid(row=0, column=1, padx=5, pady=5)

# Select All and Deselect All for Inputs A
select_all_button_A = tk.Button(left_frame, text="Select All A", command=select_all_A)
select_all_button_A.grid(row=0, column=2, padx=5, pady=5)

deselect_all_button_A = tk.Button(left_frame, text="Deselect All A", command=deselect_all_A)
deselect_all_button_A.grid(row=0, column=3, padx=5, pady=5)

# Checkboxes for selecting Inputs A to generate (Initially hidden in a frame)
checkbox_frame_A = tk.Frame(left_frame)

input_vars_A = []
for i, option in enumerate(input_options_A):
    var = tk.BooleanVar()
    chk = tk.Checkbutton(checkbox_frame_A, text=option, variable=var)
    chk.grid(row=i+1, column=0, padx=5, pady=2, sticky='w')
    input_vars_A.append(var)

# Initially hide the checkboxes for A
checkbox_frame_A.grid(row=1, column=0, columnspan=4, padx=5, pady=5)
checkbox_frame_A.grid_remove()

# Right side: Inputs B
right_frame = tk.LabelFrame(input_frame, text="Plexos Inputs", padx=10, pady=10)
right_frame.grid(row=1, column=1, padx=10, pady=10)

# Button to toggle visibility of the checkboxes for Inputs B
toggle_button_B = tk.Button(right_frame, text="Show Inputs B", command=toggle_checkboxes_B)
toggle_button_B.grid(row=0, column=0, padx=5, pady=5)

# Generate inputs button for Inputs B
generate_button_B = tk.Button(right_frame, text="Generate Inputs B", command=generate_inputs_B)
generate_button_B.grid(row=0, column=1, padx=5, pady=5)

# Select All and Deselect All for Inputs B
select_all_button_B = tk.Button(right_frame, text="Select All B", command=select_all_B)
select_all_button_B.grid(row=0, column=2, padx=5, pady=5)

deselect_all_button_B = tk.Button(right_frame, text="Deselect All B", command=deselect_all_B)
deselect_all_button_B.grid(row=0, column=3, padx=5, pady=5)

# Checkboxes for selecting Inputs B to generate (Initially hidden in a frame)
checkbox_frame_B = tk.Frame(right_frame)

input_vars_B = []
for i, option in enumerate(input_options_B):
    var = tk.BooleanVar()
    chk = tk.Checkbutton(checkbox_frame_B, text=option, variable=var)
    chk.grid(row=i+1, column=0, padx=5, pady=2, sticky='w')
    input_vars_B.append(var)

# Initially hide the checkboxes for B
checkbox_frame_B.grid(row=1, column=0, columnspan=4, padx=5, pady=5)
checkbox_frame_B.grid_remove()

# ================== Operations Section ==================
operations_frame = tk.LabelFrame(root, text="Operations", padx=10, pady=10)
operations_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

# Server selector (Combobox allows user to enter their own option)
server_label = tk.Label(operations_frame, text="Select server:")
server_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')

server_selector = ttk.Combobox(operations_frame, values=servers)
server_selector.grid(row=0, column=1, padx=5, pady=5)
server_selector.set(servers[0])  # Default selection

create_folder_button = tk.Button(operations_frame, text="Create folder", command=create_folder)
create_folder_button.grid(row=1, column=0, padx=5, pady=5)

transfer_button = tk.Button(operations_frame, text="Transfer files", command=transfer_files)
transfer_button.grid(row=1, column=1, padx=5, pady=5)

run_program_button = tk.Button(operations_frame, text="Run program", command=run_program)
run_program_button.grid(row=2, column=0, padx=5, pady=5)

fetch_button = tk.Button(operations_frame, text="Fetch results", command=fetch_results)
fetch_button.grid(row=2, column=1, padx=5, pady=5)

check_disk_space_button = tk.Button(operations_frame, text="Check disk space", command=check_disk_space)
check_disk_space_button.grid(row=3, column=0, padx=5, pady=5)

# ================== Log Section ==================
log_frame = tk.LabelFrame(root, text="Log", padx=10, pady=10)
log_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

log_box = scrolledtext.ScrolledText(log_frame, width=60, height=10)
log_box.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

# Start the Tkinter event loop
root.mainloop()
