import pandas as pd

from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         timeit,
                         create_logger
)
from openpyxl.utils.datetime import from_excel

logger = create_logger('filter_files')


@timeit
def create_block2day(iplp_path, path_dat, sheet_name='Block2Day'):
    # Read data from Excel file starting from cell A1 to M25
    df = pd.read_excel(iplp_path, header=None, sheet_name=sheet_name,
                       usecols="A:M", nrows=25)
    # Save data to CSV file
    csv_file = path_dat / "block2day.csv"
    df.to_csv(csv_file, index=False, header=False)


@timeit
def create_plpparam_and_plpetapas(iplp_path, path_dat):
    df_etapas = pd.read_excel(iplp_path, sheet_name='Etapas', skiprows=3)
    df_hidro = pd.read_excel(iplp_path, sheet_name='Hidrología',
                             skiprows=1, header=None, usecols='B:D', nrows=6)
    
    df_etapas['Inicial'] = df_etapas['Inicial'].apply(from_excel)
    df_etapas['Final'] = df_etapas['Final'].apply(from_excel)
    
    etapas = df_etapas.shape[0]
    bloques = df_etapas.loc[0, 'Nº Bloques']
    n = etapas - 1

    # Prepare the data to write to plpparam
    data = [
        ("Nº Hidr:", df_hidro.iloc[2,2]),
        ("Nº Sim:", df_hidro.iloc[0,2]),
        ("Nº Bloq:", bloques),
        ("", "", ""),
        ("", "Mes", "Año"),
        ("Inicio:", f"{df_etapas.loc[0, 'Inicial'].month}", f"{df_etapas.loc[0, 'Inicial'].year}"),
        ("Fin:", f"{df_etapas.loc[n, 'Final'].month}", f"{df_etapas.loc[n, 'Final'].year}")
    ]
    # Convert the data to a DataFrame
    df = pd.DataFrame(data)

    # Write the DataFrame to plpparam
    csv_file = path_dat / "plpparam.csv"
    df.to_csv(csv_file, index=False, header=None, encoding='latin1')

    # Prepare the data to write to plpetapas
    plp_etapas_data = [("Etapa", "Year", "Month", "Block")]
    for e in range(etapas):
        for b in range(bloques): 
            plp_etapas_data.append(
                ( 1 + (12*e+b), f"{df_etapas.loc[e, 'Inicial'].year}",
                f"{df_etapas.loc[e, 'Inicial'].month}", b + 1)
            )
    
    # Convert the data to a DataFrame
    df = pd.DataFrame(plp_etapas_data)

    # Write the DataFrame to plpetapas
    csv_file = path_dat / "plpetapas.csv"
    df.to_csv(csv_file, index=False, header=None, encoding='latin1')


@timeit
def main():
    '''
    Main routine
    '''
    # Get input file path
    logger.info('Getting input file path')
    parser = define_arg_parser()
    iplp_path = get_iplp_input_path(parser)

    logger.info('Checking if folders exist, create them otherwise')

    path_inputs = iplp_path.parent / "Temp"
    path_inputs.mkdir(parents=True, exist_ok=True)
    check_is_path(path_inputs)

    path_dat = iplp_path.parent / "Temp" / "Dat"
    path_dat.mkdir(parents=True, exist_ok=True)
    check_is_path(path_dat)

    path_sal = iplp_path.parent / "Temp" / "Sal"
    path_sal.mkdir(parents=True, exist_ok=True)
    check_is_path(path_sal)

    path_dat_plexos = iplp_path.parent / "Temp" / "Dat Plexos"
    path_dat_plexos.mkdir(parents=True, exist_ok=True)
    check_is_path(path_dat_plexos)

    logger.info('Create block2day')
    create_block2day(iplp_path, path_dat)
    create_block2day(iplp_path, path_dat_plexos)

    logger.info('Create plpparam and plpetapas')
    create_plpparam_and_plpetapas(iplp_path, path_dat)

    logger.info('Finished successfully')


if __name__ == "__main__":
    main()