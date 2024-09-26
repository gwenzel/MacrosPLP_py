import tkinter as tk
from tkinter import filedialog, scrolledtext
import tkinter.ttk as ttk

import paramiko
import time

from pathlib import Path
from functools import wraps

from macros_runner import execute_commands
from logger import create_logger, add_file_handler

USERNAME = "comer"
PASSWORD = "12345"

# TODO PLP MACROS VERSION + INSTALL BUTTON

# Dummy server data
servers = [
    {"name": "Server 1 (Santiago)", "ip": "10.18.243.215"},
    {"name": "Server 2 (Antofagasta)", "ip": "192.168.74.250"}
]

logger = create_logger('PLPtron_9000')
add_file_handler(logger, 'PLPtron_9000', Path(__file__).parent)

plp_commands = [
    {'description': 'Dat Files + Etapa2Dates',
     'command': 'python -c "from macros.filter_files import main; main()"',
     'parallel': False},
    {'description': 'Demand',
     'command': 'python -c "from macros.dem import main; main()"',
     'parallel': True},
    {'description': 'Inflow',
     'command': 'python -c "from macros.inflows import main;' +
        ' main(plp_enable=True, plx_enable=False)"',
     'parallel': True},
    {'description': 'Variable Cost',
     'command':  'python -c "from macros.cvar import main; main()"',
     'parallel': True},
    {'description': 'Buses',
     'command':  'python -c "from macros.bar import main; main()"',
     'parallel': False},
    {'description': 'Blocks',
     'command':  'python -c "from macros.blo import main; main()"',
     'parallel': False},
    {'description': 'Lines',
     'command':  'python -c "from macros.lin import main; main()"',
     'parallel': False},
    {'description': 'Lines Maintenance (In/Out)',
     'command':  'python -c "from macros.manli import main; main()"',
     'parallel': False},
    {'description': 'Lines Maintenance (Exp)',
     'command':  'python -c "from macros.manlix import main; main()"',
     'parallel': False},
    {'description': 'Generators',
     'command':  'python -c "from macros.cen import main; main()"',
     'parallel': False},
    {'description': 'Generators Maintenance (Exp)',
     'command':  'python -c "from macros.mantcen import main; main()"',
     'parallel': False},
    {'description': 'Generators ERNC',
     'command':  'python -c "from macros.ernc import main; main()"',
     'parallel': False},
    {'description': 'Mathematical Programming (Iterations)',
     'command':  'python -c "from macros.mat import main; main()"',
     'parallel': False},
]

plexos_commands = [
    {'description': 'Command 1',
     'command': 'echo Command 1 executed',
     'parallel': True},
    {'description': 'Command 2',
     'command': 'echo Command 2 executed',
     'parallel': False},
    {'description': 'Command 3',
     'command': 'echo Command 3 executed',
     }
]


def timeit(func):
    '''
    Wrapper to measure time
    '''
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        log_message(f'Function {func.__name__} took {total_time:.4f} seconds')
        return result
    return timeit_wrapper


# Functions to interact with remote server
@timeit
def generate_inputs_PLP():
    # Check if file_path is valid file
    if (not Path(file_path.get()).exists()) or (
            not Path(file_path.get()).is_file()):
        log_message("Please select a valid file.")
        return
    # Select inputs if any
    selected_inputs = [plp_commands[i]['description']
                       for i, var in enumerate(input_vars_A) if var.get()]
    log_message(f"Generating Inputs PLP: {', '.join(selected_inputs)}")
    # Actual logic to generate the selected inputs for A
    bool_dict = {
        plp_commands[i]['description']: var.get()
        for i, var in enumerate(input_vars_A)
        }
    parallel_dict = {
        plp_commands[i]['description']: plp_commands[i]['parallel']
    }
    command_dict = {
        plp_commands[i]['description']: (
            plp_commands[i]['command'] + ' -f "' + file_path.get() + '"')
        for i, var in enumerate(input_vars_A)
        }
    if any(bool_dict.values()):
        log_message("Inputs PLP running.")
        execute_commands(bool_dict, parallel_dict, command_dict, logger)
    else:
        log_message("No inputs selected.")
    log_message("Inputs PLP generated. Please validate files.")


def generate_inputs_Plexos():
    selected_inputs = [plexos_commands[i]['description']
                       for i, var in enumerate(input_vars_B) if var.get()]
    log_message(f"Generating Inputs Plexos: {', '.join(selected_inputs)}")
    # Actual logic to generate the selected inputs for B
    bool_dict = {
        plexos_commands[i]['description']: var.get()
        for i, var in enumerate(input_vars_B)
        }
    parallel_dict = {
        plexos_commands[i]['description']: plexos_commands[i]['parallel']
    }
    command_dict = {
        plexos_commands[i]['description']: plexos_commands[i]['command']
        for i, var in enumerate(input_vars_B)
        }
    execute_commands(bool_dict, parallel_dict, command_dict, logger)
    if any(bool_dict.values()):
        log_message("Inputs Plexos generated.")
    else:
        log_message("No inputs selected.")


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


