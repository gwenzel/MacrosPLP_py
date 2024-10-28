'''
PLPPLEM2

This script creates the PLPPLEM2.dat file
'''

from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path)
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('PLPPLEM2')


def create_plpplem2_file(iplp_file: Path, path_inputs: Path):

    df = pd.read_excel(iplp_file, sheet_name='PLPPlanosEmb2', engine='pyxlsb')

    # Prepare the header
    header = ["IPDNumIte", "IEtapa", "ISimul", "LDPhiPrv"]
    for i in range(1, df.shape[1] - 3):
        header.append(f"Emb  {i}")

    # Rename first column to make sure they match
    df.columns = header

    # Format the DataFrame
    df['IPDNumIte'] = df['IPDNumIte'].astype(int)
    df['IEtapa'] = 1
    df['ISimul'] = df['ISimul'].astype(int)
    df['LDPhiPrv'] = df['LDPhiPrv'].astype(float).apply(lambda x: f"{x:.7E}")
    for col in df.columns[4:]:
        df[col] = df[col].astype(float).apply(lambda x: f"{x:.7E}")

    # Create the output string
    output_str = '#'
    output_str += ", ".join(header) + "\n"
    output_str += df.to_csv(index=False, header=False, sep=',')

    # Write the output to a file
    with open(path_inputs / "plpplem2.dat", 'w', encoding='latin1') as f:
        f.write(output_str)

@timeit
def main():
    '''
    Main routine
    '''
    try:
        # Get input file path
        logger.info('Getting input file path')
        parser = define_arg_parser()
        iplp_path = get_iplp_input_path(parser)
        path_inputs = iplp_path.parent / "Temp"
        check_is_path(path_inputs)
        path_dat = iplp_path.parent / "Temp" / "Dat"
        check_is_path(path_dat)

        # Add destination folder to logger
        path_log = iplp_path.parent / "Temp" / "log"
        check_is_path(path_log)
        add_file_handler(logger, 'PLPPLEM2', path_log)

        logger.info('Printing PLPPLEM2.dat')
        create_plpplem2_file(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
