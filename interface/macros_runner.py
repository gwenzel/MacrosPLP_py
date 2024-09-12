from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess

# Example of predefined cmd commands mapped to boolean values
command_dict = {
    "cmd1": "echo Command 1 executed",  # Replace with your actual command
    "cmd2": "echo Command 2 executed",  # Replace with your actual command
    "cmd3": "echo Command 3 executed",  # Replace with your actual command
}

# Example boolean dictionary (you can pass this as input)
bool_dict = {
    "cmd1": True,
    "cmd2": False,
    "cmd3": False,
}


# Function to run a command
def run_command(cmd):
    print(f"Executing: {cmd}")
    result = subprocess.run(cmd, shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    return result.stdout.decode(), result.stderr.decode()


# Function to add cmd commands to a thread pool executor
def execute_commands(bool_dict, command_dict):
    with ThreadPoolExecutor() as executor:
        # Submit only the commands corresponding to True values
        futures = {executor.submit(run_command, command_dict[key]):
                   key for key, value in bool_dict.items() if value}

        for future in as_completed(futures):
            cmd_key = futures[future]
            try:
                stdout, stderr = future.result()
                print(f"{cmd_key} output:\n{stdout}")
                if stderr:
                    print(f"{cmd_key} error:\n{stderr}")
            except Exception as e:
                print(f"{cmd_key} generated an exception: {e}")


# Example usage
if __name__ == "__main__":
    execute_commands(bool_dict, command_dict)
