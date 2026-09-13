#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.25\0EXEC-DYNAMIC-PREDECESSOR-MERGE\0' in data
assert b'exec.library\0LibreKick M2.25 dynamic predecessor-only FreeMem merge slice 40.25\0' in data
# M2.17 dynamic FreeMem core must retain predecessor merge machinery.
dyn=data[0x1800:0x2000]
assert bytes.fromhex('220B4A81') in dyn, 'missing predecessor-presence test'
assert bytes.fromhex('244B222B0004D5C1') in dyn, 'missing predecessor-end calculation'
assert bytes.fromhex('22290004D3AB0004') in dyn, 'missing predecessor byte merge'
assert bytes.fromhex('2451268A') in dyn, 'missing predecessor successor relink'
# Probe: three $100 allocations, tail $9320/$CE0, predecessor-only merge to $200.
probe=data[0x2600:0x2800]
assert probe.count(bytes.fromhex('203C00000100')) >= 3
for value in (0x00009020,0x00009120,0x00009220,0x00009320,0x00000CE0,0x00000200):
    assert struct.pack('>I',value) in probe
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe
# M2.24 success gate must branch into M2.25 probe.
prev=data[0x2400:0x2600]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.24 success gate missing'
branch_abs=0x2400+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x2600, 'M2.24 gate does not branch to M2.25 probe'
def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.25 check PASS: {p} ({len(data)} bytes)')
print('Exec dynamic predecessor-only FreeMem merge qualification; checksum=0xffffffff')
