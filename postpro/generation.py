'''Generation

Module to store all processing and writing functions related to Generation data
'''
import sys
import pandas as pd
from utils import timeit


CEN_NAME = "plpcen.csv"


@timeit
def process_gen_data(path_case, blo_eta, tasa):
    '''
    Read and process generation data
    '''
    gen_data = pd.read_csv(path_case / CEN_NAME, skiprows=0)
    gen_data = gen_data[gen_data["Hidro"] != "MEDIA"]
    gen_data = (
        gen_data.rename(columns={"Hidro": "Hyd"})
        .assign(
            Hyd=pd.to_numeric(gen_data["Hidro"]), CenInyE=gen_data["CenInyE"] / 1000
        )
        .sort_values(["Hyd", "Etapa", "CenNom"])
    )
    gen_param = gen_data[["CenNom", "BarNom", "CenTip"]].drop_duplicates(
        subset=["CenNom"]
    )

    gen_data = pd.merge(gen_data, blo_eta, on="Etapa", how="left")
    gen_data = gen_data.assign(
        CenEgen=round(gen_data["CenEgen"], 3),
        CenCMg=round(
            1000 * gen_data["CenInyE"] * tasa / gen_data["CenEgen"], 3
        ),
        CenInyE=round(gen_data["CenInyE"] * tasa, 3),
        CurE=round(gen_data["CurE"], 3),
    ).drop(columns=["Etapa"])

    #import pdb; pdb.set_trace()
    gen_data_m = gen_data.groupby(["Hyd", "Year", "Month", "CenNom"]).agg(
        {"CenEgen": "sum", "CenInyE": "sum", "CurE": "sum"}
    )
    gen_data_m = gen_data_m.assign(
        CenEgen=round(gen_data_m["CenEgen"], 3),
        CenCMg=round(1000 * gen_data_m["CenInyE"] / gen_data_m["CenEgen"], 3),
        CenInyE=round(gen_data_m["CenInyE"], 3),
        CurE=round(gen_data_m["CurE"], 3),
    ).reset_index()
    return gen_data, gen_data_m, gen_param


@timeit
def process_gen_data_monthly(gen_data, type="B"):
    '''
    Process generation data to monthly and indexed by blocks
    '''
    if type == "B":
        base_headers = ["Hyd", "Year", "Month", "Block", "CenNom"]
        index = ["Hyd", "Year", "Month", "Block"]
    elif type == "M":
        base_headers = ["Hyd", "Year", "Month", "CenNom"]
        index = ["Hyd", "Year", "Month"]
    else:
        sys.exit("type must be B or M")
    Energ = gen_data[base_headers + ["CenEgen"]].pivot_table(
        index=index, columns="CenNom", values="CenEgen"
    )
    Reven = gen_data[base_headers + ["CenInyE"]].pivot_table(
        index=index, columns="CenNom", values="CenInyE"
    )
    CapPrice = gen_data[base_headers + ["CenCMg"]].pivot_table(
        index=index, columns="CenNom", values="CenCMg"
    )
    Curtail = gen_data[base_headers + ["CurE"]].pivot_table(
        index=index, columns="CenNom", values="CurE"
    )
    return Energ, Reven, CapPrice, Curtail


@timeit
def write_gen_data_file(gen_param, path_out, item, df, type="B"):
    '''
    Write generation data
    '''
    # select headers data frame
    header_data = gen_param[["BarNom", "CenTip", "CenNom"]]

    if type == "B":
        head = pd.DataFrame(
            {
                "BarNom": ["", "", "", "Ubic:"],
                "CenTip": ["", "", "", "Comb:"],
                "CenNom": ["", "", "", "Firm:"],
            }
        )
        header = pd.concat([head, header_data], axis=0).transpose()
        suffix = "_B"
    elif type == "M":
        head = pd.DataFrame(
            {
                "BarNom": ["", "", "Ubic:"],
                "CenTip": ["", "", "Comb:"],
                "CenNom": ["", "", "Firm:"],
            }
        )
        header = pd.concat([head, header_data], axis=0).transpose()
        suffix = ""
    else:
        sys.exit("type must be B or M")

    if item not in ["Energy", "Revenue", "Cap Price", "Curtailment"]:
        sys.exit("item must be in Energy, Revenue, Cap Price or Curtailment")

    filename = {
        "Energy": "outEnerg%s.csv" % suffix,
        "Revenue": "outReven%s.csv" % suffix,
        "Cap Price": "outCapPrice%s.csv" % suffix,
        "Curtailment": "outCurtail%s.csv" % suffix,
    }

    unit = {
        "Energy": "[GWh]",
        "Revenue": "[MUSD]",
        "Cap Price": "[USD/MWh]",
        "Curtailment": "[GWh]",
    }

    header.iloc[0, 0] = unit[item]
    header.to_csv(path_out / filename[item], na_rep=0, index=False, header=False)
    df.to_csv(path_out / filename[item], na_rep=0, header=True, mode="a")
