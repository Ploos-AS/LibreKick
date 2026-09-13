#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.24\0EXEC-DYNAMIC-HEAD-SPLIT\0' in data
assert b'exec.library\0LibreKick M2.24 dynamic head split slice 40.24\0' in data
# M2.21 dynamic allocator must retain split-head replacement semantics.
dyn=data[0x1600:0x1800]
assert bytes.fromhex('214A0010') in dyn, 'missing mh_First replacement path'
assert bytes.fromhex('268A') in dyn, 'missing prev.next replacement path'
assert bytes.fromhex('0C8300000008') in dyn, 'missing whole/split threshold'
# M2.24 probe occupies its dedicated ROM window and exercises a $100 dynamic
# FAST allocation from A's head, checking the remainder at $9120/$EE0.
probe=data[0x2400:0x2600]
assert bytes.fromhex('203C00000100') in probe
for value in (0x00009020,0x00009120,0x00000EE0,0x00000FE0):
    assert struct.pack('>I',value) in probe
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe
# M2.23 success gate must branch into the M2.24 probe window.
prev=data[0x2200:0x2400]
sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig)
assert gp>=0, 'M2.23 success gate missing'
branch_abs=0x2200+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x2400, 'M2.23 gate does not branch to M2.24 probe'
# Kickstart checksum must remain all ones.
def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.24 check PASS: {p} ({len(data)} bytes)')
print('Exec dynamic head MemChunk split qualification; checksum=0xffffffff')
