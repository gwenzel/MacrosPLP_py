import pandas as pd
from pathlib import Path

from utils import get_project_root
from postpro.Filtro_PLP_Windows import process_etapas_blocks


MAX_CAPACITY_FILENAME = "ernc_MaxCapacity.csv"
RATING_FACTOR_FILENAME = "ernc_RatingFactor.csv"
H_PROFILES_FILENAME = "ernc_profiles_H.csv"
HM_PROFILES_FILENAME = "ernc_profiles_HM"
M_PROFILES_FILENAME = "ernc_profiles_M.csv"


'''
    'escribir encabezados por central
    Print #FileOut, "# Nombre de la central"
    Print #FileOut, "'" & nom_cen(1, C) & "'"
    Print #FileOut, "#   Numero de Etapas e Intervalos"
    Print #FileOut, "    " & NBlo & "                 01"
    Print #FileOut, "#   Mes    Etapa  NIntPot   PotMin   PotMax"
'''

root = get_project_root()

path_dat = Path(root, 'macros', 'inputs', 'Dat')
blo_eta, _ = process_etapas_blocks(path_dat)

# print(blo_eta)


