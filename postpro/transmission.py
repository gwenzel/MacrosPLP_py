'''Transmission

Module to store all transmission related functions
'''
import sys
import pandas as pd
from utils.utils import timeit


LIN_NAME = "plplin.csv"


@timeit
def process_lin_data(path_case, blo_eta):
    '''
    Read and process line data
    '''
    lin_data = pd.read_csv(path_case / LIN_NAME, skiprows=0)
    lin_data = lin_data.query('Hidro != "MEDIA"')
    lin_data = lin_data.rename(columns={"Hidro": "Hyd"})
    lin_data['Hyd'] = pd.to_numeric(lin_data['Hyd'])
    lin_data = lin_data.sort_values(by=["Hyd", "Etapa", "LinNom"])
    lin_param = lin_data[["LinNom"]].drop_duplicates()

    lin_data = (
        pd.merge(lin_data, blo_eta, on="Etapa")
        .loc[
            :,
            [
                "Hyd",
                "Year",
                "Month",
                "Block",
                "Block_Len",
                "LinNom",
                "LinFluP",
                "LinUso",
            ],
        ]
        .assign(
            LinFluP=lambda x: round(x["LinFluP"], 3),
            LinUso=lambda x: round(x["LinUso"], 3),
        )
    )

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


@timeit
def process_lin_data_monthly(lin_data, type="B"):
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


@timeit
def write_transmission_data(lin_param, path_out, item, df, type="B"):
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
        path_out / filename[item], index=False, header=False, na_rep=0, mode="w"
    )
    df.to_csv(path_out / filename[item], header=True, na_rep=0, mode="a")


@timeit
def transmission_converter(path_case, path_out, blo_eta):
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
