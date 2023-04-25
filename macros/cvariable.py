from utils import ( get_project_root,
                    get_iplp_input_path,
                    check_is_path,
                    create_logger,
                    process_etapas_blocks
)
import pandas as pd

root = get_project_root()
logger = create_logger('cvariable')


def main():
    # Get input file path
    logger.info('Getting input file path')
    iplp_path = get_iplp_input_path()
    path_inputs = iplp_path.parent / "Temp"
    check_is_path(path_inputs)
    path_dat = iplp_path.parent / "Temp" / "Dat"
    check_is_path(path_dat)

    # Get Hour-Blocks-Etapas definition
    logger.info('Processing block to etapas files')
    blo_eta, _, _ = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)

if __name__ == "__main__":
    main()