import unittest
import pytest
from pathlib import Path
from utils.utils import get_project_root, process_etapas_blocks

root = get_project_root()


@pytest.mark.skip(reason="no way of currently testing this")
class Test_Filtro_PLP_Windows(unittest.TestCase):

    def test_process_etapas_blocks(self):
        path_dat = Path(root, 'postpro', 'test', 'Dat')
        blo_eta, _, _ = process_etapas_blocks(path_dat, droptasa=False)

        # Check tasa first month
        mask1 = blo_eta['Year'] == 2023
        mask2 = blo_eta['Month'] == 1
        tasa_val = blo_eta[mask1 & mask2]['Tasa'].mean()    
        self.assertEqual(tasa_val, 1.0)

        # Check tasa last month
        mask1 = blo_eta['Year'] == 2051
        mask2 = blo_eta['Month'] == 3
        tasa_val = blo_eta[mask1 & mask2]['Tasa'].mean()    
        self.assertEqual(round(tasa_val, 6), 14.651901)
