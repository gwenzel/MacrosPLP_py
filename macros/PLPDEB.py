'''
PLPDEB

This script creates the PLPDEB.dat file
'''

from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path)
from utils.logger import add_file_handler, create_logger
from pathlib import Path


logger = create_logger('PLPDEB')


def create_plpdeb_file(iplp_file: Path, path_inputs: Path):
    """Creates a plpdeb.dat file with specified parameters."""

    # Set initial values for parameters
    f_log = "T"
    pri_prog_din = "T"
    pd_sv_fl = "F"
    er_sv_fl = "T"
    fsv_la_ps = "F"
    ps_fz_fl = "T"
    ind_sim_imp = "00"
    ind_ite_imp = "00"
    ind_eta1_imp = "0"
    ind_eta2_imp = "0"

    # Write the plpdeb.dat file
    with open(path_inputs / "plpdeb.dat", "w") as f:
        f.write("# Archivo con parametros de Debug (plpdeb.dat)\n")
        f.write("# FLogFile\n")
        f.write(f"{' ' * 9}{f_log}\n")
        f.write("# PriProgDin PDSvFl PMSvFl FDatChe ErSvFl PsFzFl FTSvFl FSvLaPs\n")
        f.write(f"{' ' * 11}{pri_prog_din}{' ' * 6}{pd_sv_fl}{' ' * 6}F{' ' * 7}F{' ' * 6}{er_sv_fl}{' ' * 6}{ps_fz_fl}{' ' * 6}F{' ' * 7}{fsv_la_ps}\n")
        f.write("# IndSimImp  IndIteImp  FBest  IndEta1Imp  IndEta2Imp\n")
        f.write(f"{' ' * 9}{ind_sim_imp.zfill(2)}{' ' * 9}{ind_ite_imp.zfill(2)}{' ' * 6}F{' ' * 11}{ind_eta1_imp.zfill(1)}{' ' * 11}{ind_eta2_imp.zfill(1)}\n")


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
        add_file_handler(logger, 'plpmat', path_log)

        logger.info('Printing PLPDEB.dat')
        create_plpdeb_file(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
