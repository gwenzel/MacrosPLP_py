import pandas as pd
from datetime import timedelta
from pathlib import Path
from openpyxl.utils.datetime import from_excel
from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         timeit,
                         create_logger)


logger = create_logger('filter_files')


def create_block2day(iplp_path: Path, path_dat: Path,
                     sheet_name: str = 'Block2Day'):
    # Read data from Excel file starting from cell A1 to M25
    df = pd.read_excel(iplp_path, header=None, sheet_name=sheet_name,
                       usecols="A:M", nrows=25)
    # Save data to CSV file
    csv_file = path_dat / "block2day.csv"
    df.to_csv(csv_file, index=False, header=False)


def create_plpparam_and_plpetapas(iplp_path: Path, path_dat: Path,
                                  path_dat_plexos: Path):
    # read data
    df_etapas = pd.read_excel(iplp_path, sheet_name='Etapas', skiprows=3)
    df_hidro = pd.read_excel(iplp_path, sheet_name='Hidrología',
                             skiprows=1, header=None, usecols='B:D', nrows=6)
    # format data
    df_etapas['Inicial'] = df_etapas['Inicial'].apply(from_excel)
    df_etapas['Final'] = df_etapas['Final'].apply(from_excel)

    # create csv files
    create_plpparam(df_hidro, df_etapas, path_dat)
    create_plpetapas(df_etapas, path_dat)
    create_simtohyd(df_hidro, df_etapas, path_dat, path_dat_plexos)


def create_plpparam(df_hidro: pd.DataFrame, df_etapas: pd.DataFrame,
                    path_dat: Path):

    etapas = df_etapas.shape[0]
    bloques = df_etapas.loc[0, 'Nº Bloques']
    n = etapas - 1

    ini_month = f"{df_etapas.loc[0, 'Inicial'].month}"
    ini_year = f"{df_etapas.loc[0, 'Inicial'].year}"
    end_month = f"{df_etapas.loc[n, 'Final'].month}"
    end_year = f"{df_etapas.loc[n, 'Final'].year}"

    # Prepare the data to write to plpparam
    data = [
        ("Nº Hidr:", df_hidro.iloc[2, 2]),
        ("Nº Sim:", df_hidro.iloc[0, 2]),
        ("Nº Bloq:", bloques),
        ("", "", ""),
        ("", "Mes", "Año"),
        ("Inicio:", ini_month, ini_year)
        ("Fin:", end_month, end_year)
    ]
    # Convert the data to a DataFrame
    df = pd.DataFrame(data)

    # Write the DataFrame to plpparam
    csv_file = path_dat / "plpparam.csv"
    df.to_csv(csv_file, index=False, header=None, encoding='latin1')


def create_plpetapas(df_etapas: pd.DataFrame, path_dat: Path):

    etapas = df_etapas.shape[0]
    bloques = df_etapas.loc[0, 'Nº Bloques']

    # Prepare the data to write to plpetapas
    plp_etapas_data = [("Etapa", "Year", "Month", "Block")]
    for e in range(etapas):
        for b in range(bloques):
            plp_etapas_data.append(
                (1 + (12*e+b), f"{df_etapas.loc[e, 'Inicial'].year}",
                    f"{df_etapas.loc[e, 'Inicial'].month}", b + 1)
            )

    # Convert the data to a DataFrame
    df = pd.DataFrame(plp_etapas_data)

    # Write the DataFrame to plpetapas
    csv_file = path_dat / "plpetapas.csv"
    df.to_csv(csv_file, index=False, header=None, encoding='latin1')


def create_simtohyd(df_hidro: pd.DataFrame, df_etapas: pd.DataFrame,
                    path_dat: Path, path_dat_plexos: Path):

    fecha_ini = df_etapas.loc[0, 'Inicial']
    n_meses = df_etapas.shape[0]
    total_hidro = df_hidro.iloc[2, 2]
    total_sim = df_hidro.iloc[0, 2]
    n_blo = df_etapas.loc[0, 'Nº Bloques']

    # Initialize empty lists to store data
    data_list_plp = [("ETA_Date", "ID_Hyd", "ID_Sym")]
    data_list_plexos = [("Year", "Month", "Hour", "ID_Hyd", "ID_Sym")]

    def format_data_plp(etapa, b, h, hidro, sim):
        return (f"{(etapa - 1) * n_blo + b}",
                f"{hidro}", f"{sim}")

    def format_data_plexos(fecha, h, hidro, sim):
        return (f"{fecha.year}", f"{fecha.month}",
                f"{h}", f"{hidro}", f"{sim}")

    # Loop through each simulation (Sim)
    for Sim in range(1, total_sim + 1):
        Hidro = Sim
        fecha = fecha_ini

        # Loop through each stage (Etapa)
        for Etapa in range(1, n_meses + 1):
            for b in range(1, n_blo + 1):
                data_list_plp.append(
                    format_data_plp(Etapa, b, 0, Hidro, Sim))

            for h in range(1, 25):
                data_list_plexos.append(
                    format_data_plexos(fecha, h, Hidro, Sim))

            fecha += timedelta(days=30)  # Add one month to the current date
            if fecha.month == 4:
                Hidro += 1
                if Hidro > total_hidro:
                    Hidro = 1

    # Create pandas DataFrames from the accumulated data
    df_plp = pd.DataFrame(data_list_plp)
    df_plexos = pd.DataFrame(data_list_plexos)

    # Write the DataFrame to plpetapas
    csv_file = path_dat / "SimToHyd.csv"
    df_plp.to_csv(csv_file, index=False, header=None, encoding='latin1')

    # Write the DataFrame to plpetapas
    csv_file = path_dat_plexos / "SimToHyd_Hour.csv"
    df_plexos.to_csv(csv_file, index=False, header=None, encoding='latin1')


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
    create_plpparam_and_plpetapas(iplp_path, path_dat, path_dat_plexos)

    logger.info('Finished successfully')


if __name__ == "__main__":
    main()
