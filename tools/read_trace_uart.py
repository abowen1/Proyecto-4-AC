"""Read-only capture of Go Board debug UART packets; does not send data."""
import argparse
from collections import Counter
import json
import time
import serial

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port',default='/dev/cu.usbserial-1101')
parser.add_argument('--baud',type=int,action='append')
args=parser.parse_args()
for baud in args.baud or [115200]:
    port=serial.Serial(port=None,baudrate=baud,timeout=.15)
    port.dtr=False;port.rts=False;port.port=args.port;port.open()
    port.reset_input_buffer();data=b'';deadline=time.monotonic()+.8
    while time.monotonic()<deadline:data+=port.read(512)
    port.close()
    magic=bytes.fromhex('55aa1234')
    packets=Counter(data[i+4:i+8].hex() for i in range(len(data)-11) if data[i:i+4]==magic and data[i+8:i+12]==magic)
    print(json.dumps(dict(baud=baud,bytes=len(data),head=data[:64].hex(),packets=packets.most_common(4))),flush=True)
