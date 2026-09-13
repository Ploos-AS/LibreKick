#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.21\0EXEC-DYNAMIC-MEMCHUNK-TRAVERSAL\0' in data
assert b'exec.library\0LibreKick M2.21 dynamic MemChunk traversal slice 40.21\0' in data
# Dynamic allocator slot must contain linked MemChunk traversal and both head/non-head relinking paths.
dyn=data[0x1600:0x1800]
assert bytes.fromhex('22680010') in dyn, 'missing mh_First load'
assert bytes.fromhex('26492251') in dyn, 'missing prev/current MemChunk advance'
assert bytes.fromhex('268A') in dyn, 'missing prev.next relink'
assert bytes.fromhex('214A0010') in dyn, 'missing mh_First replacement'
assert bytes.fromhex('0C8300000008') in dyn, 'missing whole-chunk threshold'
# Runtime probe must contain the fragmented-list allocation that skips a too-small first chunk.
boot=data[8:0x0B00]
for value in (0x100,0x180):
    assert bytes.fromhex('203C')+struct.pack('>I',value) in boot
assert struct.pack('>I',0x00009020) in boot
assert struct.pack('>I',0x00009220) in boot
assert struct.pack('>I',0x000093A0) in boot
assert bytes.fromhex('33FC00F000DFF180') in boot
assert bytes.fromhex('33FC000F00DFF18060FE') in boot
# Kickstart checksum must still be all ones.
def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.21 check PASS: {p} ({len(data)} bytes)')
print('Exec dynamic AllocMem first-fit MemChunk traversal; checksum=0xffffffff')
