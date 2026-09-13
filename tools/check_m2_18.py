#!/usr/bin/env python3
from pathlib import Path
import struct, sys
p=Path(sys.argv[1])
data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.18\0EXEC-DYNAMIC-MEMF-LARGEST\0' in data
assert b'exec.library\0LibreKick M2.18 dynamic MEMF_LARGEST slice 40.18\0' in data
# The M2.18 AvailMem slot must reference the linked dynamic-head pointer,
# mh_Attributes, mh_First and mc_Bytes offsets used by the runtime traversal.
av=data[0x0D00:0x0E00]
assert struct.pack('>I',0x4C00) in av
assert struct.pack('>H',0x000E) in av
assert struct.pack('>H',0x0010) in av
assert struct.pack('>H',0x0004) in av
# Runtime probe embeds the dynamic-A largest result (0x0fe0).
assert struct.pack('>I',0x0FE0) in data[8:0x0B00]
def ones(total,value):
    total+=value
    return (total&0xffffffff)+(total>>32)
total=0
for off in range(0,len(data),4):
    total=ones(total,struct.unpack_from('>I',data,off)[0])
total=(total&0xffffffff)+(total>>32)
assert total==0xffffffff, f'bad checksum {total:08x}'
print(f'M2.18 check PASS: {p} ({len(data)} bytes)')
print('Exec AvailMem dynamic MEMF_LARGEST traversal; checksum=0xffffffff')
