'''Marginal Costs

Module to store all functions related with marginal costs
'''
import pandas as pd
from pathlib import Path
import threading


BAR_NAME = "plpbar.csv"
CHUNKSIZE = 100000


def read_plpbar_file(path_case: Path,
                     blo_eta: pd.DataFrame) -> tuple[
                     pd.DataFrame, pd.DataFrame]:
    '''
    Read and process marginal costs and demand data from plpbar file
    '''
    dtypes = {
        "Hidro": "category",
        "BarNom": "category",
        "Etapa": "int32",
        "CMgBar": "float32",
        "DemBarE": "float32"
    }
    bar_data_list = []

    print("Reading marginal costs data, chunksize: %d" % CHUNKSIZE)

    for bar_data_c in pd.read_csv(path_case / BAR_NAME,
                                  chunksize=CHUNKSIZE,
                                  low_memory=False,
                                  dtype=dtypes):

        # print("Processing chunk %d" % len(bar_data_list))

        # Remove spaces from BarNom
        bar_data_c["BarNom"] = bar_data_c["BarNom"].str.strip()

        # Filter out MEDIA
        bar_data_c = bar_data_c[bar_data_c["Hidro"] != "MEDIA"]
        # Hydro to numeric
        bar_data_c['Hidro'] = pd.to_numeric(bar_data_c['Hidro'])
        # Rename column
        bar_data_c = bar_data_c.rename(columns={"Hidro": "Hyd"})

        # Merge with blo_eta
        bar_data_c = pd.merge(bar_data_c, blo_eta, on="Etapa", how="left")
        bar_data_c = bar_data_c[
            ["Hyd", "Year", "Month", "Block", "Block_Len", "BarNom", "CMgBar",
             "DemBarE"]
        ]
        bar_data_c["CMgBar"] = bar_data_c["CMgBar"].round(3)
        bar_data_c["DemBarE"] = bar_data_c["DemBarE"].round(3)

        # Append to list
        bar_data_list.append(bar_data_c)

    # Concatenate all chunks data
    bar_data = pd.concat(bar_data_list, axis=0)
    # Sort
    bar_data = bar_data.sort_values(["Hyd", "Year", "Month",
                                     "Block", "BarNom"])
    # Get bar parameters
    bar_param = bar_data[["BarNom"]].drop_duplicates()

    return bar_data, bar_param


def bar_process(bar_data: pd.DataFrame, columns: list, indexes: list,
                values: str) -> pd.DataFrame:
    '''
    Bar process
    '''
    bar_data[values] = bar_data[values].round(3)
    bar_data = bar_data.reset_index(drop=False)
    bar_data.index = bar_data.index.astype('int32')
    return bar_data[columns].pivot_table(index=indexes, columns="BarNom",
                                         values=values)


def process_cmg_dem(bar_data: pd.DataFrame, resolution: str,
                    values: str) -> pd.DataFrame:
    '''
    Process CMg and Dem
    '''
    bar_data_m = bar_data.copy()

    if resolution == 'B':
        columns = ["Hyd", "Year", "Month", "Block", "BarNom"]
        indexes = ["Hyd", "Year", "Month", "Block"]
        return bar_process(bar_data, columns + [values], indexes,
                           values=values)
    elif resolution == 'M':
        # Multiply by block length and divide by hours in day
        bar_data_m["CMgBar"] = \
            bar_data_m["Block_Len"] * bar_data_m["CMgBar"] / 24
        # Group by using sum as aggregation, for CMg and Dem
        bar_data_m = \
            bar_data_m.groupby(["Hyd", "Year", "Month", "BarNom"]).agg(
                CMgBar=("CMgBar", "sum"), DemBarE=("DemBarE", "sum")
                )
        columns = ["Hyd", "Year", "Month", "BarNom"]
        indexes = ["Hyd", "Year", "Month"]
        return bar_process(bar_data_m, columns + [values], indexes,
                           values=values)
    else:
        raise ValueError("resolution must be B or M")


def write_marginal_costs_file(bar_param: pd.DataFrame, path_out: Path,
                              item: str, df: pd.DataFrame, type: str = 'B'):
    '''
    Write marginal costs data
    '''
    if type == "B":
        head = pd.DataFrame({"BarNom": ["", "", "", "Ubic:"]})
        header = pd.concat([head, bar_param]).T
        suffix = '_B'
    elif type == "M":
        head = pd.DataFrame({"BarNom": ["", "", "Ubic:"]})
        header = pd.concat([head, bar_param]).T
        suffix = ''
    else:
        raise ValueError("type must be B or M")
    filename = {
        "CMg": "outBarCMg%s.csv" % suffix,
        "Dem": "outDemEne%s.csv" % suffix,
    }
    unit = {
        "CMg": "[USD/MWh]",
        "Dem": "[GWh]",
    }
    header.iloc[0, 0] = unit[item]
    header.to_csv(path_out / filename[item], na_rep=0, header=False,
                  index=False, mode="w")
    df.to_csv(path_out / filename[item], na_rep=0, header=True, mode="a")


def process_and_write(bar_data: pd.DataFrame, resolution: str, values: str,
                      bar_param: pd.DataFrame, path_out: Path, item: str):
    '''
    Group both process and write functions to multithread them
    '''
    df = process_cmg_dem(bar_data, resolution, values)
    write_marginal_costs_file(bar_param, path_out, item, df, resolution)


def marginal_costs_converter(path_case: Path, path_out: Path,
                             blo_eta: pd.DataFrame):
    '''
    Wrap marginal costs read, process and write
    '''
    # Read and process data
    bar_data, bar_param = read_plpbar_file(path_case, blo_eta)

    # Write files + multithreading
    t1 = threading.Thread(
            target=process_and_write,
            args=(bar_data, 'B', 'CMgBar', bar_param, path_out, 'CMg')
            )
    t2 = threading.Thread(
            target=process_and_write,
            args=(bar_data, 'B', 'DemBarE', bar_param, path_out, 'Dem')
            )
    t3 = threading.Thread(
            target=process_and_write,
            args=(bar_data, 'M', 'CMgBar', bar_param, path_out, 'CMg')
            )
    t4 = threading.Thread(
            target=process_and_write,
            args=(bar_data, 'M', 'DemBarE', bar_param, path_out, 'Dem')
            )

    t1.start()
    t2.start()
    t3.start()
    t4.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()
