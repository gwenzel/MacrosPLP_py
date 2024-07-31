'''Transmission

Module to store all transmission related functions
'''
import sys
import pandas as pd
from pathlib import Path


LIN_NAME = "plplin.csv"
CHUNKSIZE = 100000


def process_lin_data(path_case: Path, blo_eta: pd.DataFrame) -> pd.DataFrame:
    '''
    Read and process line data
    '''
    # Define data types
    dtypes = {
        "Hidro": "category",
        "LinNom": "category",
        "LinFluP": "float32",
        "LinUso": "float32",
    }
    lin_data_list = []

    print("Reading line data, chunksize: %d" % CHUNKSIZE)

    for lin_data_c in pd.read_csv(
        path_case / LIN_NAME,
        chunksize=CHUNKSIZE,
        low_memory=False,
        dtype=dtypes,
    ):

        # print("Processing chunk %d" % len(lin_data_list))

        lin_data_c = lin_data_c[lin_data_c["Hidro"] != "MEDIA"]
        lin_data_c = lin_data_c.rename(columns={"Hidro": "Hyd"})
        lin_data_c['Hyd'] = pd.to_numeric(lin_data_c['Hyd'])

        # Remove spaces from LinNom
        lin_data_c["LinNom"] = lin_data_c["LinNom"].str.strip()

        # Merge with blo_eta
        lin_data_c = pd.merge(lin_data_c, blo_eta, on="Etapa")
        lin_data_c = lin_data_c[
            [
                "Hyd",
                "Year",
                "Month",
                "Block",
                "Block_Len",
                "LinNom",
                "LinFluP",
                "LinUso",
            ]
        ]
        lin_data_c["LinFluP"] = lin_data_c["LinFluP"].round(3)
        lin_data_c["LinUso"] = lin_data_c["LinUso"].round(3)

        # Append to list
        lin_data_list.append(lin_data_c)

    # Concatenate all chunks data
    lin_data = pd.concat(lin_data_list, axis=0)
    # Sort
    lin_data = lin_data.sort_values(["Hyd", "Year", "Month", "LinNom"])
    # Get line parameters
    lin_param = lin_data[["LinNom"]].drop_duplicates()

    # Data mensual
    lin_data_m = (
        lin_data.assign(
            LinFluP=lambda x: x["Block_Len"] * x["LinFluP"],
            LinUso=lambda x: x["Block_Len"] * x["LinUso"],
        )
        .groupby(["Hyd", "Year", "Month", "LinNom"])
        .agg(LinFluP=("LinFluP", "sum"), LinUso=("LinUso", "sum"))
        .assign(
            LinFluP=lambda x: round(x["LinFluP"], 3),
            LinUso=lambda x: round(x["LinUso"], 3),
        )
        .reset_index()
    )
    return lin_data, lin_data_m, lin_param


def process_lin_data_monthly(lin_data: pd.DataFrame, type: str = "B") -> tuple:
    '''
    Process line data to monthly
    '''
    if type == "B":
        base_headers = ["Hyd", "Year", "Month", "Block", "LinNom"]
        index = ["Hyd", "Year", "Month", "Block"]
    elif type == "M":
        base_headers = ["Hyd", "Year", "Month", "LinNom"]
        index = ["Hyd", "Year", "Month"]
    else:
        sys.exit("type must be B or M")
    LinFlu = lin_data[base_headers + ["LinFluP"]].pivot(
        index=index, columns="LinNom", values="LinFluP"
    )
    LinUse = lin_data[base_headers + ["LinUso"]].pivot(
        index=index, columns="LinNom", values="LinUso"
    )
    return LinFlu, LinUse


def write_transmission_data(lin_param: pd.DataFrame, path_out: Path,
                            item: str, df: pd.DataFrame, type: str = "B"):
    '''
    Write transmission data
    '''
    # headers
    header_data = lin_param

    if type == "B":
        head = pd.DataFrame({"LinNom": ["", "", "", "Ubic:"]})
        header = pd.concat([head, header_data]).T
        suffix = "_B"
    elif type == "M":
        head = pd.DataFrame({"LinNom": ["", "", "Ubic:"]})
        header = pd.concat([head, header_data]).T
        suffix = ""
    else:
        sys.exit("type must be B or M")

    filename = {
        "LinFlu": "outLinFlu%s.csv" % suffix,
        "LinUse": "outLinUse%s.csv" % suffix,
    }
    unit = {"LinFlu": "[MW]", "LinUse": "[%]"}

    header.iloc[0, 0] = unit[item]
    header.to_csv(
        path_out / filename[item], index=False, header=False, na_rep=0,
        mode="w"
    )
    df.to_csv(path_out / filename[item], header=True, na_rep=0, mode="a")


def transmission_converter(path_case: Path, path_out: Path,
                           blo_eta: pd.DataFrame):
    '''
    Wrap transmission read, process and write
    '''
    lin_data, lin_data_m, lin_param = process_lin_data(path_case, blo_eta)

    LinFlu_B, LinUse_B = process_lin_data_monthly(lin_data, type="B")
    LinFlu_M, LinUse_M = process_lin_data_monthly(lin_data_m, type="M")

    # Write Transmission data

    write_transmission_data(lin_param, path_out, "LinFlu", LinFlu_B, type="B")
    write_transmission_data(lin_param, path_out, "LinFlu", LinFlu_M, type="M")
    write_transmission_data(lin_param, path_out, "LinUse", LinUse_B, type="B")
    write_transmission_data(lin_param, path_out, "LinUse", LinUse_M, type="M")
