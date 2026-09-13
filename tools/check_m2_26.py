#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.26\0EXEC-DYNAMIC-SUCCESSOR-MERGE\0' in data
assert b'exec.library\0LibreKick M2.26 dynamic successor-only FreeMem merge slice 40.26\0' in data
# M2.17 dynamic FreeMem core must retain successor merge machinery.
dyn=data[0x1800:0x2000]
assert bytes.fromhex('22084A81') in dyn, 'missing successor-presence test'
assert bytes.fromhex('2449D5C2') in dyn, 'missing new-end calculation'
assert bytes.fromhex('22280004D3A90004') in dyn, 'missing successor byte merge'
assert bytes.fromhex('2450228A') in dyn, 'missing successor relink'
# Probe: three $100 allocations. Runtime checks then qualify successor-only
# merges rooted at $9220/$DE0 and $9120/$EE0, followed by full restore to
# $9020/$FE0. The pre-merge tail $9320/$CE0 is setup state only and is not
# encoded as an immediate in this probe, so it must not be required here.
probe=data[0x2800:0x2A00]
assert probe.count(bytes.fromhex('203C00000100')) >= 3
for value in (0x00009020,0x00009120,0x00009220,0x00000DE0,0x00000EE0,0x00000FE0):
    assert struct.pack('>I',value) in probe
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe
# M2.25 success gate must branch into M2.26 probe.
prev=data[0x2600:0x2800]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.25 success gate missing'
branch_abs=0x2600+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x2800, 'M2.25 gate does not branch to M2.26 probe'
def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.26 check PASS: {p} ({len(data)} bytes)')
print('Exec dynamic successor-only FreeMem merge qualification; checksum=0xffffffff')
