'''Fail

Module to store all failure related functions
'''
import pandas as pd


FAL_NAME = "plpfal.csv"


def fail_converter(path_case, path_out, blo_eta):
    '''
    Read, process and write all failure related data
    '''
    fail_data = pd.read_csv(path_case / FAL_NAME, skiprows=0, low_memory=False)
    fail_data = fail_data[fail_data["Hidro"] != "MEDIA"]
    fail_data = fail_data.rename(columns={"Hidro": "Hyd"}).astype(
        {"Hyd": "float64"})
    fail_data = fail_data.sort_values(["Hyd", "Etapa", "BarNom"])
    fail_data = fail_data.merge(blo_eta, on="Etapa")
    fail_data = fail_data[
        ["Hyd", "Year", "Month", "Block", "BarNom", "CenPgen", "CenEgen"]
    ]
    fail_data["CenPgen"] = fail_data["CenPgen"].round(3)
    fail_data["CenEgen"] = fail_data["CenEgen"].round(3)
    fail_data.to_csv(
        path_out / "outFailure_B.csv", header=True, na_rep=0, mode="w"
    )
