#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.43\0EXEC-PREPARED-TASK-ACTIVATE\0' in data
assert b'exec.library\0LibreKick M2.43 prepared-task context activation slice 40.43\0' in data
activate=data[0x5E00:0x5F00]
restore=data[0x5F00:0x6000]
target=data[0x6000:0x6100]
for op in ('40F900004D48','23CF00004D40','2017','23C000004D44','23FC0000C10000003514','23FC0000C10000004C10','13FC00020000C10F','2E790000C136','4E75'):
    assert bytes.fromhex(op) in activate, f'missing activation opcode {op}'
for op in ('205F','225F','245F','265F','285F','2C5F','2E1F','2C1F','2A1F','281F','261F','241F','46DF','4E75'):
    assert bytes.fromhex(op) in restore, f'missing restore opcode {op}'
for op in ('40F900004D4A','23CF00004D4C','23FC4C4B343300004D50','46F900004D48','2E7900004D40','4E75'):
    assert bytes.fromhex(op) in target, f'missing target opcode {op}'
probe=data[0x5B00:0x5E00]
for value in (0x0000E000,0x0000E800,0x0000E7F0,0x0000E7C2,0x0000E7BE,0x0000E7F4,
              0x00F85F00,0x00F86000,0x4C4B3433,0x43000002,0x0000E506):
    assert struct.pack('>I',value) in probe, f'missing M2.43 value {value:08x}'
assert bytes.fromhex('4EB900F85E00') in probe, 'missing prepared-task activation call'
assert bytes.fromhex('303900004D4A0C402700') in probe, 'missing target SR verification'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe
# M2.42 green gate must chain into M2.43.
prev=data[0x5600:0x5900]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0
branch_abs=0x5600+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x5B00

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.43 check PASS: {p} ({len(data)} bytes)')
print('Exec private prepared-task activation qualification; checksum=0xffffffff')
