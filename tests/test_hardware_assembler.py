from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from assembler import assemble,AssemblyError


class HardwareAssemblerTests(unittest.TestCase):
    def test_exact_encoding_of_supported_extensions(self):
        self.assertEqual(assemble('slli x3, x4, 5',isa='shifter'),[0x00521193])
        self.assertEqual(assemble('srli x3, x4, 1',isa='shifter'),[0x00125193])
        self.assertEqual(assemble('qcap x3, x4, x5',isa='qcap'),[0x0052018b])

    def test_extensions_do_not_leak_into_baseline_or_each_other(self):
        for isa,source in [('base','slli x3, x4, 5'),('base','qcap x3, x4, x5'),('shifter','qcap x3, x4, x5'),('qcap','srli x3, x4, 1')]:
            with self.assertRaises(AssemblyError):assemble(source,isa=isa)

    def test_unsupported_shift_and_registers_rejected(self):
        for source in ['slli x3, x4, 2','srli x3, x4, 5','srai x3, x4, 1','sll x3, x4, x5','slli x16, x4, 1']:
            with self.assertRaises(AssemblyError):assemble(source,isa='shifter')


if __name__=='__main__':unittest.main()
