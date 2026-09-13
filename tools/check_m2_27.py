#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.27\0EXEC-DYNAMIC-BIDIRECTIONAL-MERGE\0' in data
assert b'exec.library\0LibreKick M2.27 dynamic bidirectional FreeMem merge slice 40.27\0' in data
# Dynamic FreeMem core must retain both successor and predecessor merge paths.
dyn=data[0x1800:0x2000]
for sig,msg in [
    ('22084A81','missing successor-presence test'),
    ('2449D5C2','missing successor-end calculation'),
    ('22280004D3A90004','missing successor byte merge'),
    ('2450228A','missing successor relink'),
    ('220B4A81','missing predecessor-presence test'),
    ('244B222B0004D5C1','missing predecessor-end calculation'),
    ('22290004D3AB0004','missing predecessor byte merge'),
    ('2451268A','missing predecessor successor relink'),
]:
    assert bytes.fromhex(sig) in dyn, msg
# Probe: three $100 allocations; free A0 and A2 to form two free neighbors,
# then free A1 and require one complete $9020/$FE0 chunk.
probe=data[0x2A00:0x2C00]
assert probe.count(bytes.fromhex('203C00000100')) >= 3
for value in (0x00009020,0x00009120,0x00009220,0x00000DE0,0x00000EE0,0x00000FE0):
    assert struct.pack('>I',value) in probe
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe
# M2.26 success gate must branch into M2.27 probe.
prev=data[0x2800:0x2A00]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.26 success gate missing'
branch_abs=0x2800+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x2A00, 'M2.26 gate does not branch to M2.27 probe'
def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.27 check PASS: {p} ({len(data)} bytes)')
print('Exec dynamic bidirectional FreeMem merge qualification; checksum=0xffffffff')