def check_disk_space(server_ip):
    log_message("Checking disk space on remote server...")
    # Use df command to check disk space
    command = "df -h /dev/sda2"
    host = server_ip
    if host != "":
        # Use paramiko to connect to remote server
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=USERNAME, password=PASSWORD)
        _, _stdout, _ = client.exec_command(command)
        log_message(_stdout.read().decode())
        client.close()
    else:
        log_message("Please select a server first.")


def browse_file():
    filename = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsb *.xlsx *.xlsm *.xls")])
    if filename:
        file_path.set(filename)
        log_message(f"File selected: {filename}")
    else:
        log_message("File selection cancelled.")


# Toggle visibility of input checkboxes for A
def toggle_checkboxes_PLP():
    if checkbox_frame_A.winfo_viewable():
        checkbox_frame_A.grid_remove()
        toggle_button_A.config(text="Show")
    else:
        checkbox_frame_A.grid()
        toggle_button_A.config(text="Hide")


# Toggle visibility of input checkboxes for B
def toggle_checkboxes_Plexos():
    if checkbox_frame_B.winfo_viewable():
        checkbox_frame_B.grid_remove()
        toggle_button_B.config(text="Show")
    else:
        checkbox_frame_B.grid()
        toggle_button_B.config(text="Hide")


# Select or deselect all checkboxes for Inputs PLP
def select_all_PLP():
    for var in input_vars_A:
        var.set(True)


def deselect_all_PLP():
    for var in input_vars_A:
        var.set(False)


# Select or deselect all checkboxes for Inputs Plexos
def select_all_Plexos():
    for var in input_vars_B:
        var.set(True)


def deselect_all_Plexos():
    for var in input_vars_B:
        var.set(False)


# Logger for the text box
def log_message(message):
    log_box1.insert(tk.END, message + '\n')
    log_box1.see(tk.END)
    log_box2.insert(tk.END, message + '\n')
    log_box2.see(tk.END)
    logger.info(message)


