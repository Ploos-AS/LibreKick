#!/usr/bin/env python3
from pathlib import Path
import struct, sys
ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008; EXEC_BASE=0x00003000
MARKER_OFF=0x1200; IDENT_OFF=0x1280
MARKER=b'LIBREKICK-M2.6\0EXEC-ALLOCMEM-FREEMEM\0'
IDENT=b'exec.library\0LibreKick M2.6 deterministic memory slice 40.6\0'
def ones(t,v): t+=v; return (t&0xffffffff)+(t>>32)
if len(sys.argv)!=2: raise SystemExit('usage: check_m2_6.py ROM')
p=Path(sys.argv[1]); data=p.read_bytes(); assert len(data)==ROM_SIZE
assert struct.unpack_from('>II',data,0)==(SP,PC)
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)]==MARKER
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)]==IDENT
boot=data[8:0x800]
assert bytes.fromhex('13FC000300BFE201') in boot
assert bytes.fromhex('08B9000000BFE001') in boot
assert bytes.fromhex('23FC0000300000000004') in boot
assert bytes.fromhex('33FC002800003014') in boot
assert bytes.fromhex('33FC000600003016') in boot
for lvo,off in ((198,0x0B00),(210,0x0B80)):
    slot=EXEC_BASE-lvo; target=0x00F80000+off
    assert struct.pack('>I',slot) in boot, f'missing LVO -{lvo} slot'
    assert struct.pack('>H',target&0xffff) in boot, f'missing LVO -{lvo} target'
assert boot.count(bytes.fromhex('4EAEFF3A'))==4, 'expected four AllocMem calls'
assert boot.count(bytes.fromhex('4EAEFF2E'))==1, 'expected one FreeMem call'
assert bytes.fromhex('33FC00F000DFF180') in boot, 'missing green PASS marker'
assert bytes.fromhex('33FC000F00DFF180') in boot, 'missing blue FAIL marker'
assert data[0x0B00:0x0B02]==bytes.fromhex('4A80')
assert data[0x0B80:0x0B82]==bytes.fromhex('2209')
t=0
for o in range(0,ROM_SIZE,4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32); assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.6 check PASS: {p} ({len(data)} bytes)')
print('Exec AllocMem(-198)/FreeMem(-210); deterministic 2x256-byte pool; checksum=0xffffffff')
