'''Demanda

Module to generate demand input files for PLP.

Ouput files are:

- plpdem.dat: Demand per Etapa for each node
- uni_plpdem.dat: Demand per Etapa for the uninodal case
- plpfal.prn: Define maximum power for each Failure Unit,
              based on the max demand of each node
'''

from utils import (     get_project_root,
                        get_iplp_input_path,
                        check_is_path
)

root = get_project_root()


def main():
    '''
    Main routine
    '''
    # Get input file path
    iplp_path = get_iplp_input_path()
    #path_inputs = iplp_path.parent / "Temp"
    #check_is_path(path_inputs)
    #path_dat = iplp_path.parent / "Temp" / "Dat"
    #check_is_path(path_dat)

    # Get Hour-Blocks-Etapas definition


    # Sheet "DdaPorBarra" to row format


    # Get mappings


    # Get monthly demand from Sheet "DdaEnergia"


    # Get hourly profiles from Sheet "PerfilesDDA"


    # Generate dataframe with profiles per Etapa


    # Print to plpdem and uni_plpdem


    # Get failure units and generate plpfal.prn



if __name__ == "__main__":
    main()
