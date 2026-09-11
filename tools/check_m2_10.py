#!/usr/bin/env python3
from pathlib import Path
import struct, sys
ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008; EXEC_BASE=0x00003400
MEMHDR=0x00004800; MEM_BASE=0x00005000; MEM_SIZE=0x1000
MARKER_OFF=0x1600; IDENT_OFF=0x1680
MARKER=b'LIBREKICK-M2.10\0EXEC-MEMF-CLEAR-REQUIREMENTS\0'
IDENT=b'exec.library\0LibreKick M2.10 MEMF_CLEAR and requirement filter slice 40.10\0'
def ones(t,v): t+=v; return (t&0xffffffff)+(t>>32)
if len(sys.argv)!=2: raise SystemExit('usage: check_m2_10.py ROM')
p=Path(sys.argv[1]); data=p.read_bytes(); assert len(data)==ROM_SIZE
assert struct.unpack_from('>II',data,0)==(SP,PC)
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)]==MARKER
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)]==IDENT
boot=data[8:0x0B00]
assert bytes.fromhex('13FC000300BFE201') in boot
assert bytes.fromhex('08B9000000BFE001') in boot
assert bytes.fromhex('23FC0000340000000004') in boot
assert bytes.fromhex('33FC002800003414') in boot
assert bytes.fromhex('33FC000A00003416') in boot
for lvo,off in ((198,0x0B00),(210,0x0C00),(216,0x0D00)):
    slot=EXEC_BASE-lvo; target=0x00F80000+off
    assert struct.pack('>I',slot) in boot, f'missing LVO -{lvo}'
    assert struct.pack('>H',target&0xffff) in boot, f'missing LVO target -{lvo}'
# FAST reject + CHIP|CLEAR request are explicit runtime probes.
assert bytes.fromhex('223C00000004') in boot, 'missing MEMF_FAST probe'
assert bytes.fromhex('223C00010002') in boot, 'missing MEMF_CHIP|MEMF_CLEAR probe'
# Wrapper must test FAST and CLEAR bits and clear longwords.
wrap=data[0x0B00:0x0C00]
assert bytes.fromhex('08030002') in wrap, 'missing MEMF_FAST test'
assert bytes.fromhex('08030010') in wrap, 'missing MEMF_CLEAR test'
assert bytes.fromhex('4298') in wrap, 'missing clr.l clear loop'
assert bytes.fromhex('4EB900F80E00') in wrap, 'missing first-fit core call'
# Core retains M2.9 traversal behavior.
core=data[0x0E00:0x1600]
assert bytes.fromhex('26482050') in core, 'missing first-fit traversal'
assert bytes.fromhex('268A') in core, 'missing non-head relink'
assert bytes.fromhex('33FC00F000DFF180') in boot, 'missing green PASS marker'
assert bytes.fromhex('33FC000F00DFF180') in boot, 'missing blue FAIL marker'
t=0
for o in range(0,ROM_SIZE,4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32); assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.10 check PASS: {p} ({len(data)} bytes)')
print('Exec MEMF_FAST filtering + MEMF_CLEAR zeroing; checksum=0xffffffff')
