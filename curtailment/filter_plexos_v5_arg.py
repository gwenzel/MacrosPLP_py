# -*- coding: utf-8 -*-
'''
Filter Plexos

Take plexos outputs and print equivalent PLP outputs,
to be used by the Curtailment Model
'''
import pandas as pd
import numpy as np
import datetime
from pathlib import Path
from argparse import ArgumentParser
from logger import create_logger, add_file_handler


logger = create_logger('filter_plexos')

# Define global variables
HYD20 = 20


Hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
         13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
Blocks = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6,
          7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12]

B2H = pd.DataFrame()
B2H['Hour'] = Hours
B2H['Block'] = Blocks


def return_on_failure(msg):
    def decorate(f):
        def applicator(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                logger.error('Error: %s' % e)
                logger.error(msg)
                logger.error('Code will continue')
            return msg
        return applicator
    return decorate


def check_is_file(path: Path):
    if not path.is_file():
        logger.error("file %s does not exist" % path)


def check_is_path(path: Path):
    if not path.exists():
        logger.warning("Path is not valid: %s" % path)
        path.mkdir(parents=True, exist_ok=True)
        logger.info("Path was created: %s" % path)


def print_in_plp_format(df: pd.DataFrame, new_indexes: list,
                        csv_out: str, PLP_Row: int):
    # Format as in PLP (set index, unstack, reset_index, add blank lines)
    df = df.set_index(new_indexes)
    df = df.unstack()
    # Drop level
    df.columns = df.columns.droplevel()
    df = df.reset_index()
    df.to_csv(csv_out, index=False)
    add_blank_lines(csv_out, PLP_Row)


def groupby_func(df: pd.DataFrame, by: list, func: str) -> pd.DataFrame:
    if func == "avg":
        return df.groupby(by=by, as_index=False).mean()
    elif func == "sum":
        return df.groupby(by=by, as_index=False).sum()


def add_blank_lines(out_file: Path, lines: int):
    with open(out_file, 'r') as original:
        data = original.read()
    with open(out_file, 'w') as modified:
        for i in range(lines):
            modified.write('\n')
        modified.write(data)


def define_outdata(f, wDir, RPaths, NPaths, oDir) -> pd.DataFrame:
    logger.info("---Defining outData: %s" % f)
    outData = pd.read_csv(Path(wDir, RPaths[0, 0], "Interval", f))
    for i in range(NPaths - 1):
        csv_path = Path(wDir, RPaths[i + 1, 0], "Interval", f)
        df = pd.read_csv(csv_path)
        outData = pd.concat([outData, df], ignore_index=True)
    outData = outData.copy().fillna(0)
    outData["DATETIME"] = pd.to_datetime(
        outData["DATETIME"], format='mixed')
    outData.insert(1, "Hyd", HYD20)
    outData.insert(2, "Year", outData["DATETIME"].dt.year)
    outData.insert(3, "Month", outData["DATETIME"].dt.month)
    outData.insert(4, "Day", outData["DATETIME"].dt.day)
    outData.insert(5, "Hour", outData["DATETIME"].dt.hour)
    outData.to_csv(Path(oDir, f), index=False)

    # Filter out columns SING_Cero and SIC_Cero, if present
    if 'SING_Cero' in outData.columns:
        outData = outData.drop(['SING_Cero'], axis=1)
    if 'SIC_Cero' in outData.columns:
        outData = outData.drop(['SIC_Cero'], axis=1)

    return outData


@return_on_failure("Print File_12B failed")
def print_outdata_12B(outData, Item_Name, Value_Name, Group_By, File_12B,
                      PLP_Div, PLP_Row, oDir, oDir_long):
    logger.info("---Printing outData 12B: %s" % File_12B)
    outData_12B = outData.copy()
    outData_12B = pd.merge(outData_12B, B2H, on='Hour', how='right')
    outData_12B = outData_12B.drop(['DATETIME', 'Day', 'Hour'], axis=1)
    outData_12B = pd.melt(outData_12B,
                          id_vars=['Hyd', 'Year', 'Month', 'Block'],
                          var_name=Item_Name,
                          value_name=Value_Name)
    outData_12B = groupby_func(
        outData_12B,
        by=['Hyd', 'Year', 'Month', 'Block', Item_Name],
        func=Group_By)
    outData_12B = outData_12B.round(3)
    # Adjust magnitude of values
    outData_12B[Value_Name] = outData_12B[Value_Name].transform(
        lambda x: x / PLP_Div)
    # Format as in PLP
    csv_out = Path(oDir, File_12B)
    print_in_plp_format(
        outData_12B, ['Hyd', 'Year', 'Month', 'Block', Item_Name], csv_out,
        PLP_Row)
    # Print in long format
    outData_12B.to_csv(Path(oDir_long, File_12B), index=False)


@return_on_failure("Print File_24H failed")
def print_outdata_24H(outData, Item_Name, Value_Name, Group_By, File_24H,
                      PLP_Div, PLP_Row, oDir, oDir_long):
    logger.info("---Printing outData 24H: %s" % File_24H)
    outData_24H = outData.copy()
    outData_24H = outData_24H.drop(['DATETIME', 'Day'], axis=1)
    outData_24H = pd.melt(outData_24H,
                          id_vars=['Hyd', 'Year', 'Month', 'Hour'],
                          var_name=Item_Name,
                          value_name=Value_Name)
    outData_24H = groupby_func(
        outData_24H, by=['Hyd', 'Year', 'Month', 'Hour', Item_Name],
        func=Group_By)
    outData_24H = outData_24H.round(3)
    # Adjust magnitude of values
    outData_24H[Value_Name] = outData_24H[Value_Name].transform(
        lambda x: x / PLP_Div)
    csv_out = Path(oDir, File_24H)
    print_in_plp_format(
        outData_24H, ['Hyd', 'Year', 'Month', 'Hour', Item_Name], csv_out,
        PLP_Row)
    # Print in long format
    outData_24H.to_csv(Path(oDir_long, File_24H), index=False)


@return_on_failure("Print File_M failed")
def print_outdata(outData, Item_Name, Value_Name, Group_By, File_M,
                  PLP_Div, PLP_Row, oDir, oDir_long):
    logger.info("---Printing outData: %s" % File_M)
    outData = outData.drop(['DATETIME', 'Day', 'Hour'], axis=1)
    outData = pd.melt(outData,
                      id_vars=['Hyd', 'Year', 'Month'],
                      var_name=Item_Name,
                      value_name=Value_Name)
    outData = groupby_func(
        outData, by=['Hyd', 'Year', 'Month', Item_Name], func=Group_By)
    outData = outData.round(3)
    # Adjust magnitude of values
    outData[Value_Name] = outData[Value_Name].transform(
        lambda x: x / PLP_Div)
    # Print in PLP format
    csv_out = Path(oDir, File_M)
    print_in_plp_format(outData, ['Hyd', 'Year', 'Month', Item_Name], csv_out,
                        PLP_Row)
    # Print in long format
    outData.to_csv(Path(oDir_long, File_M), index=False)
    return outData


@return_on_failure("Print File_PLP failed")
def print_out_plp(outData, Item_Name, Value_Name, File_M, PLP_Row,
                  Yini, Mini, Yend, Mend, oDir, pDir, oDir_long):
    logger.info("---Printing outPLP: %s" % File_M)

    csv_in = Path(pDir, File_M)
    # Leer datos y headers separados
    outPLP = pd.read_csv(csv_in, low_memory=False, skiprows=PLP_Row)

    # Filtrar por Hyd
    outPLP = outPLP.loc[outPLP['Hyd'] == HYD20]

    outPLP = pd.melt(outPLP, id_vars=['Hyd', 'Year', 'Month'],
                     var_name=Item_Name, value_name=Value_Name)

    # Drop rows that are not in the range of interest
    outPLP['Year'] = pd.to_numeric(outPLP['Year'])
    outPLP['Month'] = pd.to_numeric(outPLP['Month'])
    outPLP['DateTime'] = pd.to_datetime(
        outPLP[['Year', 'Month']].assign(DAY=1), format="mixed")
    mask_ini = (outPLP.DateTime < datetime.datetime(Yini, Mini, 1))
    mask_end = (outPLP.DateTime > datetime.datetime(Yend, Mend, 1))
    outPLP = outPLP.loc[mask_ini | mask_end]

    # Drop columns that are not in the range of interest
    outPLP = outPLP.drop(['DateTime'], axis=1)

    # Concatenate outData and outPLP
    outPLP = pd.concat([outPLP, outData], ignore_index=True)
    outPLP = outPLP.sort_values(['Hyd', 'Year', 'Month', Item_Name])

    # Print in long format
    outPLP.to_csv(Path(oDir_long, File_M), index=False)

    # Format as in PLP (set index, unstack, reset_index, add blank lines)
    # But don't skip lines
    csv_out = Path(oDir, File_M)
    print_in_plp_format(outPLP, ['Hyd', 'Year', 'Month', Item_Name],
                        csv_out, PLP_Row)


def add_headers_to_csv(out_file, df_header, indexes):
    # First, read out file as df
    df_out = pd.read_csv(out_file, encoding="latin1",
                         skip_blank_lines=True)

    # If df_header's first column is Hyd,
    # it means that there were no headers in the file,
    # so we need to skip the rest and add the 3 blank lines

    if df_header.iloc[0, 0] == 'Hyd':
        add_blank_lines(out_file, 3)
    else:
        # Define last row of df_header as header
        df_header.columns = df_header.iloc[-1]

        # Get generator columns in order
        gen_columns = df_out.columns.tolist()
        for item in indexes:
            gen_columns.remove(item)

        # Get 3 cols of header
        df_header_ini = df_header.iloc[:, :3]
        # add nan column at the beginning if there are 4 columns
        if len(indexes) == 4:
            df_header_ini.insert(0, 'nan', np.nan)

        # Then, reorder df_header based on df_out columns
        df_header_ordered = df_header.reindex(columns=gen_columns)
        # Fill nan with NA
        df_header_ordered = df_header_ordered.fillna('NA')

        # Concatenate df_header_ini and df_header_ordered
        df_header = pd.concat([df_header_ini, df_header_ordered], axis=1)

        # Finally, write to out_file
        with open(out_file, 'w', newline='') as modified:
            df_header.to_csv(modified, header=False, index=False)
            df_out.to_csv(modified, index=False)


def replace_all_headers(pDir, oDir, File_12B, File_24H, File_M, PLP_Row):
    # Replace headers in File_12B, File_24H, File_M
    df_header = pd.read_csv(Path(pDir, File_M), nrows=PLP_Row,
                            header=None)
    add_headers_to_csv(Path(oDir, File_M), df_header,
                       indexes=['Hyd', 'Year', 'Month'])
    add_headers_to_csv(Path(oDir, File_12B), df_header,
                       indexes=['Hyd', 'Year', 'Month', 'Block'])
    add_headers_to_csv(Path(oDir, File_24H), df_header,
                       indexes=['Hyd', 'Year', 'Month', 'Hour'])


def define_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Get Filter Plexos input filepaths")
    parser.add_argument(
        "-w", "--working_directory", help="Working directory",
        required=True, dest="wDir", type=str)
    parser.add_argument(
        "-p", "--plp_directory", help="PLP directory",
        required=True, dest="pDir", type=str)
    parser.add_argument(
        "-o", "--output_directory", help="Output directory",
        required=True, dest="oDir", type=str)
    parser.add_argument(
        "-f", "--folder_paths_file", help="Folder paths file",
        required=True, dest="folder_paths_file",
        type=lambda x: is_valid_file(parser, x))
    parser.add_argument(
        "-c", "--config_file", help="Config file",
        required=True, dest="config_file",
        type=lambda x: is_valid_file(parser, x))
    return parser


def is_valid_file(parser: ArgumentParser, arg: str) -> Path:
    if not Path(arg).exists():
        parser.error("The file or path %s does not exist!" % arg)
    else:
        return Path(arg)


def main():

    try:
        parser = define_arg_parser()
        args = parser.parse_args()

        # Define paths and files, and check
        wDir = Path(args.wDir)
        check_is_path(wDir)
        pDir = Path(args.pDir)
        check_is_path(pDir)
        oDir = Path(args.oDir)
        check_is_path(oDir)
        oDir_long = oDir / 'long_format'
        check_is_path(oDir_long)
        folder_paths_file = args.folder_paths_file
        check_is_file(folder_paths_file)
        config_file = args.config_file
        check_is_file(config_file)

        # Add destination folder to logger
        add_file_handler(logger, 'filter_plexos',
                         Path(oDir))

        logger.info("--Start script Filter Plexos")
        logger.info("---General Inputs directory: %s" % wDir)
        logger.info("---PLP Inputs directory: %s" % pDir)
        logger.info("---Folder paths file: %s" % folder_paths_file)
        logger.info("---Config file: %s" % config_file)
        logger.info("---Output directory: %s" % oDir)

        # Read folder paths file with paths to Plexos results
        fp = pd.read_csv(folder_paths_file)
        NPaths = len(fp)
        RPaths = fp.to_numpy()
        Yini = RPaths[0, 1]
        Mini = RPaths[0, 2]
        Yend = RPaths[NPaths - 1, 3]
        Mend = RPaths[NPaths - 1, 4]

        logger.info("---Number of paths: %s" % NPaths)

        # Read configuration from filter_plexos_config.json
        filter_config = pd.read_csv(config_file)

        # Node Price
        for idx, row in filter_config.iterrows():
            logger.info("--Processing file %s/%s: %s" %
                        (idx + 1, len(filter_config), row['Origin']))
            f = row['Origin']
            Item_Name = row['Item']
            Value_Name = row['Value']
            Group_By = row['GroupBy']
            File_24H = row['File_24H']
            File_12B = row['File_12B']
            File_M = row['File_M']
            PLP_Row = row['PLP_Row']
            PLP_Div = row['PLP_Div']

            # Define outdata
            outData = define_outdata(f, wDir, RPaths, NPaths, oDir)

            # Print outdata 12B
            print_outdata_12B(
                outData, Item_Name, Value_Name, Group_By, File_12B,
                PLP_Div, PLP_Row, oDir, oDir_long)

            # Print outdata 24H
            print_outdata_24H(
                outData, Item_Name, Value_Name, Group_By, File_24H,
                PLP_Div, PLP_Row, oDir, oDir_long)

            # Print outData
            outData = print_outdata(
                outData, Item_Name, Value_Name, Group_By, File_M,
                PLP_Div, PLP_Row, oDir, oDir_long)

            if row['PLP_Bool']:
                # Print plp files
                print_out_plp(
                    outData, Item_Name, Value_Name, File_M, PLP_Row,
                    Yini, Mini, Yend, Mend, oDir, pDir, oDir_long)
                # Replace headers in File_12B, File_24H, File_M
                replace_all_headers(pDir, oDir, File_12B, File_24H, File_M,
                                    PLP_Row)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')

    logger.info('--Finished Filter Plexos script')


if __name__ == "__main__":
    main()
