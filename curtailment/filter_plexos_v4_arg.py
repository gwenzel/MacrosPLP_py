# -*- coding: utf-8 -*-
'''
Filter Plexos

Take plexos outputs and print equivalent PLP outputs,
to be used by the Curtailment Model
'''
import os
import pandas as pd
import datetime
from pathlib import Path
from argparse import ArgumentParser
from logger import create_logger, add_file_handler


logger = create_logger('filter_plexos')

# Define global variables
Hydro = 20


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


def print_in_plp_format(df, new_indexes, csv_out, rows_to_skip):
    # Format as in PLP (set index, unstack, reset_index, add blank lines)
    df = df.set_index(new_indexes)
    df = df.unstack()
    # Drop level
    df.columns = df.columns.droplevel()
    df = df.reset_index()
    df.to_csv(csv_out, index=False)
    add_blank_lines(csv_out, rows_to_skip)


def groupby_func(df, by, func):
    if func == "avg":
        return df.groupby(by=by, as_index=False).mean()
    elif func == "sum":
        return df.groupby(by=by, as_index=False).sum()


def add_blank_lines(out_file, lines):
    with open(out_file, 'r') as original:
        data = original.read()
    with open(out_file, 'w') as modified:
        for i in range(lines):
            modified.write('\n')
        modified.write(data)


def define_outdata(f, wDir, RPaths, NPaths, oDir) -> pd.DataFrame:
    logger.info("---Defining outData: %s" % f)
    outData = pd.read_csv(os.path.join(wDir, RPaths[0, 0], "Interval", f))
    for i in range(NPaths - 1):
        csv_path = os.path.join(wDir, RPaths[i + 1, 0], "Interval", f)
        df = pd.read_csv(csv_path)
        outData = pd.concat([outData, df], ignore_index=True)
    outData = outData.copy().fillna(0)
    outData["DATETIME"] = pd.to_datetime(
        outData["DATETIME"], format='mixed')
    outData.insert(1, "Year", outData["DATETIME"].dt.year)
    outData.insert(2, "Month", outData["DATETIME"].dt.month)
    outData.insert(3, "Day", outData["DATETIME"].dt.day)
    outData.insert(4, "Hour", outData["DATETIME"].dt.hour)
    outData.to_csv(os.path.join(oDir, f), index=False)
    return outData


@return_on_failure("Print File_12B failed")
def print_outdata_12B(outData, Item_Name, Value_Name, Group_By, File_12B,
                      PLP_Row, oDir):
    logger.info("---Printing outData 12B: %s" % File_12B)
    outData_12B = outData.copy()
    outData_12B = pd.merge(outData_12B, B2H, on='Hour', how='right')
    outData_12B = outData_12B.drop(['DATETIME', 'Day', 'Hour'], axis=1)
    outData_12B = pd.melt(outData_12B, id_vars=['Year', 'Month', 'Block'],
                          var_name=Item_Name, value_name=Value_Name)
    outData_12B = groupby_func(
        outData_12B, by=['Year', 'Month', 'Block', Item_Name], func=Group_By)
    # Format as in PLP
    csv_out = os.path.join(oDir, File_12B)
    print_in_plp_format(
        outData_12B, ['Year', 'Month', 'Block', Item_Name], csv_out,
        PLP_Row)
    # Print in long format, using same name but with "_long" suffix
    csv_out_long = os.path.join(oDir, File_12B.replace(".csv", "_long.csv"))
    outData_12B.to_csv(csv_out_long, index=False)


@return_on_failure("Print File_24H failed")
def print_outdata_24H(outData, Item_Name, Value_Name, Group_By, File_24H,
                      PLP_Row, oDir):
    logger.info("---Printing outData 24H: %s" % File_24H)
    outData_24H = outData.copy()
    outData_24H = outData_24H.drop(['DATETIME', 'Day'], axis=1)
    outData_24H = pd.melt(outData_24H, id_vars=['Year', 'Month', 'Hour'],
                          var_name=Item_Name, value_name=Value_Name)
    outData_24H = groupby_func(
        outData_24H, by=['Year', 'Month', 'Hour', Item_Name], func=Group_By)
    csv_out = os.path.join(oDir, File_24H)
    print_in_plp_format(
        outData_24H, ['Year', 'Month', 'Hour', Item_Name], csv_out,
        PLP_Row)
    # Print in long format, using same name but with "_long" suffix
    csv_out_long = os.path.join(oDir, File_24H.replace(".csv", "_long.csv"))
    outData_24H.to_csv(csv_out_long, index=False)


