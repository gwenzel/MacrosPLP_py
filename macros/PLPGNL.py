'''
PLPGNL

This script creates the PLPGNL.dat file
'''

from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path)
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('PLPGNL')


def create_plpgnl_file(iplp_file: Path, path_inputs: Path):

    # Check if PLPGNL_ships sheet exists
    if "PLPGNL_ships" not in pd.ExcelFile(iplp_file).sheet_names:
        logger.error("Sheet PLPGNL_ships not found in input file")
        logger.error("GNL data was not generated")
        return

    # Read data from Excel sheet
    df_params = pd.read_excel(iplp_file, sheet_name='PLPGNL_ships',
                              usecols="A,C:R", skiprows=2, nrows=6,
                              index_col=0, engine='pyxlsb')

    df_ships = pd.read_excel(iplp_file, sheet_name='PLPGNL_ships',
                             usecols="A:R", skiprows=11,
                             engine='pyxlsb').dropna(how='all')

    df_rend = pd.read_excel(iplp_file, sheet_name='PLPGNL_ships',
                            usecols="T:X", skiprows=2,
                            engine='pyxlsb').dropna(how='all')

    df_etapas = pd.read_excel(iplp_file, sheet_name="Etapas",
                              usecols="A:F", skiprows=3)

    etapa_max = df_etapas['Etapa'].max()
    df_ships = df_ships[df_ships['Etapa'].isin(range(1, etapa_max + 1))]

    # Warn if there are NaN values in dataframes
    if (df_ships.isnull().values.any() or
            df_params.isnull().values.any() or
            df_rend.isnull().values.any()):
        logger.warning('There are NaN values in PLPGNL_ships')

    # Warn if there are 0 values in Check Contrato
    if (df_rend['Check Contrato'].sum() == 0):
        logger.warning("There are gas units without an active contract")

    # Fill df_ships nan with 0
    df_ships.fillna(0, inplace=True)
    # Get list of active contracts
    active_contracts = [col for col in df_params.columns if
                        df_params.loc["Habilitado", col] == 1]

    id = 1
    with open(path_inputs / "plpcnfgnl.dat", "w", encoding="latin1") as file:
        file.write("# Archivo que describe terminales GNL\n")
        file.write("# Numero de terminales GNL\n")
        file.write(f" {len(active_contracts)} \n")
        for contract in active_contracts:
            vmax = df_params.loc["Volumen Máximo", contract]
            vini = df_params.loc["Volumen Inicial", contract]
            cgnl = 0.00
            cver = df_params.loc["Costo Vertimiento GNL", contract]
            creg = df_params.loc["Costo Regasificacion", contract]
            calm = df_params.loc["Costo Almacenar", contract]
            rend = 1.00

            ncen = df_rend[df_rend["Contrato"] == contract].shape[0]
            file.write("#ID     Nombre                                       ")
            file.write("   VMax[TBtu]  Vini[TBtu]  CGNL    CVerGNL CRegGNL ")
            file.write("CAlmGNL RendGNL\n")
            file.write(f"{id:2d}      ")
            file.write(f"'{contract}'".ljust(48))
            file.write(f"{vmax:<12.2f}{vini:<12.2f}{cgnl:<8.2f}")
            file.write(f"{cver:<9.1E}".replace("E+0", "E+"))
            file.write(f"{creg:<8.2f}{calm:<8.2f}{rend:<8.2f}\n")
            file.write("# Numero centrales\n")
            file.write(f" {ncen} \n")
            file.write("# Central                                     ")
            file.write("Rendimiento [MMBtu/MWh]\n")
            for _, row in df_rend[df_rend["Contrato"] == contract].iterrows():
                file.write(f"{row['Central Gas']:45s} ")
                file.write(f"{row['Rendimiento [MMBtu/MWh]']:<10.8f}\n")
            file.write("# Numero de barcos futuros\n")
            file.write(f" {etapa_max} \n")
            file.write("# Etapa Volumen[TBtu]\n")
            for _, row in df_ships.iterrows():
                file.write(f"{row['Etapa']:<8d} {row[contract]:<8.2f}\n")
            id += 1



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
        add_file_handler(logger, 'PLPGNL', path_log)

        logger.info('Printing PLPGNL.dat')
        create_plpgnl_file(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
