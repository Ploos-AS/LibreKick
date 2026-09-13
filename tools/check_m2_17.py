#!/usr/bin/env python3
from pathlib import Path
import struct,sys

ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008
DYN_HEAD=0x4C00; ABASE=0x9000; BBASE=0xA000; CBASE=0xB000
MARKER_OFF=0x2000; IDENT_OFF=0x2080; DYN_ALLOC_OFF=0x1600; DYN_FREE_OFF=0x1800
MARKER=b'LIBREKICK-M2.17\0EXEC-DYNAMIC-FREEMEM-ROUTING\0'
IDENT=b'exec.library\0LibreKick M2.17 dynamic FreeMem routing slice 40.17\0'

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
assert boot.count(bytes.fromhex('4EAEFD96'))>=3, 'missing AddMemList calls'
assert boot.count(bytes.fromhex('4EAEFF2E'))>=4, 'missing FreeMem probes'
need(boot,bytes.fromhex('0CB9')+struct.pack('>II',ABASE+32,ABASE+16),'A restore mh_First check')
need(boot,bytes.fromhex('0CB9')+struct.pack('>II',BBASE+32,BBASE+16),'B restore mh_First check')
need(boot,bytes.fromhex('33FC00F000DFF180'),'PASS color')
need(boot,bytes.fromhex('33FC000F00DFF180'),'FAIL color')

freew=data[0x0C00:0x0D00]
need(freew,struct.pack('>I',DYN_HEAD),'dynamic head load')
need(freew,bytes.fromhex('24280014B282'),'mh_Lower address test')
need(freew,bytes.fromhex('24280018B282'),'mh_Upper address test')
need(freew,bytes.fromhex('4EB9')+struct.pack('>I',0x00F80000+DYN_FREE_OFF),'generic dynamic free call')
need(freew,bytes.fromhex('2050'),'linked-header advance')

core=data[DYN_FREE_OFF:DYN_FREE_OFF+0x200]
need(core,bytes.fromhex('2848'),'preserve selected MemHeader in A4')
need(core,bytes.fromhex('206C0010'),'relative mh_First load')
need(core,bytes.fromhex('29490010'),'relative mh_First update')
need(core,bytes.fromhex('222C001CD2822941001C'),'relative mh_Free increment')
need(core,bytes.fromhex('22280004D3A90004'),'successor coalesce')
need(core,bytes.fromhex('22290004D3AB0004'),'predecessor coalesce')

alloc=data[0x0B00:0x0C00]
need(alloc,bytes.fromhex('4EB9')+struct.pack('>I',0x00F80000+DYN_ALLOC_OFF),'M2.16 dynamic allocator preserved')

t=0
for o in range(0,ROM_SIZE,4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.17 check PASS: {p} ({len(data)} bytes)')
print('Exec FreeMem dynamic MemHeader routing + generic sorted/coalescing free core; checksum=0xffffffff')
