import os
import pandas as pd
from pathlib import Path

from utils.logger import add_file_handler, create_logger
from utils.utils import (timeit,
                         check_is_path,
                         define_arg_parser,
                         get_iplp_input_path,
                         process_etapas_blocks)
from openpyxl.utils.datetime import from_excel

logger = create_logger('PLPIDSIMAPE_MANUAL')


def crea_archivo_PLPIDSIMAPE_MANUAL(iplp_path: Path, path_inputs: Path):
    # Configuración de directorio
    directorio = path_inputs

    # Meses hidrológicos
    meses_hid = {1: 10, 2: 11, 3: 12, 4: 1, 5: 2, 6: 3,
                 7: 4, 8: 5, 9: 6, 10: 7, 11: 8, 12: 9}

    # Rango de etapas
    df_etapas = pd.read_excel(iplp_path, sheet_name='Etapas', skiprows=3)
    n_eta = len(df_etapas)

    df_etapas['Inicial'] = df_etapas['Inicial'].apply(from_excel)
    df_etapas['Final'] = df_etapas['Final'].apply(from_excel)

    # Rango de simulaciones
    sim_df = pd.read_excel(iplp_path, sheet_name='ConfigSim', usecols="A:U")
    n_sim = sim_df.shape[1] - 1
    # n_sim_hid = pd.read_excel(iplp_path, sheet_name='Hidrología').iloc[1, 3]

    # Rango de aperturas
    ape_df = pd.read_excel(iplp_path, sheet_name='ConfigApe', usecols="A:L")
    n_ape = ape_df.shape[1] - 1

    # n_sim = pd.read_excel(iplp_path, sheet_name='Hidrología').iloc[0, 3]
    # n_ape = pd.read_excel(iplp_path, sheet_name='Hidrología').iloc[1, 3]
    n_ape_hid = pd.read_excel(iplp_path, sheet_name='Hidrología').iloc[1, 3]

    # Meses de deshielo
    f_desh = True if pd.read_excel(
        iplp_path, sheet_name='Path').iloc[33, 0].upper() != "OFF" else False
    m_lluv_ini = pd.read_excel(iplp_path, sheet_name='Path').iloc[34, 0] if \
        str(pd.read_excel(
            iplp_path, sheet_name='Path').iloc[35, 0]).isnumeric() else 4
    m_lluv_fin = pd.read_excel(iplp_path, sheet_name='Path').iloc[35, 0] if \
        str(pd.read_excel(
            iplp_path, sheet_name='Path').iloc[36, 0]).isnumeric() else 9

    # Escribe plpidap2.dat
    with open(os.path.join(directorio, "plpidap2.dat"), "w") as f:
        f.write("# Archivo de caudales por etapa (plpidap2.dat)\n")
        f.write("# Numero de etapas con caudales\n")
        f.write(f"{n_eta:8d}\n")
        f.write("# Mes   Etapa NApert ApertInd(1,...,NApert)\n")

        for i_eta in range(n_eta):
            mes = df_etapas.iloc[i_eta, 1].month
            mes_hid = meses_hid[mes]
            n_ape_aux = ape_df.iloc[i_eta, 1 + n_ape_hid]
            x_str = f"  {mes_hid:03d}   {i_eta + 1:03d}   {n_ape_aux:02d}     "
            for i_ape in range(n_ape_aux):
                x_str += f"{int(ape_df.iloc[i_eta, i_ape + 1]):02d}   "
            f.write(x_str + "\n")

    # Escribe plpidape.dat
    with open(os.path.join(directorio, "plpidape.dat"), "w") as f:
        f.write("# Archivo de caudales por etapa (plpidape.dat)\n")
        f.write("# Numero de simulaciones y etapas con caudales\n")
        f.write(f"  {n_sim:5d}     {n_eta:03d}\n")

        for i_sim in range(n_sim):
            f.write(
                f"# Mes   Etapa NApert ApertInd(1,...,NApert) - Simulacion={i_sim + 1:02d}\n")

            for i_eta in range(n_eta):
                mes = df_etapas.iloc[i_eta, 1].month
                mes_hid = meses_hid[mes]
                n_ape_aux = ape_df.iloc[i_eta, 1 + n_ape_hid]
                if i_eta == 0 and n_ape_aux == n_ape_hid:
                    x_str = f"{mes_hid:03d}   {i_eta + 1:03d}   01     {i_sim + 1:02d}   "
                else:
                    x_str = \
                        f"  {mes_hid:03d}   {i_eta + 1:03d}   {n_ape_aux:02d}     "
                    for i_ape in range(n_ape_aux):
                        if f_desh and (mes < m_lluv_ini or mes > m_lluv_fin):
                            x_str += f"{i_sim + 1:02d}   "
                        else:
                            x_str += f"{int(ape_df.iloc[i_eta, i_ape + 1]):02d}   "
                f.write(x_str + "\n")

    # Escribe plpidsim.dat
    with open(os.path.join(directorio, "plpidsim.dat"), "w") as f:
        f.write("#   Archivo de caudales por etapa (plpidsim.dat)\n")
        f.write("#   Numero de simulaciones, aperturas y etapas con caudales\n")
        f.write(f"    {n_sim:02d}  {n_ape:02d}  {n_eta:03d}\n")
        f.write("#   Mes Etapa   SimulInd(1,...,NSimul)\n")

        for i_eta in range(n_eta):
            mes = df_etapas.iloc[i_eta, 1].month
            mes_hid = meses_hid[mes]
            x_str = f"    {mes_hid:03d} {i_eta + 1:03d}     "
            for i_sim in range(n_sim):
                x_str += f"{sim_df.iloc[i_eta, i_sim + 1]:02d}  "
            f.write(x_str + "\n")


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
        add_file_handler(logger, 'PLPIDSIMAPE_MANUAL', path_log)

        # Get Hour-Blocks-Etapas definition
        logger.info('Processing block to etapas files')
        blo_eta, _, _ = process_etapas_blocks(path_dat, droptasa=False)

        # Create PLPIDSIMAPE_MANUAL files
        logger.info('Creating PLPIDSIMAPE_MANUAL files')
        crea_archivo_PLPIDSIMAPE_MANUAL(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
