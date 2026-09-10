#!/usr/bin/env python3
from pathlib import Path
import struct, sys
ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008; EXEC_BASE=0x00003400
MEMHDR=0x00004800; MEM_BASE=0x00005000; MEM_SIZE=0x1000
MARKER_OFF=0x1600; IDENT_OFF=0x1680
MARKER=b'LIBREKICK-M2.8\0EXEC-SORTED-FREELIST-COALESCE\0'
IDENT=b'exec.library\0LibreKick M2.8 sorted free-list allocator slice 40.8\0'
def ones(t,v): t+=v; return (t&0xffffffff)+(t>>32)
if len(sys.argv)!=2: raise SystemExit('usage: check_m2_8.py ROM')
p=Path(sys.argv[1]); data=p.read_bytes(); assert len(data)==ROM_SIZE
assert struct.unpack_from('>II',data,0)==(SP,PC)
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)]==MARKER
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)]==IDENT
boot=data[8:0x0B00]
assert bytes.fromhex('13FC000300BFE201') in boot
assert bytes.fromhex('08B9000000BFE001') in boot
assert bytes.fromhex('23FC0000340000000004') in boot
assert bytes.fromhex('33FC002800003414') in boot
assert bytes.fromhex('33FC000800003416') in boot
for lvo,off in ((198,0x0B00),(210,0x0C00),(216,0x0D00)):
    slot=EXEC_BASE-lvo; target=0x00F80000+off
    assert struct.pack('>I',slot) in boot, f'missing LVO -{lvo} slot'
    assert struct.pack('>H',target&0xffff) in boot, f'missing LVO -{lvo} target'
# Canonical one-region MemHeader initialization.
assert struct.pack('>I',MEM_BASE) in boot
assert struct.pack('>I',MEM_BASE+MEM_SIZE) in boot
assert struct.pack('>I',MEM_SIZE) in boot
# Three initial allocations plus one reuse; four frees including arbitrary order A,C,B.
assert boot.count(bytes.fromhex('4EAEFF3A'))==4, 'expected four AllocMem calls'
assert boot.count(bytes.fromhex('4EAEFF2E'))==4, 'expected four FreeMem calls'
assert boot.count(bytes.fromhex('4EAEFF28'))==2, 'expected two AvailMem calls'
# Runtime must assert two-fragment shape before final bidirectional coalesce.
assert struct.pack('>I',MEM_BASE+0x1c0) in boot
assert struct.pack('>I',MEM_BASE+0x180) in boot
assert struct.pack('>I',MEM_SIZE-0x180) in boot
# FreeMem body: sorted traversal and both merge paths are present.
free=data[0x0C00:0x0D00]
assert bytes.fromhex('26482050') in free, 'missing sorted-list traversal'
assert bytes.fromhex('D3A90004') in free, 'missing successor coalesce'
assert bytes.fromhex('D3AB0004') in free, 'missing predecessor coalesce'
assert bytes.fromhex('2689') in free, 'missing predecessor link insertion'
# Regression guards: 68000 word branches and no address-register TST encodings.
assert bytes.fromhex('4A89') not in free and bytes.fromhex('4A8B') not in free
assert bytes.fromhex('33FC00F000DFF180') in boot, 'missing green PASS marker'
assert bytes.fromhex('33FC000F00DFF180') in boot, 'missing blue FAIL marker'
t=0
for o in range(0,ROM_SIZE,4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32); assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.8 check PASS: {p} ({len(data)} bytes)')
print('Exec sorted FreeMem free-list + successor/predecessor coalescing; checksum=0xffffffff')
