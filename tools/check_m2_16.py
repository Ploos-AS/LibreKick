#!/usr/bin/env python3
from pathlib import Path
import struct,sys

ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008
DYN_HEAD=0x4C00; ABASE=0x9000; BBASE=0xA000; CBASE=0xB000
MARKER_OFF=0x1E00; IDENT_OFF=0x1E80; DYN_ALLOC_OFF=0x1600
MARKER=b'LIBREKICK-M2.16\0EXEC-DYNAMIC-ALLOCMEM-TRAVERSAL\0'
IDENT=b'exec.library\0LibreKick M2.16 dynamic AllocMem traversal slice 40.16\0'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)

def need(haystack,needle,what):
    assert needle in haystack, f'missing {what}'

p=Path(sys.argv[1]); data=p.read_bytes(); assert len(data)==ROM_SIZE
assert struct.unpack_from('>II',data,0)==(SP,PC)
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)]==MARKER
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)]==IDENT

boot=data[8:0x0B00]
assert boot.count(bytes.fromhex('4EAEFD96'))>=3, 'missing three AddMemList() calls'
for base,name in ((ABASE,'FAST A'),(BBASE,'CHIP B'),(CBASE,'FAST C')):
    need(boot,bytes.fromhex('207C')+struct.pack('>I',base),f'{name} base load')
need(boot,bytes.fromhex('0C80')+struct.pack('>I',ABASE+32),'dynamic A allocation result check')
need(boot,bytes.fromhex('0C80')+struct.pack('>I',0x0FC0),'post-allocation FAST total')
need(boot,bytes.fromhex('33FC00F000DFF180'),'PASS color write')
need(boot,bytes.fromhex('33FC000F00DFF180'),'FAIL color write')

alloc=data[0x0B00:0x0C00]
need(alloc,struct.pack('>I',DYN_HEAD),'AllocMem dynamic-head load')
need(alloc,bytes.fromhex('3828000E'),'dynamic attribute read')
need(alloc,bytes.fromhex('4EB9')+struct.pack('>I',0x00F80000+DYN_ALLOC_OFF),'generic dynamic allocator call')
need(alloc,bytes.fromhex('2051'),'linked-header advance')
need(alloc,bytes.fromhex('08040002'),'FAST attribute filter')
need(alloc,bytes.fromhex('08040001'),'CHIP attribute filter')

core=data[DYN_ALLOC_OFF:DYN_ALLOC_OFF+0x100]
need(core,bytes.fromhex('22680010'),'generic mh_First load via A0')
need(core,bytes.fromhex('24290004'),'generic MemChunk size load')
need(core,bytes.fromhex('214A0010'),'generic mh_First update')
need(core,bytes.fromhex('2428001C94812142001C'),'split mh_Free update')
need(core,bytes.fromhex('2628001C96822143001C'),'whole-chunk mh_Free update')

# M2.16 must reuse the M2.15 linked AddMemList implementation.
add=data[0x1400:0x1500]
need(add,bytes.fromhex('2679')+struct.pack('>I',DYN_HEAD),'preserved old dynamic head in A3')
need(add,bytes.fromhex('27480004'),'old-head ln_Pred update')

t=0
for o in range(0,ROM_SIZE,4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.16 check PASS: {p} ({len(data)} bytes)')
print('Exec AllocMem linked dynamic MemHeader traversal + generic dynamic allocator; checksum=0xffffffff')
