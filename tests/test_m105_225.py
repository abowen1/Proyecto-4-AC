"""Casos con resultado calculado independientemente de la implementacion Espino."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from m105_225 import simulate
from assembler import assemble

class TestM105225(unittest.TestCase):
    def test_delayed_fills_commissions_latched_sale(self):
        summary,rows,policy=simulate([105,100,100,225,224,200])
        self.assertEqual([(r['cash'],r['shares']) for r in rows],[(10000,0),(3695,63),(90,99),(90,99),(14197,36),(21392,0)])
        self.assertEqual([r['next_decision'] for r in rows],[127,100,0,191,164,0])
        self.assertEqual(summary['orders'],4)
        self.assertEqual(summary['commissions'],20)
        self.assertEqual(policy.closed[0]['net_profit'],11392)
        self.assertEqual(rows[4]['state'],'selling')

    def test_entry_threshold_and_abandoned_accumulation(self):
        _,rows,_=simulate([106,105,110,100,100,224,225])
        self.assertEqual(rows[0]['next_decision'],0)
        self.assertEqual(rows[1]['next_decision'],127)
        self.assertEqual(rows[2]['shares'],63)
        self.assertTrue(all(r['next_decision']==0 for r in rows[2:6]))
        self.assertEqual(rows[6]['next_decision'],191)

    def test_no_forced_end_sale_or_execution(self):
        summary,rows,_=simulate([105])
        self.assertEqual(summary['equity'],10000)
        self.assertEqual(summary['orders'],0)
        self.assertEqual(rows[-1]['next_decision'],127)
        summary,rows,_=simulate([100]*3)
        self.assertEqual((summary['equity'],summary['cash'],summary['shares']),(9990,90,99))

    def test_reentry_after_flat(self):
        _,rows,policy=simulate([100]*3+[225]*3+[100]*3)
        self.assertEqual(len(policy.closed),1)
        self.assertEqual(rows[5]['shares'],0)
        self.assertEqual(rows[6]['next_decision'],127)
        self.assertGreater(rows[7]['shares'],0)

    def test_prefixes_do_not_depend_on_future(self):
        prices=[106,105,255,104,100,224,225,1,1,1,225,100]*5
        _,full,_=simulate(prices)
        for size in range(1,len(prices)+1):
            _,prefix,_=simulate(prices[:size])
            self.assertEqual(prefix,full[:size])

    def test_base_isa_program_fits_ram(self):
        source=(Path(__file__).resolve().parents[1]/'sw/trade_m105_225.s').read_text()
        words=assemble(source,isa='base')
        self.assertLessEqual(len(words),512)

if __name__=='__main__':unittest.main()
