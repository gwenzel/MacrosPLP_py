'''ERNC

Module to generate renewable energy profiles in PLP format,
modifying plpmance.dat file, which stores the maintenance of
generation units
'''
from utils.utils import (timeit,
                         process_etapas_blocks,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         create_logger,
                         get_scenarios)
from macros.ernc_read_write import (read_ernc_files,
                                    write_plpmance_ernc_dat,
                                    generate_max_capacity_csv,
                                    generate_min_capacity_csv,
                                    generate_rating_factor_csv,
                                    generate_profiles_csv,
                                    get_valid_unit_names,
                                    define_input_names)
from macros.ernc_shape_data import (get_profiles_blo,
                                    get_all_profiles,
                                    get_rating_factors,
                                    get_scaled_profiles)

logger = create_logger('ernc')


def get_input_paths():
    logger.info('Getting input file path')
    parser = define_arg_parser(ext=True)
    iplp_path = get_iplp_input_path(parser)
    path_inputs = iplp_path.parent / "Temp"
    check_is_path(path_inputs)
    path_dat = iplp_path.parent / "Temp" / "Dat"
    check_is_path(path_dat)
    return iplp_path, path_inputs, path_dat


def get_input_names(iplp_path):
    logger.info('Getting scenarios and input names')
    scenario_data = get_scenarios(iplp_path)
    ernc_scenario = scenario_data['Eolico']
    input_names = define_input_names(ernc_scenario)
    return input_names


def generate_csv_files(iplp_path, path_inputs, input_names):
    logger.info('Generating input csv files')
    generate_max_capacity_csv(iplp_path, path_inputs, input_names)
    generate_min_capacity_csv(iplp_path, path_inputs, input_names)
    generate_rating_factor_csv(iplp_path, path_inputs, input_names)
    generate_profiles_csv(iplp_path, path_inputs, input_names)


def get_inputs(iplp_path, path_inputs, path_dat, input_names):
    logger.info('Processing csv inputs')
    ernc_data = read_ernc_files(path_inputs, input_names)
    blo_eta, _, block2day = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)
    valid_unit_names = get_valid_unit_names(ernc_data, iplp_path)
    return ernc_data, blo_eta, block2day, valid_unit_names


def get_profiles_and_rating_factors(ernc_data, blo_eta, block2day):
    # Convert hourly profiles to blocks
    logger.info('Converting hourly profiles to blocks')
    profiles_dict = get_profiles_blo(ernc_data, block2day)

    # Replicate data for all Etapas
    logger.info('Getting all profiles')
    df_all_profiles = get_all_profiles(blo_eta, profiles_dict)

    # Get Rating Factors
    logger.info('Getting rating factors')
    df_rf = get_rating_factors(ernc_data, blo_eta)
    return df_all_profiles, df_rf


def scale_profiles(ernc_data, df_all_profiles, df_rf, valid_unit_names):
    logger.info('Using rating factors to scaled profiles')
    return get_scaled_profiles(
        ernc_data, df_all_profiles, df_rf, valid_unit_names)


def write_data(ernc_data, df_scaled_profiles, valid_unit_names, iplp_path):
    logger.info('Writing profiles in .dat format')
    write_plpmance_ernc_dat(
        ernc_data, df_scaled_profiles, valid_unit_names, iplp_path)


@timeit
def main():
    '''
    Main routine
    '''
    # Get input file path
    iplp_path, path_inputs, path_dat =\
        get_input_paths()

    # Get ERNC scenario and input file names
    input_names = get_input_names(iplp_path)

    # Generate csv files
    generate_csv_files(
        iplp_path, path_inputs, input_names)

    # Get inputs
    ernc_data, blo_eta, block2day, valid_unit_names =\
        get_inputs(iplp_path, path_inputs, path_dat, input_names)

    # Get profiles and rating factors
    df_all_profiles, df_rf = get_profiles_and_rating_factors(
        ernc_data, blo_eta, block2day)

    # Use RFs to scale profiles
    df_scaled_profiles = scale_profiles(
        ernc_data, df_all_profiles, df_rf, valid_unit_names)

    # Write data in .dat format
    write_data(
        ernc_data, df_scaled_profiles, valid_unit_names, iplp_path)

    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
