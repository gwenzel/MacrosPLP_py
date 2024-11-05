'''
PLPMANEM_ETA

This script creates the PLPMANEM_ETA.dat file
'''

from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         translate_to_hydromonth)
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path
import math
from macros.func_cdec.lmaule import Vol_LMAULE
from macros.func_cdec.cipreses import Vol_CIPRESES
from macros.func_cdec.pehuenche import Vol_PEHUENCHE
from macros.func_cdec.colbun import Vol_COLBUN
from macros.func_cdec.eltoro import Vol_ELTORO
from macros.func_cdec.rapel import Vol_RAPEL
from macros.func_cdec.canutillar import Vol_CANUTILLAR
from macros.func_cdec.ralco import Vol_RALCO
from macros.func_cdec.pangue import Vol_PANGUE
from openpyxl.utils.datetime import from_excel


dict_dam_volfunc = {
    "LMAULE": Vol_LMAULE,
    "CIPRESES": Vol_CIPRESES,
    "PEHUENCHE": Vol_PEHUENCHE,
    "COLBUN": Vol_COLBUN,
    "ELTORO": Vol_ELTORO,
    "RAPEL": Vol_RAPEL,
    "CANUTILLAR": Vol_CANUTILLAR,
    "RALCO": Vol_RALCO,
    "PANGUE": Vol_PANGUE
}

logger = create_logger('PLPMANEM_ETA')


