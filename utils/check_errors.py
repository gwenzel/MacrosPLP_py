# Script that reads folder, lists all log files, and checks if they have errors

import os
import re
import pandas as pd
from pathlib import Path
from utils.utils import check_is_path, define_arg_parser, get_iplp_input_path


def check_errors(folder: Path) -> pd.DataFrame:
    '''
    Check errors in log files
    '''
    # Get all log files
    log_files = [f for f in os.listdir(folder) if f.endswith('.log')]
    # Initialize dataframe
    list_of_errors = []
    # Loop over log files
    for log_file in log_files:
        file_clean = True
        with open(folder / log_file, 'r') as f:
            # Read lines
            lines = f.readlines()
            # Check for errors
            for line in lines:
                if 'ERROR' in line:
                    # Get error message, removing line break and timestamp before error
                    error = line.split('ERROR : ')[1].replace('\n', '')
                    # Append to dataframe
                    list_of_errors.append({'File': log_file, 'Error': error})
                    file_clean = False
        if file_clean:
            list_of_errors.append({'File': log_file, 'Error': 'No errors found'})

    df = pd.DataFrame(list_of_errors)
    if len(df) == 0:
        df.to_csv(folder / '_no_errors.csv', index=False)
    else:
        df.to_csv(folder / '_errors.csv', index=False)


def main():
    '''
    Main routine
    '''
    parser = define_arg_parser()
    iplp_path = get_iplp_input_path(parser)

    # Add destination folder to logger
    path_log = iplp_path.parent / "Temp" / "log"
    check_is_path(path_log)

    # Check errors
    check_errors(path_log)