@return_on_failure("Print File_M failed")
def print_outdata(outData, Item_Name, Value_Name, Group_By, File_M, PLP_Row,
                  oDir):
    logger.info("---Printing outData: %s" % File_M)
    outData = outData.drop(['DATETIME', 'Day', 'Hour'], axis=1)
    outData = pd.melt(outData, id_vars=['Year', 'Month'], var_name=Item_Name,
                      value_name=Value_Name)
    outData = groupby_func(
        outData, by=['Year', 'Month', Item_Name], func=Group_By)
    # Print in PLP format
    csv_out = os.path.join(oDir, File_M)
    print_in_plp_format(outData, ['Year', 'Month', Item_Name], csv_out,
                        PLP_Row)
    # Print in long format, using same name but with "_long" suffix
    csv_out_long = os.path.join(oDir, File_M.replace(".csv", "_long.csv"))
    outData.to_csv(csv_out_long, index=False)
    return outData


@return_on_failure("Print File_PLP failed")
def print_out_plp(outData, Item_Name, Value_Name, File_M, PLP_Row, PLP_Div,
                  Yini, Mini, Yend, Mend, oDir, pDir):
    logger.info("---Printing outPLP: %s" % File_M)
    csv_in = os.path.join(pDir, File_M)
    outPLP = pd.read_csv(csv_in, low_memory=False, skiprows=PLP_Row)
    # Filtrar por Hyd
    outPLP = outPLP.loc[outPLP['Hyd'] == Hydro]

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
    # Add Hydro index
    outData.insert(0, "Hyd", Hydro)
    # Adjust magnitude of values
    outData[Value_Name] = outData[Value_Name].transform(
        lambda x: x / PLP_Div)

    # Concatenate outData and outPLP
    outPLP = pd.concat([outPLP, outData], ignore_index=True)
    outPLP = outPLP.set_index(['Hyd', 'Year', 'Month', Item_Name]).unstack()
    outPLP = outPLP.reset_index()
    outPLP['Hyd'] = pd.to_numeric(outPLP['Hyd'])
    outPLP['Year'] = pd.to_numeric(outPLP['Year'])
    outPLP['Month'] = pd.to_numeric(outPLP['Month'])
    outPLP = outPLP.sort_values(['Hyd', 'Year', 'Month'])
    # Format as in PLP (set index, unstack, reset_index, add blank lines)
    csv_out = os.path.join(oDir, File_M)
    # Dataframe already in wide format. Print directly
    # Drop level, reset index, print and add blank line
    outPLP.columns = outPLP.columns.droplevel()
    outPLP = outPLP.reset_index(drop=True)
    # Rename first 3 columns as Hyd, Year and Month
    outPLP.columns = ['Hyd', 'Year', 'Month'] + list(outPLP.columns[3:])
    outPLP.to_csv(csv_out, index=False)
    add_blank_lines(csv_out, PLP_Row)
    # Print in long format, using same name but with "_long" suffix
    csv_out_long = os.path.join(oDir, File_M.replace(".csv", "_long.csv"))
    outPLP.to_csv(csv_out_long, index=False)


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
    if not os.path.exists(arg):
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
                outData, Item_Name, Value_Name, Group_By, File_12B, PLP_Row,
                oDir)

            # Print outdata 24H
            print_outdata_24H(
                outData, Item_Name, Value_Name, Group_By, File_24H, PLP_Row,
                oDir)

            # Print outData
            outData = print_outdata(
                outData, Item_Name, Value_Name, Group_By, File_M, PLP_Row,
                oDir)

            # Print plp files
            if row['PLP_Bool']:
                print_out_plp(
                    outData, Item_Name, Value_Name, File_M, PLP_Row, PLP_Div,
                    Yini, Mini, Yend, Mend, oDir, pDir)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')

    logger.info('--Finished Filter Plexos script')


if __name__ == "__main__":
    main()
