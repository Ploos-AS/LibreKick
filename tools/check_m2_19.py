#!/usr/bin/env python3
from pathlib import Path
import struct,sys

ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008
ROM_BASE=0x00F80000; ADDMEM_OFF=0x1400; BASE_AVAIL_OFF=0x1500
DYN_HEAD=0x4C00; ABASE=0x9000; BBASE=0xA000; CBASE=0xB000
MARKER=b'LIBREKICK-M2.19\0EXEC-PRIORITY-ADDMEMLIST\0'
IDENT=b'exec.library\0LibreKick M2.19 priority AddMemList slice 40.19\0'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)

def need(h,n,w):
    assert n in h, f'missing {w}'

p=Path(sys.argv[1]); data=p.read_bytes(); assert len(data)==ROM_SIZE
assert struct.unpack_from('>II',data,0)==(SP,PC)
need(data,MARKER,'M2.19 marker'); need(data,IDENT,'M2.19 ident')

add=data[ADDMEM_OFF:BASE_AVAIL_OFF]
need(add,bytes.fromhex('488548C5'),'signed extension of new ln_Pri')
need(add,bytes.fromhex('182A0009488448C4'),'signed extension of current ln_Pri')
need(add,bytes.fromhex('B8856D'),'signed priority compare/BLT insertion')
need(add,struct.pack('>I',DYN_HEAD),'dynamic head reference')
need(add,bytes.fromhex('288A294B0004'),'new successor/predecessor links')
need(add,bytes.fromhex('268C'),'previous successor update')
need(add,bytes.fromhex('254C0004'),'next predecessor update')

boot=data[8:0x0B00]
# Runtime gate must encode C(7)->A(5)->B(3) and consistent predecessor links.
for value,address,what in (
    (CBASE,DYN_HEAD,'head C'),(ABASE,CBASE,'C->A'),(0,CBASE+4,'C pred null'),
    (BBASE,ABASE,'A->B'),(CBASE,ABASE+4,'A pred C'),
    (0,BBASE,'B succ null'),(ABASE,BBASE+4,'B pred A'),
):
    need(boot,bytes.fromhex('0CB9')+struct.pack('>II',value,address),what)
need(boot,bytes.fromhex('33FC00F000DFF180'),'PASS color')
need(boot,bytes.fromhex('33FC000F00DFF180'),'FAIL color')

# M2.18 dynamic largest wrapper remains current and linked dynamic traversal is preserved.
av=data[0x0D00:0x0E00]
need(av,struct.pack('>I',DYN_HEAD),'M2.18 dynamic AvailMem traversal')

t=0
for off in range(0,ROM_SIZE,4): t=ones(t,struct.unpack_from('>I',data,off)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.19 check PASS: {p} ({len(data)} bytes)')
print('Exec AddMemList signed-priority insertion + linked-list integrity; checksum=0xffffffff')
