#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.28\0EXEC-DYNAMIC-FREEMEM-SORTED-INSERT\0' in data
assert b'exec.library\0LibreKick M2.28 dynamic non-coalescing FreeMem insertion slice 40.28\0' in data
# Dynamic FreeMem core must retain sorted insertion and both optional merge paths.
dyn=data[0x1800:0x2000]
assert bytes.fromhex('268A') in dyn, 'missing predecessor next-link insertion'
assert bytes.fromhex('29490010') in dyn, 'missing mh_First insertion path'
assert bytes.fromhex('22084A81') in dyn, 'missing successor-presence test'
assert bytes.fromhex('220B4A81') in dyn, 'missing predecessor-presence test'
# Probe: four $100 allocations, then free $9120 without adjacency.
probe=data[0x2C00:0x2E00]
assert probe.count(bytes.fromhex('203C00000100')) >= 5
for value in (0x00009020,0x00009120,0x00009220,0x00009320,0x00009420,0x00000BE0,0x00000CE0,0x00000FE0):
    assert struct.pack('>I',value) in probe
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe
# M2.27 success gate must branch into M2.28 probe.
prev=data[0x2A00:0x2C00]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.27 success gate missing'
branch_abs=0x2A00+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x2C00, 'M2.27 gate does not branch to M2.28 probe'
def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.28 check PASS: {p} ({len(data)} bytes)')
print('Exec dynamic sorted non-coalescing FreeMem insertion qualification; checksum=0xffffffff')
