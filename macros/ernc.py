from pathlib import Path

from utils import get_project_root, timeit, process_etapas_blocks, input_iplp_path
from macros.read_write import (read_ernc_files,
                               write_dat_file,
                               generate_max_capacity_csv,
                               generate_rating_factor_csv,
                               generate_profiles_csv)
from macros.shape_data import (get_profiles_blo,
                               get_all_profiles,
                               get_rating_factors,
                               get_scaled_profiles)

root = get_project_root()
path_inputs = Path(root, 'macros', 'inputs')
path_dat = Path(root, 'macros', 'inputs', 'Dat')


@timeit
def main():
    '''
    Main routine
    '''
    # Generate csv files
    iplp_path = input_iplp_path()

    generate_max_capacity_csv(iplp_path, path_inputs)
    generate_rating_factor_csv(iplp_path, path_inputs)
    generate_profiles_csv(iplp_path, path_inputs)

    # Get inputs
    ernc_data = read_ernc_files(path_inputs)
    blo_eta, _, block2day = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)

    # Convert hourly profiles to blocks
    profiles_dict = get_profiles_blo(ernc_data, block2day)
    # Replicate data for all Etapas
    df_all_profiles = get_all_profiles(blo_eta, profiles_dict)

    # Get Rating Factors
    df_rf = get_rating_factors(ernc_data, blo_eta)

    # Use RFs to scale profiles
    df_scaled_profiles = get_scaled_profiles(ernc_data, df_all_profiles, df_rf)

    # Write data in .dat format
    write_dat_file(ernc_data, df_scaled_profiles)


if __name__ == "__main__":
    main()

