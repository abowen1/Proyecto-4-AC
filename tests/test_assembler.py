import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('assembler', ROOT / 'tools/assembler.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def sign(value, bits):
    return value - (1 << bits) if value & (1 << (bits-1)) else value


class AssemblerTests(unittest.TestCase):
    def test_original_board_program(self):
        words = a.assemble((ROOT/'sw/buttons_leds.s').read_text())
        expected = (ROOT/'tests/fixtures/buttons_leds.hex').read_text()
        self.assertEqual(''.join(f'{w:08x}\n' for w in words), expected)

    def test_known_encodings(self):
        vectors = {
            'addi x1, x0, -1': 0xfff00093,
            'add x3, x1, x2': 0x002081b3,
            'sub x3, x1, x2': 0x402081b3,
            'lw x5, -4(x2)': 0xffc12283,
            'sw x5, -4(x2)': 0xfe512e23,
            'beq x1, x2, 8': 0x00208463,
            'jal x1, 8': 0x008000ef,
            'jalr x0, 0(x1)': 0x00008067,
            'auipc x1, 1': 0x00001097,
            'lui x2, 0x80000': 0x80000137,
        }
        for source, word in vectors.items():
            with self.subTest(source=source):
                self.assertEqual(a.assemble(source), [word])

    def test_every_alu_variant(self):
        for op, f3 in [('add',0),('sub',0),('slt',2),('sltu',3),('xor',4),('or',6),('and',7)]:
            w = a.assemble(f'{op} x15, x14, x13')[0]
            self.assertEqual((w & 127, (w>>7)&31, (w>>12)&7, (w>>15)&31, (w>>20)&31, w>>25),
                             (51,15,f3,14,13,32 if op=='sub' else 0))
        for op, f3 in [('addi',0),('slti',2),('sltiu',3),('xori',4),('ori',6),('andi',7)]:
            w = a.assemble(f'{op} x15, x14, -2048')[0]
            self.assertEqual((w&127,(w>>12)&7, sign(w>>20,12)),(19,f3,-2048))

    def test_branch_offsets(self):
        for op, f3 in [('beq',0),('bne',1),('blt',4),('bge',5),('bltu',6),('bgeu',7)]:
            for offset in [-4096,-2048,-4,0,4,2048,4092]:
                w = a.assemble(f'{op} x1, x2, {offset}')[0]
                recovered = ((w>>31)<<12) | (((w>>7)&1)<<11) | (((w>>25)&63)<<5) | (((w>>8)&15)<<1)
                self.assertEqual(sign(recovered,13),offset)
                self.assertEqual((w>>12)&7,f3)

    def test_jump_offsets(self):
        for offset in [-1048576,-4096,-4,0,4,2048,1048572]:
            w = a.assemble(f'jal x1, {offset}')[0]
            recovered = ((w>>31)<<20) | (((w>>12)&255)<<12) | (((w>>20)&1)<<11) | (((w>>21)&1023)<<1)
            self.assertEqual(sign(recovered,21),offset)

    def test_forward_and_backward_labels(self):
        words = a.assemble('.text\n.global start\nstart: beq x1,x2,end\naddi x1,x1,1\nend: jal x0,start')
        self.assertEqual(words,[0x00208463,0x00108093,0xff9ff06f])

    def test_signed_immediate_limits(self):
        for value in [-2048,-1,0,2047]:
            for source in [f'addi x1,x2,{value}',f'lw x1,{value}(x2)',f'jalr x1,{value}(x2)']:
                self.assertEqual(sign(a.assemble(source)[0]>>20,12),value)
            w = a.assemble(f'sw x1,{value}(x2)')[0]
            self.assertEqual(sign(((w>>25)<<5)|((w>>7)&31),12),value)

    def test_invalid_inputs(self):
        invalid = ['', 'addi x16,x0,1', 'addi x1,x0,2048', 'addi x1,x0,-2049',
                   'lui x1,0x100000','lui x1,-1','slli x1,x1,1','mul x1,x2,x3',
                   'beq x1,x2,missing','jal x0,2','beq x1,x2,4096',
                   'jal x0,1048576','a: add x1,x2,x3\na: add x1,x2,x3',
                   '.word 0', 'lw x1,x2','addi x1,x2', 'add x1,x2,x3,',
                   '.global missing\naddi x0,x0,0']
        for source in invalid:
            with self.subTest(source=source):
                with self.assertRaises(a.AssemblyError):
                    a.assemble(source)

    def test_ram_limit(self):
        self.assertEqual(len(a.assemble('addi x0,x0,0\n'*512)),512)
        with self.assertRaises(a.AssemblyError):
            a.assemble('addi x0,x0,0\n'*513)

    def test_cli_preserves_output_on_invalid_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder)/'bad.s', Path(folder)/'good.hex'
            source.write_text('addi x16,x0,1')
            output.write_text('previous\n')
            result = subprocess.run([sys.executable,str(ROOT/'tools/assembler.py'),str(source),'-o',str(output)],capture_output=True,text=True)
            self.assertEqual(result.returncode,1)
            self.assertIn('línea 1',result.stderr)
            self.assertEqual(output.read_text(),'previous\n')


if __name__ == '__main__':
    unittest.main()
