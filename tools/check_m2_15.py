#!/usr/bin/env python3
from pathlib import Path
import struct,sys
ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008; EXEC_BASE=0x3400
DYN_HEAD=0x4C00; ABASE=0x9000; BBASE=0xA000; MARKER_OFF=0x1C00; IDENT_OFF=0x1C80
MARKER=b'LIBREKICK-M2.15\0EXEC-LINKED-DYNAMIC-MEMLIST\0'
IDENT=b'exec.library\0LibreKick M2.15 linked dynamic MemList slice 40.15\0'
def ones(t,v): t+=v; return (t&0xffffffff)+(t>>32)
p=Path(sys.argv[1]); data=p.read_bytes(); assert len(data)==ROM_SIZE
assert struct.unpack_from('>II',data,0)==(SP,PC)
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)]==MARKER
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)]==IDENT
boot=data[8:0x0B00]
assert boot.count(bytes.fromhex('4EAEFD96'))>=2
for v in (DYN_HEAD,ABASE,BBASE,0x0FE0,0x07E0,0x1FE0,0x17E0,0x37C0): assert struct.pack('>I',v) in boot
add=data[0x1400:0x1500]; avail=data[0x0D00:0x0E00]
assert struct.pack('>I',DYN_HEAD) in add and bytes.fromhex('2084') in add
assert bytes.fromhex('27480004') in add
assert struct.pack('>I',DYN_HEAD) in avail and bytes.fromhex('2050') in avail
assert bytes.fromhex('D6A8001C') in avail
assert bytes.fromhex('33FC00F000DFF180') in boot
assert bytes.fromhex('33FC000F00DFF180') in boot
t=0
for o in range(0,ROM_SIZE,4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32); assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.15 check PASS: {p} ({len(data)} bytes)')
print('Exec linked dynamic MemList registration + filtered AvailMem traversal; checksum=0xffffffff')
