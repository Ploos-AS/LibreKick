#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.29\0EXEC-DYNAMIC-ALLOCATION-ALIGNMENT\0' in data
assert b'exec.library\0LibreKick M2.29 dynamic allocation alignment slice 40.29\0' in data

# Both dynamic allocation and free cores must round sizes up to 8 bytes.
align=bytes.fromhex('0680000000070280FFFFFFF8')
alloc_core=data[0x1600:0x1800]
free_core=data[0x1800:0x2000]
assert align in alloc_core, 'missing dynamic AllocMem 8-byte alignment sequence'
assert align in free_core, 'missing dynamic FreeMem 8-byte alignment sequence'

# Probe exhausts static FAST and dynamic C, then requests 1 and 9 bytes in A.
probe=data[0x2E00:0x3000]
for value in (0x00001000,0x000000E0,0x0000B020,0x00000001,0x00000009,
              0x00009020,0x00009028,0x00009038,0x00000FC8,0x00000FE0,
              0x000020C0):
    assert struct.pack('>I',value) in probe, f'missing probe value {value:#010x}'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.28 success gate must branch into M2.29 probe.
prev=data[0x2C00:0x2E00]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.28 success gate missing'
branch_abs=0x2C00+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x2E00, 'M2.28 gate does not branch to M2.29 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.29 check PASS: {p} ({len(data)} bytes)')
print('Exec dynamic AllocMem/FreeMem 8-byte alignment qualification; checksum=0xffffffff')
