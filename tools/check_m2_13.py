#!/usr/bin/env python3
from pathlib import Path
import struct, sys
ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008; EXEC_BASE=0x00003400
MEMHDR=0x00004800; FAST_HDR=0x00004A00; MEM_BASE=0x00005000; FAST_BASE=0x00007000
DYN_SLOT=0x00004C00; DYN_BASE=0x00009000; DYN_SIZE=0x1000; DYN_PAYLOAD=DYN_BASE+32; DYN_FREE=DYN_SIZE-32
MARKER_OFF=0x1800; IDENT_OFF=0x1880
MARKER=b'LIBREKICK-M2.13\0EXEC-ADDMEMLIST-DYNAMIC\0'
IDENT=b'exec.library\0LibreKick M2.13 AddMemList dynamic-region slice 40.13\0'
def ones(t,v): t+=v; return (t&0xffffffff)+(t>>32)
if len(sys.argv)!=2: raise SystemExit('usage: check_m2_13.py ROM')
p=Path(sys.argv[1]); data=p.read_bytes(); assert len(data)==ROM_SIZE
assert struct.unpack_from('>II',data,0)==(SP,PC)
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)]==MARKER
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)]==IDENT
boot=data[8:0x0B00]
assert bytes.fromhex('13FC000300BFE201') in boot
assert bytes.fromhex('08B9000000BFE001') in boot
assert bytes.fromhex('33FC002800003414') in boot
assert bytes.fromhex('33FC026A00003410') in boot, 'negative library size does not cover AddMemList'
assert bytes.fromhex('33FC000D00003416') in boot, 'missing V40.13 header'
for lvo,off in ((198,0x0B00),(210,0x0C00),(216,0x0D00),(618,0x1400)):
    assert struct.pack('>I',EXEC_BASE-lvo) in boot, f'missing LVO -{lvo} slot'
    assert struct.pack('>H',(0x00F80000+off)&0xffff) in boot, f'missing LVO -{lvo} target'
# Runtime uses the public AddMemList ABI and exact -618 vector call.
assert bytes.fromhex('4EAEFD96') in boot, 'missing AddMemList(-618) runtime call'
for v in (DYN_SLOT,DYN_BASE,DYN_SIZE,DYN_PAYLOAD,DYN_FREE,DYN_BASE+DYN_SIZE):
    assert struct.pack('>I',v) in boot, f'missing dynamic-region probe constant {v:08x}'
# AddMemList body creates a MemHeader and one initial MemChunk.
add=data[0x1400:0x1500]
assert struct.pack('>I',DYN_SLOT) in add
assert bytes.fromhex('11420009') in add, 'missing ln_Pri write'
assert bytes.fromhex('2149000A') in add, 'missing ln_Name write'
assert bytes.fromhex('3141000E') in add, 'missing mh_Attributes write'
assert bytes.fromhex('45E80020') in add, 'missing base+MemHeader-size calculation'
assert bytes.fromhex('214A0010') in add and bytes.fromhex('214A0014') in add
assert bytes.fromhex('21440018') in add and bytes.fromhex('2143001C') in add
assert bytes.fromhex('4292') in add and bytes.fromhex('25430004') in add
# Public AvailMem wrapper delegates to M2.12 and adds dynamically registered mh_Free.
avail=data[0x0D00:0x0E00]
assert bytes.fromhex('4EB9')+struct.pack('>I',0x00F81500) in avail
assert struct.pack('>I',DYN_SLOT) in avail
assert bytes.fromhex('D0A8001C') in avail, 'missing dynamic mh_Free contribution'
assert bytes.fromhex('08010011') in avail, 'missing MEMF_LARGEST defer gate'
# Probe must demonstrate changed FAST/total accounting after registration.
for v in (0x1000,0x2000,0x0FE0,0x1FE0,0x2FE0):
    assert struct.pack('>I',v) in boot
assert boot.count(bytes.fromhex('4EAEFF28'))>=6
assert bytes.fromhex('33FC00F000DFF180') in boot
assert bytes.fromhex('33FC000F00DFF180') in boot
# 68000 regression guards.
assert bytes.fromhex('4A88') not in data[0x0D00:0x1600]
t=0
for o in range(0,ROM_SIZE,4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32); assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.13 check PASS: {p} ({len(data)} bytes)')
print('Exec AddMemList(-618) dynamic MemHeader creation + AvailMem total accounting; checksum=0xffffffff')