if __name__ == "__main__":
    # Tkinter setup
    root = tk.Tk()
    root.title("PLPtrón 9000 - v1.0.0")

    # Add tabs
    tabControl = ttk.Notebook(root) 
    tab1 = ttk.Frame(tabControl)
    tab2 = ttk.Frame(tabControl)
    tabControl.add(tab1, text='Inputs PLP y Plexos')
    tabControl.add(tab2, text='Servers PLP')
    tabControl.pack(expand=1, fill="both")

    # ================== Input Section ==================
    input_frame = tk.LabelFrame(tab1, text="Input Selection", padx=10, pady=10)
    input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    # File selection frame
    file_frame = tk.Frame(input_frame)
    file_frame.grid(row=0, column=0, padx=10, pady=10, columnspan=2)

    file_path = tk.StringVar()
    file_entry = tk.Entry(file_frame, textvariable=file_path, width=100)
    file_entry.grid(row=0, column=0, padx=5, pady=5)

    browse_button = tk.Button(file_frame, text="Browse", command=browse_file)
    browse_button.grid(row=0, column=1, padx=5, pady=5)

    # Left side frame------------------------------------------------------------
    # Left side: Inputs PLP
    left_frame = tk.LabelFrame(input_frame, text="PLP Inputs",
                               padx=10, pady=10)
    left_frame.grid(row=1, column=0, padx=10, pady=10)

    # Generate inputs button for Inputs PLP
    generate_button_A = tk.Button(
        left_frame, text="Generate Inputs PLP", command=generate_inputs_PLP)
    generate_button_A.grid(row=0, column=0, padx=5, pady=5)

    # Select All and Deselect All for Inputs PLP
    select_all_button_A = tk.Button(
        left_frame, text="Select All", command=select_all_PLP)
    select_all_button_A.grid(row=0, column=1, padx=5, pady=5)

    deselect_all_button_A = tk.Button(
        left_frame, text="Deselect All", command=deselect_all_PLP)
    deselect_all_button_A.grid(row=0, column=2, padx=5, pady=5)

    # Button to toggle visibility of the checkboxes for Inputs PLP
    toggle_button_A = tk.Button(
        left_frame, text="Show", command=toggle_checkboxes_PLP)
    toggle_button_A.grid(row=0, column=3, padx=5, pady=5)

    # Checkboxes for selecting Inputs PLP to generate (Initially hidden)
    checkbox_frame_A = tk.Frame(left_frame)

    input_vars_A = []
    for i, option in enumerate(plp_commands):
        var = tk.BooleanVar()
        chk = tk.Checkbutton(checkbox_frame_A,
                             text=option['description'],
                             variable=var)
        chk.grid(row=i+1, column=0, padx=5, pady=2, sticky='w')
        input_vars_A.append(var)

    # Initially hide the checkboxes for A
    checkbox_frame_A.grid(row=1, column=0, columnspan=4, padx=5, pady=5)
    checkbox_frame_A.grid_remove()

    # Right side frame------------------------------------------------------------
    # Right side: Inputs Plexos
    right_frame = tk.LabelFrame(
        input_frame, text="Plexos Inputs", padx=10, pady=10)
    right_frame.grid(row=1, column=1, padx=10, pady=10)

    # Generate inputs button for Inputs Plexos
    generate_button_B = tk.Button(
        right_frame, text="Generate Inputs Plexos",
        command=generate_inputs_Plexos)
    generate_button_B.grid(row=0, column=0, padx=5, pady=5)

    # Select All and Deselect All for Inputs Plexos
    select_all_button_B = tk.Button(
        right_frame, text="Select All", command=select_all_Plexos)
    select_all_button_B.grid(row=0, column=1, padx=5, pady=5)

    deselect_all_button_B = tk.Button(
        right_frame, text="Deselect All", command=deselect_all_Plexos)
    deselect_all_button_B.grid(row=0, column=2, padx=5, pady=5)

    # Button to toggle visibility of the checkboxes for Inputs Plexos
    toggle_button_B = tk.Button(
        right_frame, text="Show",
        command=toggle_checkboxes_Plexos)
    toggle_button_B.grid(row=0, column=3, padx=5, pady=5)

    # Checkboxes for selecting Inputs Plexos to generate (Initially hidden)
    checkbox_frame_B = tk.Frame(right_frame)

    input_vars_B = []
    for i, option in enumerate(plexos_commands):
        var = tk.BooleanVar()
        chk = tk.Checkbutton(checkbox_frame_B,
                             text=option['description'],
                             variable=var)
        chk.grid(row=i+1, column=0, padx=5, pady=2, sticky='w')
        input_vars_B.append(var)

    # Initially hide the checkboxes for B
    checkbox_frame_B.grid(row=1, column=0, columnspan=4, padx=5, pady=5)
    checkbox_frame_B.grid_remove()

    # ================== Operations Section ==================
    operations_frame = tk.LabelFrame(tab2, text="Operations", padx=10, pady=10)
    operations_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    # Server selector (Combobox allows user to enter their own option)
    server_label = tk.Label(operations_frame, text="Select server:")
    server_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')

    server_selector = ttk.Combobox(
        operations_frame, values=[server["name"] for server in servers])
    server_selector.grid(row=0, column=1, padx=5, pady=5)

    # Display value chosen in separate box
    server_ip = tk.StringVar("")
    server_ip_label = tk.Label(operations_frame, textvariable=server_ip)
    server_ip_label.grid(row=0, column=2, padx=5, pady=5)

    def update_server_ip(event):
        server_ip.set(servers[server_selector.current()]["ip"])
    server_selector.bind("<<ComboboxSelected>>", update_server_ip)

    # Arrange buttons horizontally
    create_folder_button = tk.Button(
        operations_frame, text="Create folder", command=create_folder)
    create_folder_button.grid(row=1, column=0, padx=5, pady=5)

    transfer_button = tk.Button(
        operations_frame, text="Transfer files", command=transfer_files)
    transfer_button.grid(row=1, column=1, padx=5, pady=5)

    run_program_button = tk.Button(
        operations_frame, text="Run program", command=run_program)
    run_program_button.grid(row=1, column=2, padx=5, pady=5)

    fetch_button = tk.Button(
        operations_frame, text="Fetch results", command=fetch_results)
    fetch_button.grid(row=1, column=3, padx=5, pady=5)

    check_disk_space_button = tk.Button(
        operations_frame, text="Check disk space",
        command=lambda: check_disk_space(server_ip.get()))
    check_disk_space_button.grid(row=1, column=4, padx=5, pady=5)

    # Ensure the buttons and combobox expand with the frame
    operations_frame.grid_columnconfigure(0, weight=1)
    operations_frame.grid_columnconfigure(1, weight=1)
    operations_frame.grid_columnconfigure(2, weight=1)
    operations_frame.grid_columnconfigure(3, weight=1)
    operations_frame.grid_columnconfigure(4, weight=1)

    # ================== Log Section ==================
    log_frame1 = tk.LabelFrame(tab1, text="Log", padx=10, pady=10)
    log_frame1.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    log_box1 = scrolledtext.ScrolledText(log_frame1, width=90, height=10)
    log_box1.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

    # Ensure the log box expands with the window
    log_frame1.grid_columnconfigure(0, weight=1)
    log_frame1.grid_rowconfigure(0, weight=1)

    log_frame2 = tk.LabelFrame(tab2, text="Log", padx=10, pady=10)
    log_frame2.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    log_box2 = scrolledtext.ScrolledText(log_frame2, width=90, height=10)
    log_box2.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

    # Ensure the log box expands with the window
    log_frame2.grid_columnconfigure(0, weight=1)
    log_frame2.grid_rowconfigure(0, weight=1)

    # Start the Tkinter event loop
    root.mainloop()
