import unittest
import os

from pathlib import Path
from postpro.utils import get_project_root
from postpro.Filtro_PLP_Windows import process_etapas_blocks


root = get_project_root()

class Test_Filtro_PLP_Windows(unittest.TestCase):

    def test_process_etapas_blocks(self):
        path_dat = Path(root, 'postpro', 'test', 'Dat')
        blo_eta, tasa = process_etapas_blocks(path_dat)
        print(blo_eta)
        print(tasa)
        import pdb; pdb.set_trace()