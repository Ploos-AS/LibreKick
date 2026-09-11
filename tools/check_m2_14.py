#!/usr/bin/env python3
from pathlib import Path
import struct, sys
ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008; EXEC_BASE=0x00003400
MEMHDR=0x4800; FAST_HDR=0x4A00; DYN_SLOT=0x4C00; FAST_BASE=0x7000; DYN_BASE=0x9000; DYN_PAYLOAD=0x9020
MARKER_OFF=0x1A00; IDENT_OFF=0x1A80
MARKER=b'LIBREKICK-M2.14\0EXEC-DYNAMIC-ALLOC-FREE\0'
IDENT=b'exec.library\0LibreKick M2.14 dynamic AllocMem FreeMem slice 40.14\0'
def ones(t,v): t+=v; return (t&0xffffffff)+(t>>32)
if len(sys.argv)!=2: raise SystemExit('usage: check_m2_14.py ROM')
p=Path(sys.argv[1]); data=p.read_bytes(); assert len(data)==ROM_SIZE
assert struct.unpack_from('>II',data,0)==(SP,PC)
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)]==MARKER
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)]==IDENT
boot=data[8:0x0B00]
assert bytes.fromhex('13FC000300BFE201') in boot
assert bytes.fromhex('08B9000000BFE001') in boot
assert bytes.fromhex('33FC026A00003410') in boot or struct.pack('>H',618) in boot
for lvo,off in ((198,0x0B00),(210,0x0C00),(216,0x0D00),(618,0x1400)):
    assert struct.pack('>I',EXEC_BASE-lvo) in boot
    assert struct.pack('>H',(0x00F80000+off)&0xffff) in boot
# Runtime calls AddMemList, exhausts static FAST, then allocates from dynamic payload.
assert bytes.fromhex('4EAEFD96') in boot
assert boot.count(bytes.fromhex('4EAEFF3A'))>=2
assert boot.count(bytes.fromhex('4EAEFF2E'))>=2
for v in (FAST_BASE,DYN_BASE,DYN_PAYLOAD,0x1000,0x0FE0,0x0EE0): assert struct.pack('>I',v) in boot
# Alloc wrapper must call static FAST and dynamic cores and inspect the registration slot.
alloc=data[0x0B00:0x0C00]
for target in (0x00F81000,0x00F81600): assert bytes.fromhex('4EB9')+struct.pack('>I',target) in alloc
assert struct.pack('>I',DYN_SLOT) in alloc
assert bytes.fromhex('08020002') in alloc
# Free wrapper must route to dynamic free core.
free=data[0x0C00:0x0D00]
assert struct.pack('>I',DYN_PAYLOAD) in free
assert bytes.fromhex('4EB9')+struct.pack('>I',0x00F81700) in free
# Relocated dynamic cores must touch dynamic mh_First/mh_Free.
for off in (0x1600,0x1700):
    code=data[off:off+0x100]
    assert struct.pack('>I',DYN_BASE+16) in code
    assert struct.pack('>I',DYN_BASE+28) in code
assert bytes.fromhex('33FC00F000DFF180') in boot
assert bytes.fromhex('33FC000F00DFF180') in boot
t=0
for o in range(0,ROM_SIZE,4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32); assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.14 check PASS: {p} ({len(data)} bytes)')
print('Exec dynamic AllocMem fallback + FreeMem routing after AddMemList; checksum=0xffffffff')
