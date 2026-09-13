#!/usr/bin/env python3
from pathlib import Path
import struct,sys

ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008; EXEC_BASE=0x3400
DYN_HEAD=0x4C00; ABASE=0x9000; BBASE=0xA000; MARKER_OFF=0x1C00; IDENT_OFF=0x1C80
MARKER=b'LIBREKICK-M2.15\0EXEC-LINKED-DYNAMIC-MEMLIST\0'
IDENT=b'exec.library\0LibreKick M2.15 linked dynamic MemList slice 40.15\0'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)

def need(haystack, needle, what):
    assert needle in haystack, f'missing {what}'

p=Path(sys.argv[1]); data=p.read_bytes(); assert len(data)==ROM_SIZE
assert struct.unpack_from('>II',data,0)==(SP,PC)
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)]==MARKER
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)]==IDENT

boot=data[8:0x0B00]
assert boot.count(bytes.fromhex('4EAEFD96'))>=2, 'missing two AddMemList() calls'

# Check the concrete M2.15 bootstrap instructions instead of requiring every
# expected numeric result to occur as a standalone 32-bit byte string. Some
# values are materialized through instruction operands/derived arithmetic, so
# the old raw-literal scan produced false negatives despite a valid ROM.
need(boot, bytes.fromhex('207C')+struct.pack('>I',ABASE), 'dynamic FAST A base load')
need(boot, bytes.fromhex('207C')+struct.pack('>I',BBASE), 'dynamic CHIP B base load')
need(boot, struct.pack('>I',DYN_HEAD), 'dynamic MemList head reference')

# The runtime probe must contain the three post-registration AvailMem expected
# totals and the base-only MEMF_LARGEST expectation. cmpd0() encodes these as
# CMP.L #imm,D0 (0c80 + 32-bit immediate).
for value,name in (
    (0x1FE0,'FAST total after registration'),
    (0x17E0,'CHIP total after registration'),
    (0x37C0,'combined total after registration'),
    (0x1000,'base-only MEMF_LARGEST result'),
):
    need(boot, bytes.fromhex('0C80')+struct.pack('>I',value), name)

add=data[0x1400:0x1500]; avail=data[0x0D00:0x0E00]
need(add, struct.pack('>I',DYN_HEAD), 'AddMemList dynamic-head access')
need(add, bytes.fromhex('2084'), 'AddMemList ln_Succ store')
need(add, bytes.fromhex('27480004'), 'AddMemList old-head ln_Pred update')
need(avail, struct.pack('>I',DYN_HEAD), 'AvailMem dynamic-head access')
need(avail, bytes.fromhex('2050'), 'AvailMem linked-list advance')
need(avail, bytes.fromhex('D6A8001C'), 'AvailMem mh_Free accumulation')
need(boot, bytes.fromhex('33FC00F000DFF180'), 'PASS color write')
need(boot, bytes.fromhex('33FC000F00DFF180'), 'FAIL color write')

t=0
for o in range(0,ROM_SIZE,4):
    t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'

print(f'M2.15 check PASS: {p} ({len(data)} bytes)')
print('Exec linked dynamic MemList registration + filtered AvailMem traversal; checksum=0xffffffff')
