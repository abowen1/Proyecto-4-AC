"""Contrato de las fuentes de entrega y sus variantes de ISA."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from assembler import assemble

class DeliveryM105225(unittest.TestCase):
    def test_official_trade_is_selected_optimized_software(self):
        official=assemble((ROOT/'sw/trade.s').read_text(),isa='base')
        selected=assemble((ROOT/'sw/trade_m105_225_soft.s').read_text(),isa='base')
        self.assertEqual(official,selected)

    def test_variants_fit_soc_and_use_their_own_isa(self):
        for suffix,isa in [('soft','base'),('shifter','shifter'),('qcap','qcap')]:
            with self.subTest(variant=suffix):
                words=assemble((ROOT/f'sw/trade_m105_225_{suffix}.s').read_text(),isa=isa)
                self.assertLessEqual(len(words),512)

if __name__=='__main__':unittest.main()
