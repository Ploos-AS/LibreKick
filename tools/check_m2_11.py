#!/usr/bin/env python3
from pathlib import Path
import struct, sys
ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008; EXEC_BASE=0x00003400
MEMHDR=0x00004800; FAST_HDR=0x00004A00; MEM_BASE=0x00005000; FAST_BASE=0x00007000
MEM_SIZE=FAST_SIZE=0x1000; MARKER_OFF=0x1600; IDENT_OFF=0x1680
MARKER=b'LIBREKICK-M2.11\0EXEC-MULTI-MEMHEADER-CHIP-FAST\0'
IDENT=b'exec.library\0LibreKick M2.11 CHIP/FAST multi-MemHeader slice 40.11\0'
def ones(t,v): t+=v; return (t&0xffffffff)+(t>>32)
if len(sys.argv)!=2: raise SystemExit('usage: check_m2_11.py ROM')
p=Path(sys.argv[1]); data=p.read_bytes(); assert len(data)==ROM_SIZE
assert struct.unpack_from('>II',data,0)==(SP,PC)
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)]==MARKER
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)]==IDENT
boot=data[8:0x0B00]
assert bytes.fromhex('13FC000300BFE201') in boot
assert bytes.fromhex('08B9000000BFE001') in boot
assert bytes.fromhex('33FC002800003414') in boot
assert bytes.fromhex('33FC000B00003416'.replace(' ','')) in boot
for lvo,off in ((198,0x0B00),(210,0x0C00),(216,0x0D00)):
    assert struct.pack('>I',EXEC_BASE-lvo) in boot
    assert struct.pack('>H',(0x00F80000+off)&0xffff) in boot
# Both logical MemHeaders and their attributes/regions must be initialized.
# Header addresses themselves are not necessarily emitted as literal immediates;
# verify the canonical field writes and region bounds instead.
assert bytes.fromhex('33FC00020000480E') in boot, 'missing CHIP MemHeader attribute'
assert bytes.fromhex('33FC000400004A0E') in boot, 'missing FAST MemHeader attribute'
for addr,val in (
    (MEMHDR+16,MEM_BASE),(MEMHDR+20,MEM_BASE),(MEMHDR+24,MEM_BASE+MEM_SIZE),(MEMHDR+28,MEM_SIZE),
    (FAST_HDR+16,FAST_BASE),(FAST_HDR+20,FAST_BASE),(FAST_HDR+24,FAST_BASE+FAST_SIZE),(FAST_HDR+28,FAST_SIZE),
):
    assert struct.pack('>I',addr) in boot, f'missing MemHeader field address {addr:08x}'
    assert struct.pack('>I',val) in boot, f'missing MemHeader field value {val:08x}'
# Wrapper must dispatch to distinct CHIP/FAST cores and preserve CLEAR support.
alloc=data[0x0B00:0x0C00]
for target in (0x00F80E00,0x00F81000): assert bytes.fromhex('4EB9')+struct.pack('>I',target) in alloc
assert bytes.fromhex('08030010') in alloc, 'missing MEMF_CLEAR test'
free=data[0x0C00:0x0D00]
for target in (0x00F80F00,0x00F81100): assert bytes.fromhex('4EB9')+struct.pack('>I',target) in free
avail=data[0x0D00:0x0E00]
assert struct.pack('>I',MEMHDR+28) in avail and struct.pack('>I',FAST_HDR+28) in avail
# Relocated FAST cores must reference FAST mh_First/mh_Free rather than CHIP fields.
fast_alloc=data[0x1000:0x1100]; fast_free=data[0x1100:0x1600]
assert struct.pack('>I',FAST_HDR+16) in fast_alloc and struct.pack('>I',FAST_HDR+28) in fast_alloc
assert struct.pack('>I',FAST_HDR+16) in fast_free and struct.pack('>I',FAST_HDR+28) in fast_free
# Runtime probe includes CHIP, FAST, total, CLEAR and conflicting requirements.
assert boot.count(bytes.fromhex('4EAEFF3A'))>=4
assert boot.count(bytes.fromhex('4EAEFF2E'))>=3
assert boot.count(bytes.fromhex('4EAEFF28'))>=8
assert bytes.fromhex('33FC00F000DFF180') in boot
assert bytes.fromhex('33FC000F00DFF180') in boot
t=0
for o in range(0,ROM_SIZE,4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32); assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.11 check PASS: {p} ({len(data)} bytes)')
print('Exec two-region CHIP/FAST MemHeader routing + CLEAR + AvailMem filtering; checksum=0xffffffff')
