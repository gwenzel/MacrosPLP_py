import subprocess
import tkinter as tk
from tkinter import messagebox
import concurrent.futures


# Define the command to activate Anaconda environment and run the entry point
def run_in_env(env_name, entry_point, argument):
    # Activate Anaconda, the virtual environment, and run the entry point
    # The `&` at the end ensures that each command runs in a new shell.
    # Modify this according to the shell used (bash, cmd, etc.)
    command = f'conda activate {env_name} & {entry_point} {argument}'

    # Use subprocess.Popen to open a new shell and activate environment
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    return stdout.decode(), stderr.decode(), process.returncode == 0  # Return success status


# Function triggered when the button is pressed
def run_commands():
    env_name = env_name_entry.get()
    entry_point = entry_point_entry.get()
    argument = argument_entry.get()

    if not env_name or not entry_point or not argument:
        messagebox.showerror("Error", "All fields must be filled!")
        return

    # Run the process in a thread to avoid blocking the GUI
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_env, env_name, entry_point, argument)
        stdout, stderr, success = future.result()

        # Show result in messagebox
        if success:
            messagebox.showinfo("Success", f"Output:\n{stdout}")
        else:
            messagebox.showerror("Error", f"Error:\n{stderr}")

# Create the Tkinter interface
app = tk.Tk()
app.title("Virtual Environment Runner")

# Create and place widgets
tk.Label(app, text="Conda Environment Name:").pack(pady=5)
env_name_entry = tk.Entry(app, width=50)
env_name_entry.pack(pady=5)

tk.Label(app, text="Entry Point:").pack(pady=5)
entry_point_entry = tk.Entry(app, width=50)
entry_point_entry.pack(pady=5)

tk.Label(app, text="Argument:").pack(pady=5)
argument_entry = tk.Entry(app, width=50)
argument_entry.pack(pady=5)

run_button = tk.Button(app, text="Run Command", command=run_commands)
run_button.pack(pady=20)

# Start the Tkinter event loop
app.mainloop()
