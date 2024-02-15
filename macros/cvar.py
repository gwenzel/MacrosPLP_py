'''Variable Cost

This module calculates the variable cost for each unit in the system.

It stores the data in csv files, and then it prints
the plpcosce.dat file with the data.
'''
from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         process_etapas_blocks,
                         translate_to_hydromonth,
                         write_lines_from_scratch,
                         write_lines_appending)
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path
from openpyxl.utils.datetime import from_excel

logger = create_logger('cvariable')

formatter_plpcosce = {
    'Month': "   {:02d}".format,
    'Etapa': "    {:03d}".format,
    'Variable Cost + CO2 Tax USD/MWh': "{:9.1f}".format
}


def read_fuel_price_iplp(iplp_path: Path, fuel: str):
    '''
    Read fuel price for each fuel type
    '''
    fuel2sheetname = {
        'Coal': 'Carbón',
        'Gas': 'GNL-GAS',
        'Diesel': 'Diesel'
    }
    if fuel not in fuel2sheetname.keys():
        logger.error('Fuel %s not recognized' % fuel)
        logger.error('Valid fuels are: Coal, Gas, Diesel')
    df = pd.read_excel(
        iplp_path, sheet_name=fuel2sheetname[fuel])
    df = df.set_index(['Combustible', 'Unidad'])
    # Warn if there are missing values
    for row in df.index:
        if df.loc[row].T.isna().any():
            logger.warning('Fuel %s has missing values, which'
                           ' will be filled with previous value' % row[0])
    df = df.stack(future_stack=True)
    df = df.reset_index()
    df = df.rename(columns={'level_2': 'Date', 0: 'Variable Cost USD/Unit'})
    df['Date'] = df['Date'].apply(from_excel)
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df = df[['Combustible', 'Unidad', 'Year', 'Month', 'Date',
             'Variable Cost USD/Unit']]
    df = df.rename(columns={'Combustible': 'Fuel Name', 'Unidad': 'Unit'})
    # Fill missing values using ffill first, then bfill
    df = df.ffill().bfill()
    return df


def validate_fuel_price(df_fuel_price: pd.DataFrame):
    # TODO validate names and values
    pass


def read_all_fuel_prices(iplp_path: Path):
    '''
    Build dictionary of dataframes with fuel price info
    for Carbon USD/ton, Gas USD/MMBtu, Diesel USD/ton
    '''
    fuel_prices = {}
    for fuel in ['Coal', 'Gas', 'Diesel']:
        fuel_prices[fuel] = read_fuel_price_iplp(
            iplp_path, fuel=fuel)
        validate_fuel_price(fuel_prices[fuel])
    df = pd.concat(fuel_prices)
    df = df.reset_index()
    df = df.drop(columns=['level_1'])
    df = df.rename(columns={'level_0': 'Fuel Category'})
    return df


def read_unit_cvar_nominal(iplp_path: Path, ernc_zero: bool = False):
    '''
    Read nominal variable cost for each unit
    '''
    df = pd.read_excel(iplp_path, sheet_name='Centrales',
                       usecols='B:D', skiprows=4,
                       index_col='CENTRALES')
    df = df[df['Tipo de Central'] == 'T']
    # If enrc_zero is true, set ernc units to 0
    if ernc_zero:
        ernc_starts_with = ['SOLAR_', 'SOLARx_', 'ENGIE_PV',
                            'EOLICA_', 'EOLICAx_', 'ENGIE_Wind',
                            'BESS_', 'BESSx_', 'ENGIE_BESS_',
                            'CSP_', 'CSPx_']
        for type in ernc_starts_with:
            df.loc[df.index.str.startswith(type), 'Costo Variable'] = 0
    # Filter columns if values are missing
    df = df.dropna(how='any')
    return df.to_dict()['Costo Variable']


def read_heatrate_and_unit_fuel_mapping(iplp_path: Path):
    '''
    Build dictionaries for heatrate and fuel price name
    for:
    - Carbon ton/MWh,
    - Gas MMBtu/MWh,
    - Diesel ton/MWh
    '''
    df = pd.read_excel(iplp_path, sheet_name='Rendimientos y CVarNcomb',
                       usecols='B,D:F')
    df = df.rename(columns={
        'Rendimiento': 'Heat Rate',
        'Combustible OSE': 'Fuel Name',
        'Costo Variable No Combustible': 'Non-Fuel Cost'})
    # Filter out missing units
    df_cen = pd.read_excel(iplp_path, sheet_name='Centrales',
                           usecols='B:C', skiprows=4)
    df = df.merge(df_cen, left_on='Central', right_on='CENTRALES')
    df = df[df['Tipo de Central'] == 'T']
    df = df.drop(columns=['Tipo de Central', 'CENTRALES'])
    if df.isna().any().any():
        logger.error('Heatrate and fuel mapping has missing values')
    return df


