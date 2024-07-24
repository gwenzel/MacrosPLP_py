'''Marginal Costs

Module to store all functions related with marginal costs
'''
import sys
import pandas as pd


BAR_NAME = "plpbar.csv"
CHUNKSIZE = 1000000


def process_marginal_costs(path_case, blo_eta):
    '''
    Read an process marginal costs data
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

        print("Processing chunk %d" % len(bar_data_list))

        bar_data_c = bar_data_c[bar_data_c["Hidro"] != "MEDIA"]
        bar_data_c = bar_data_c.rename(columns={"Hidro": "Hyd"})

        # Remove spaces from BarNom
        bar_data_c["BarNom"] = bar_data_c["BarNom"].str.strip()

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


def bar_process(bar_data, columns, indexes, values):
    '''
    Bar process
    '''
    bar_data = bar_data.reset_index(drop=False)
    bar_data.index = bar_data.index.astype('int32')
    return bar_data[columns].pivot_table(index=indexes, columns="BarNom",
                                         values=values)


def process_marginal_costs_monthly(bar_data):
    '''
    Process monthly costs
    '''
    bar_data_m = bar_data.copy()
    # Multiply by block length and divide by hours in day
    bar_data_m["CMgBar"] = bar_data_m["Block_Len"] * bar_data_m["CMgBar"] / 24
    # Group by using sum as aggregation, for CMg and Dem
    bar_data_m = bar_data_m.groupby(["Hyd", "Year", "Month", "BarNom"]).agg(
        CMgBar=("CMgBar", "sum"), DemBarE=("DemBarE", "sum")
    )
    bar_data_m["CMgBar"] = bar_data_m["CMgBar"].round(3)
    bar_data_m["DemBarE"] = bar_data_m["DemBarE"].round(3)
    b_columns = ["Hyd", "Year", "Month", "Block", "BarNom"]
    b_indexes = ["Hyd", "Year", "Month", "Block"]
    m_columns = ["Hyd", "Year", "Month", "BarNom"]
    m_indexes = ["Hyd", "Year", "Month"]

    cmg_b = bar_process(bar_data, b_columns + ["CMgBar"], b_indexes,
                        values="CMgBar")
    dem_b = bar_process(bar_data, b_columns + ["DemBarE"], b_indexes,
                        values="DemBarE")
    cmg_m = bar_process(bar_data_m, m_columns + ["CMgBar"], m_indexes,
                        values="CMgBar")
    dem_m = bar_process(bar_data_m, m_columns + ["DemBarE"], m_indexes,
                        values="DemBarE")
    return cmg_b, dem_b, cmg_m, dem_m


def write_marginal_costs_file(bar_param, path_out, item, df,
                              type='B'):
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
        sys.exit("type must be B or M")
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


def marginal_costs_converter(path_case, path_out, blo_eta):
    '''
    Wrap marginal costs read, process and write
    '''
    # Read and process data
    bar_data, bar_param = process_marginal_costs(path_case, blo_eta)
    cmg_b, dem_b, cmg_m, dem_m = process_marginal_costs_monthly(bar_data)

    # Write files
    write_marginal_costs_file(bar_param, path_out, 'CMg', cmg_b,
                              type='B')
    write_marginal_costs_file(bar_param, path_out, 'CMg', cmg_m,
                              type='M')
    write_marginal_costs_file(bar_param, path_out, 'Dem', dem_b,
                              type='B')
    write_marginal_costs_file(bar_param, path_out, 'Dem', dem_m,
                              type='M')
