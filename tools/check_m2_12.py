#!/usr/bin/env python3
from pathlib import Path
import struct, sys
ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008; EXEC_BASE=0x00003400
MEMHDR=0x00004800; FAST_HDR=0x00004A00; MEM_BASE=0x00005000; FAST_BASE=0x00007000
MEM_SIZE=FAST_SIZE=0x1000; MARKER_OFF=0x1600; IDENT_OFF=0x1680
MARKER=b'LIBREKICK-M2.12\0EXEC-AVAILMEM-LARGEST\0'
IDENT=b'exec.library\0LibreKick M2.12 AvailMem MEMF_LARGEST slice 40.12\0'
def ones(t,v): t+=v; return (t&0xffffffff)+(t>>32)
if len(sys.argv)!=2: raise SystemExit('usage: check_m2_12.py ROM')
p=Path(sys.argv[1]); data=p.read_bytes(); assert len(data)==ROM_SIZE
assert struct.unpack_from('>II',data,0)==(SP,PC)
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)]==MARKER
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)]==IDENT
boot=data[8:0x0B00]
assert bytes.fromhex('13FC000300BFE201') in boot
assert bytes.fromhex('08B9000000BFE001') in boot
assert bytes.fromhex('33FC002800003414') in boot
assert bytes.fromhex('33FC000C00003416') in boot
for lvo,off in ((198,0x0B00),(210,0x0C00),(216,0x0D00)):
    assert struct.pack('>I',EXEC_BASE-lvo) in boot
    assert struct.pack('>H',(0x00F80000+off)&0xffff) in boot
# Both logical region initializations retained.
for addr,val in ((MEMHDR+16,MEM_BASE),(MEMHDR+20,MEM_BASE),(MEMHDR+24,MEM_BASE+MEM_SIZE),(MEMHDR+28,MEM_SIZE),
                 (FAST_HDR+16,FAST_BASE),(FAST_HDR+20,FAST_BASE),(FAST_HDR+24,FAST_BASE+FAST_SIZE),(FAST_HDR+28,FAST_SIZE)):
    assert struct.pack('>I',addr) in boot and struct.pack('>I',val) in boot
# AvailMem wrapper recognizes MEMF_LARGEST and calls both region scanners.
avail=data[0x0D00:0x0E00]
assert bytes.fromhex('08010011') in avail, 'missing MEMF_LARGEST bit test'
for target in (0x00F81200,0x00F81300):
    assert bytes.fromhex('4EB9')+struct.pack('>I',target) in avail, 'missing largest helper call'
assert struct.pack('>I',MEMHDR+28) in avail and struct.pack('>I',FAST_HDR+28) in avail
# Each scanner walks mc_Next and compares mc_Bytes to a running maximum.
for off,hdr in ((0x1200,MEMHDR),(0x1300,FAST_HDR)):
    code=data[off:off+0x100]
    assert struct.pack('>I',hdr+16) in code
    assert bytes.fromhex('24280004') in code, 'missing mc_Bytes read'
    assert bytes.fromhex('B082') in code, 'missing largest comparison'
    assert bytes.fromhex('2050') in code, 'missing mc_Next traversal'
# Probe must distinguish total free from largest free under fragmentation.
for v in (0x0E00,0x0D00,0x1E00,0x0C00,0x1A00): assert struct.pack('>I',v) in boot
assert boot.count(bytes.fromhex('4EAEFF28'))>=14, 'insufficient AvailMem coverage'
assert boot.count(bytes.fromhex('4EAEFF3A'))>=4
assert boot.count(bytes.fromhex('4EAEFF2E'))>=4
assert bytes.fromhex('33FC00F000DFF180') in boot
assert bytes.fromhex('33FC000F00DFF180') in boot
# 68000 regression guard: no address-register TST encodings in new scanners.
assert bytes.fromhex('4A88') not in data[0x1200:0x1400]
t=0
for o in range(0,ROM_SIZE,4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32); assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.12 check PASS: {p} ({len(data)} bytes)')
print('Exec AvailMem total-free + MEMF_LARGEST across CHIP/FAST regions; checksum=0xffffffff')
