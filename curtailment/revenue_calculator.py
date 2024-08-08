
# -*- coding: utf-8 -*-
'''
Revenue calculator
'''
import pandas as pd
from pathlib import Path
from argparse import ArgumentParser
from logger import create_logger, add_file_handler


logger = create_logger('revenue_calculator')


def define_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Get Revenue Calculator inputs")
    parser.add_argument('-p', dest='price_file', required=True,
                        help='Price file path',
                        metavar="PRICE_FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-q', dest='energy_file', required=True,
                        help='Energy file path',
                        metavar="ENERGY_FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-o', dest='output_folder', required=True,
                        help='Path to output files',
                        metavar="OUTPUTS_PATH",
                        type=str)
    return parser


def is_valid_file(parser: ArgumentParser, arg: str) -> Path:
    if not Path(arg).exists():
        parser.error("The file or path %s does not exist!" % arg)
    else:
        return Path(arg)


def read_input_map_gen2bar(energy_file: Path) -> pd.DataFrame:
    '''
    Read input map gen2bar file
    '''
    df = pd.read_csv(energy_file, encoding='latin1', nrows=3, header=None)

    # Use first 3 rows, first is bar, second is dropped, and third is gen
    # Create dictionary between bar and gen
    df = df.T.dropna().reset_index(drop=True)
    # Drop first row (Ubic, Comb, Firm)
    df = df.drop(0, axis=0)
    # Rename Columns
    df.columns = ['bar', 'comb', 'gen']
    # Drop comb
    df = df.drop('comb', axis=1)
    # gen as index
    df = df.set_index('gen')
    # Turn df into dictionary
    dict_gen2bar = df.to_dict()['bar']
    return dict_gen2bar


def read_input_files(price_file: Path, energy_file: Path) -> tuple[
        pd.DataFrame, pd.DataFrame]:
    '''
    Read input files
    '''
    # Check if files exist
    if not price_file.exists():
        raise FileNotFoundError("Price file does not exist")
    if not energy_file.exists():
        raise FileNotFoundError("Energy file does not exist")

    # Check if ending of both file names ir _B or _H
    if ((energy_file.name[-6:] == '_B.csv') and (
            price_file.name[-6:] == '_B.csv')) or (
        (energy_file.name[-6:] == '_H.csv') and (
                price_file.name[-6:] == '_H.csv')):
        pass
    else:
        raise ValueError("Price and Energy filenames must end with"
                         " _B or _H")
    # Read price
    df_price = pd.read_csv(price_file, encoding='latin1', skiprows=1)
    # Set first 4 cols as index
    df_price = df_price.set_index(df_price.columns[:4].tolist())
    # Read energy
    df_energy = pd.read_csv(energy_file, encoding='latin1', skiprows=3)
    # Set first 4 cols as index
    df_energy = df_energy.set_index(df_energy.columns[:4].tolist())

    return df_price, df_energy


def process_data(df_price: pd.DataFrame, df_energy: pd.DataFrame,
                 dict_gen2bar: dict) -> pd.DataFrame:
    '''
    Process data
    '''
    # For each generator in in df_energy columns, multiply with price
    # Corresponding price column in df_price is found on dict_gen2bar
    df_revenue = pd.DataFrame(columns=df_energy.columns, index=df_energy.index)
    for gen in df_energy.columns:
        if gen not in dict_gen2bar.keys():
            logger.warning(f"Generator {gen} not found in energy file")
        elif dict_gen2bar[gen] not in df_price.columns:
            logger.warning(f"Bar {dict_gen2bar[gen]} not found in price file")
        else:
            bar = dict_gen2bar[gen]
            df_revenue[gen] = df_energy[gen] * df_price[bar]
    # Fill remaining NaN with 0
    df_revenue.fillna(0, inplace=True)
    return df_revenue


def main():

    try:
        parser = define_arg_parser()
        args = parser.parse_args()

        price_file = Path(args.price_file)
        energy_file = Path(args.energy_file)
        output_folder = Path(args.output_folder)

        # Add destination folder to logger
        add_file_handler(logger, 'revenue_calculator',
                         Path(output_folder))

        logger.info("--Start script Revenue Calculator")

        # Read input files
        df_price, df_energy = read_input_files(price_file, energy_file)
        dict_gen2bar = read_input_map_gen2bar(energy_file)

        # Process data
        df_revenue = process_data(df_price, df_energy, dict_gen2bar)

        # Write output data
        df_revenue.to_csv(output_folder / 'new_revenue.csv')

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')

    logger.info('--Finished Revenue Calculator script')


if __name__ == "__main__":
    main()