def read_year_co2_tax(iplp_path: Path):
    '''
    Read CO2 tax per year for current scenario
    '''
    df = pd.read_excel(iplp_path, sheet_name='CVariable',
                       usecols='J:K', skiprows=4).dropna(how='any')
    df = df.rename(columns={'CO2 Tax in USD/TonCO2': 'CO2 Tax USD/TonCO2'})
    return df


def read_unit_emissions_mapping(iplp_path: Path):
    '''
    Read CO2 emissions per unit
    '''
    df = pd.read_excel(iplp_path, sheet_name='Centrales',
                       usecols='B,C,BY', skiprows=4)
    df = df[df['Tipo de Central'] == 'T']
    df = df.drop(columns=['Tipo de Central'])
    df = df.fillna(0)
    df = df.rename(columns={
        'Factor Emisiones CO2  TonCO2/MWh': 'Emissions TonCO2/MWh',
        'CENTRALES': 'Central'})
    return df


def calculate_cvar(path_df: Path, blo_eta: pd.DataFrame,
                   df_fuel_prices: pd.DataFrame,
                   df_heatrate_unit_fuel_mapping: pd.DataFrame):
    '''
    Calculate Costo Variable for each unit in dict_unit_fuel_price_name,
    for each block in blo_eta, using fuel prices in fuel_prices
    and heatrate in dict_unit_heatrate
    '''
    # Drop Block data from blo_eta, keep only Year-Month pairs
    blo_eta_mod = blo_eta.groupby(
        ['Year', 'Month']).count().reset_index()[['Year', 'Month']]
    # Add Etapa column
    blo_eta_mod['Etapa'] = blo_eta_mod.index + 1
    # Merge to get heatrate and fuel name
    df = df_heatrate_unit_fuel_mapping.merge(blo_eta_mod, how='cross')
    # Merge with df_fuel_prices
    df = df.merge(df_fuel_prices,
                  on=['Year', 'Month', 'Fuel Name'], how='left')
    # Use ffill to fill gaps (Coal has no values after 2040)
    # Warning: for this to work, dataframes must be merged in the right order
    df = df.ffill()
    # Drop rows if price could not be calculated
    df = df.dropna(subset=['Variable Cost USD/Unit'])
    df['Variable Cost USD/MWh'] = \
        (df['Variable Cost USD/Unit'] * df['Heat Rate'] +
         df['Non-Fuel Cost']).round(1)
    # Select columns to keep
    df = df[['Etapa', 'Year', 'Month', 'Date', 'Central', 'Heat Rate',
             'Fuel Name', 'Variable Cost USD/MWh']]
    # Translate month to hydromonth
    df = translate_to_hydromonth(df)
    # df.to_csv(path_df / 'df_cvar.csv', index=False)
    return df


def add_emissions(path_df: Path, df_cvar: pd.DataFrame,
                  df_unit_emissions: pd.DataFrame,
                  df_year_co2_tax: pd.DataFrame):
    '''
    Add emissions cost to variable cost dataframe
    '''
    df = df_cvar.merge(df_unit_emissions, on='Central', how='left')
    df = df.merge(df_year_co2_tax, on='Year', how='left')
    df['CO2 Tax USD/MWh'] = \
        df['CO2 Tax USD/TonCO2'] * df['Emissions TonCO2/MWh']
    df['Variable Cost + CO2 Tax USD/MWh'] = \
        (df['Variable Cost USD/MWh'] + df['CO2 Tax USD/MWh']).round(1)
    df.to_csv(path_df / 'df_cvar_with_emissions.csv', index=False)
    return df


def validate_unit_emissions(df_unit_emissions: pd.DataFrame):
    # If there are missing values in the dataframe, log error
    if df_unit_emissions.isna().any().any():
        logger.error('Unit emissions mapping has missing values')
        return True
    return False


