import concurrent.futures
import subprocess

# Example of predefined cmd commands mapped to boolean values
command_dict = {
    "cmd1": "echo Command 1 executed",  # Replace with your actual command
    "cmd2": "echo Command 2 executed",  # Replace with your actual command
    "cmd3": "echo Command 3 executed",  # Replace with your actual command
    "cmd4": "echo Command 4 executed",  # Replace with your actual command
}

# Example boolean dictionary for selecting commands to run
bool_dict = {
    "cmd1": True,
    "cmd2": False,
    "cmd3": True,
    "cmd4": True,
}

# Example parallel/series dictionary
parallel_dict = {
    "cmd1": True,  # Run cmd1 in parallel
    "cmd2": False, # Run cmd2 in series
    "cmd3": False, # Run cmd3 in series
    "cmd4": True,  # Run cmd4 in parallel
}


# Function to run a command
def run_command(cmd):
    print(f"Executing: {cmd}")
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode(), result.stderr.decode()


# Function to execute commands in series
def execute_series(commands):
    for cmd in commands:
        stdout, stderr = run_command(cmd)
        print(f"Series command output:\n{stdout}")
        if stderr:
            print(f"Series command error:\n{stderr}")


# Function to execute commands using thread pool executor (parallel execution)
def execute_parallel(commands):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(run_command, cmd): cmd for cmd in commands}

        for future in concurrent.futures.as_completed(futures):
            cmd = futures[future]
            try:
                stdout, stderr = future.result()
                print(f"Parallel command output ({cmd}):\n{stdout}")
                if stderr:
                    print(f"Parallel command error ({cmd}):\n{stderr}")
            except Exception as e:
                print(f"{cmd} generated an exception: {e}")


# Main function to run both parallel and series commands
def execute_commands(bool_dict, parallel_dict, command_dict):
    series_commands = []
    parallel_commands = []

    for cmd_key, run_cmd in bool_dict.items():
        if run_cmd:
            if parallel_dict.get(cmd_key, False):
                parallel_commands.append(command_dict[cmd_key])
            else:
                series_commands.append(command_dict[cmd_key])

    # Execute series commands first
    if series_commands:
        print("\nExecuting series commands...")
        execute_series(series_commands)

    # Execute parallel commands next
    if parallel_commands:
        print("\nExecuting parallel commands...")
        execute_parallel(parallel_commands)


# Example usage
if __name__ == "__main__":
    execute_commands(bool_dict, parallel_dict, command_dict)