def create_plpmanem_eta_file(iplp_file: Path, path_inputs: Path):
    # Load Excel sheets into pandas DataFrames
    df_centrales = pd.read_excel(iplp_file, sheet_name="Centrales",
                                 usecols="A:Z", skiprows=4)
    df_etapas = pd.read_excel(iplp_file, sheet_name="Etapas",
                              usecols="A:F", skiprows=3)
    df_mant = pd.read_excel(iplp_file, sheet_name="MantEMB",
                            usecols="B:F", skiprows=4)

    # df_etapas['Date_Ini'] = df_etapas['Inicial'].apply(from_excel)
    # df_etapas['Date_Fin'] = df_etapas['Final'].apply(from_excel)

    df_mant['Date_Ini'] = df_mant['INICIAL'].apply(from_excel)
    df_mant['Date_Fin'] = df_mant['FINAL'].apply(from_excel)

    # Filter only rows where 'C' column indicates an embalse (E)
    df_embalses = df_centrales[df_centrales.iloc[:, 2] == "E"]
    n_emb = len(df_embalses)

    # Extract data for embalses
    nombre_e = df_embalses.iloc[:, 1].tolist()

    # Map Vnom_min, Vnom_max and Fescala to df_mant
    df_mant['Vnom_min'] = df_mant['EMBALSE'].apply(
        lambda x: df_embalses[df_embalses['CENTRALES'] == x].iloc[0, 24])
    df_mant['Vnom_max'] = df_mant['EMBALSE'].apply(
        lambda x: df_embalses[df_embalses['CENTRALES'] == x].iloc[0, 25])
    df_mant['Fescala'] = df_mant['Vnom_max'].apply(
        lambda x: 10 ** int(math.log10(x) + 0.5))

    dict_result = {}

    dia_ini = df_etapas.iloc[0, 1]
    dia_fin = df_etapas.iloc[-1, 3]
    n_emb = 0

    # Add Hydromonth
    df_mant['Month'] = df_mant['Date_Ini'].dt.month
    # Translate to hydromonth
    df_mant = translate_to_hydromonth(df_mant)

    # Filter maintenance records for embalses and update `v_min` and `costo`
    for i, emb_name in enumerate(nombre_e):
        mant_records = df_mant[df_mant.iloc[:, 0] == emb_name].copy()
        if not mant_records.empty:
            n_emb += 1
            if emb_name not in dict_dam_volfunc:
                logger.warning(f"Dam '{emb_name}' not found in vol functions")
                logger.warning(f"Skipping dam '{emb_name}'")
            # Create Vol column using function
            mant_records['Vol_min'] = mant_records['MÍNIMA'].apply(
                dict_dam_volfunc[emb_name]).round(7)
            mant_records['Vol_max'] = mant_records['MÁXIMA'].apply(
                dict_dam_volfunc[emb_name]).round(7)

            # Warn if any Vol is out of bounds
            if (mant_records['Vol_min'] > mant_records['Vnom_max']).any():
                logger.error(f"Dam '{emb_name}' has Vol min > Vnom_max")
                logger.error("Please fix, otherwise PLP will not run")
            if (mant_records['Vol_min'] < mant_records['Vnom_min']).any():
                logger.warning(f"Dam '{emb_name}' has Vol min < Vnom_min")
                logger.warning("Please fix, otherwise PLP may not run")
            if (mant_records['Vol_max'] > mant_records['Vnom_max']).any():
                logger.warning(f"Dam '{emb_name}' has Vol max > Vnom_max")
                logger.warning("Please fix, otherwise PLP may not run")
            if (mant_records['Vol_max'] < mant_records['Vnom_min']).any():
                logger.error(f"Dam '{emb_name}' has Vol max < Vnom_min")
                logger.error("Please fix, otherwise PLP will not run")

            # Filter out of FINAL <= dia_ini
            mant_records = mant_records[
                mant_records['FINAL'] > dia_ini]
            # Filter out if INICIAL > dia_fin
            mant_records = mant_records[
                mant_records['INICIAL'] <= dia_fin]

            # Move to dia_ini if INICIAL < dia_ini
            mant_records.loc[
                mant_records['INICIAL'] < dia_ini, 'INICIAL'] = dia_ini
            # Move to dia_fin if FINAL > dia_fin
            mant_records.loc[
                mant_records['FINAL'] > dia_fin, 'FINAL'] = dia_fin

            # Each etapa spans from Inicial to Final in df_etapas
            # Figure out in which etapa does each record fall
            mant_records['Etapa_Ini'] = mant_records['INICIAL'].apply(
                lambda x: df_etapas[df_etapas['Inicial'] <= x].index[-1] + 1)
            mant_records['Etapa_Fin'] = mant_records['FINAL'].apply(
                lambda x: df_etapas[df_etapas['Inicial'] <= x].index[-1] + 1)

            # Create mant_cen and v_min
            mant_records['MantCen_min'] = abs(mant_records['Vol_min'] -
                                              mant_records['Vnom_min'] /
                                              mant_records['Fescala']) > 1e-8
            # Create mant_cen and v_min
            mant_records['MantCen_max'] = abs(mant_records['Vol_max'] -
                                              mant_records['Vnom_max'] /
                                              mant_records['Fescala']) > 1e-8
            # Divide by Fescala
            mant_records['Vol_out_min'] = (mant_records['Vol_min'] /
                                           mant_records['Fescala'])
            mant_records['Vol_out_max'] = (mant_records['Vol_max'] /
                                           mant_records['Fescala'])

            dict_result[emb_name] = {}
            for _, row in mant_records.iterrows():
                for eta in range(row['Etapa_Ini'], row['Etapa_Fin'] + 1):
                    dict_result[emb_name][eta] = \
                        (row['Month'], row['Vol_out_min'], row['Vol_out_max'])

    # Create output file
    with open(path_inputs / "plpmanem.dat", "w", encoding="latin1") as file:
        file.write("# Archivo de mantenimientos embalses"
                   " (plpmanem.dat)\n")
        file.write("# Numero de embalses con mantenimientos\n")
        file.write(f" {len(dict_result.keys())} \n")

        for emb in dict_result.keys():
            file.write("# Nombre del embalse\n")
            file.write(f"'{emb}'\n")

            # Count stages with maintenance
            file.write("#   Numero de Etapas con mantenimiento\n")
            etapas_mant = len(dict_result[emb])
            file.write(f"    {etapas_mant:02d}\n")

            # Write minimum volume and cost for each stage with maintenance
            file.write("#   Mes   Etapa     VolMin     VolMax\n")
            for (eta), (hydmonth, v_min, v_max) in dict_result[emb].items():
                file.write(
                    f"     {hydmonth:02d}     {eta:03d}{v_min:11.7f}{v_max:11.7f}\n")


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
        add_file_handler(logger, 'PLPMANEM_ETA', path_log)

        logger.info('Printing PLPMANEM_ETA.dat')
        create_plpmanem_eta_file(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