def validate_year_co2_tax(df_year_co2_tax: pd.DataFrame,
                          blo_eta: pd.DataFrame):
    # If there are years from blo_eta missing in df_year_co2_tax, fix and warn
    years_blo_eta = blo_eta['Year'].unique()
    years_df_year_co2_tax = df_year_co2_tax['Year'].unique()
    if not set(years_blo_eta).issubset(set(years_df_year_co2_tax)):
        logger.error('Years from blo_eta are not in df_year_co2_tax')
        return True
    return False


def validate_df_cvar_with_emissions(df_cvar_with_emissions: pd.DataFrame):
    # If there are missing values in the last column, error
    if df_cvar_with_emissions.iloc[:, -1].isna().any():
        logger.error('There are missing values in '
                     'Variable Cost + CO2 Tax USD/MWh')
        return True
    return False


def print_plpcosce(path_inputs: Path,
                   df_cvar_with_emissions: pd.DataFrame):
    '''
    Print plpcosce.dat file
    '''
    path_plpcosce = path_inputs / 'plpcosce.dat'
    lines = ['# Archivo de precios de termicas (plpcosce.dat)']
    lines += ['# Numero de centrales termicas con cambio de costo variable']
    lines += [' %s' % len(df_cvar_with_emissions['Central'].unique())]
    write_lines_from_scratch(lines, path_plpcosce)
    df = df_cvar_with_emissions[['Central', 'Month', 'Etapa',
                                 'Variable Cost + CO2 Tax USD/MWh']]
    for central in df['Central'].unique():
        # Filter and select columns
        df_aux = df[df['Central'] == central]
        df_aux = df_aux.drop(columns=['Central'])
        # Write lines to append
        lines = ['\n# Nombre de la central']
        lines += ["'%s'" % central]
        lines += ['# Numero de etapas']
        lines += ['   %s' % len(df_aux)]
        lines += ['# Mes   Etapa    CosVar']
        lines += [df_aux.to_string(
                  index=False, header=False, formatters=formatter_plpcosce)]
        write_lines_appending(lines, path_plpcosce)


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
        path_df = iplp_path.parent / "Temp" / "df"
        check_is_path(path_df)
        path_csv = iplp_path.parent / "Temp" / "CSV"
        check_is_path(path_csv)

        # Add destination folder to logger
        path_log = iplp_path.parent / "Temp" / "log"
        check_is_path(path_log)
        add_file_handler(logger, 'cvariable', path_log)

        # Get Hour-Blocks-Etapas definition
        logger.info('Processing block to etapas files')
        blo_eta, _, _ = process_etapas_blocks(path_dat)

        # Get Hour-Blocks-Etapas definition
        logger.info('Processing csv inputs')
        blo_eta, _, _ = process_etapas_blocks(path_dat)

        # Llenado Costo Variable - IM_to_CostoVariable
        # borrar datos
        logger.info('Reading fuel prices')
        df_fuel_prices = read_all_fuel_prices(iplp_path)

        # leer Rendimientos y mapeo central-combustible
        logger.info('Reading heatrate and fuel mapping')
        df_heatrate_unit_fuel_mapping =\
            read_heatrate_and_unit_fuel_mapping(iplp_path)

        # crear matriz de centrales - costos variables
        logger.info('Calculating base Variable Cost')
        df_cvar = calculate_cvar(path_df, blo_eta, df_fuel_prices,
                                 df_heatrate_unit_fuel_mapping)

        # leer mapeo central - factor de emisiones
        logger.info('Reading unit emissions mapping and carbon tax')
        df_unit_emissions = read_unit_emissions_mapping(iplp_path)
        df_year_co2_tax = read_year_co2_tax(iplp_path)

        # Validate unit emissions and co2_tax data
        bool_error_emissions = validate_unit_emissions(df_unit_emissions)
        bool_error_co2_tax = validate_year_co2_tax(df_year_co2_tax, blo_eta)

        # Sumar impuestos verdes
        logger.info('Adding CO2 tax to variable cost')
        df_cvar_with_emissions = add_emissions(
            path_df, df_cvar, df_unit_emissions, df_year_co2_tax)

        # Validate final data
        logger.info('Validating final cvar data')
        bool_error_cvar = validate_df_cvar_with_emissions(
            df_cvar_with_emissions)

        # escribir en formato .dat
        logger.info('Printing plpcosce.dat')
        print_plpcosce(path_inputs, df_cvar_with_emissions)

        if bool_error_emissions or bool_error_co2_tax or bool_error_cvar:
            logger.error('Process finished with errors. Check log.')
        else:
            logger.info('Process finished successfully')
    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')


if __name__ == "__main__":
    main()
