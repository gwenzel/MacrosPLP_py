from utils import ( get_project_root,
                    get_iplp_input_path,
                    check_is_path,
                    create_logger
)
import pandas as pd

root = get_project_root()
logger = create_logger('mantcen')


def main():
    # LlenadoMantConvenc
    # Fill Mantcen with remaining mantcen
    # No cíclicos, cíclicos, restricciones de gas, genmin

    # Plpmance
    # Read Centrales and get PnomMax and PnomMin
    # Filter out if X, and count if F

    # Check sheet GxFalla to define tramos and Nfalla

    # Initialize array with Pnom

    # Check which units have maintenance, and validate their names

    # Update pmin/pmax data

    # translate to Etapas/Bloques

    # count Etapas with maintenance

    # write dat file

    # Write report in sheet (?)

    pass

if __name__ == "__main__":
    main()