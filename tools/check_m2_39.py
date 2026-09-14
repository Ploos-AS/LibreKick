#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.39\0EXEC-CONTEXT-REGSET\0' in data
assert b'exec.library\0LibreKick M2.39 expanded preserved-register frame slice 40.39\0' in data

routine=data[0x4E00:0x4F00]
assert bytes.fromhex('227900003514') in routine, 'missing ThisTask load'
assert bytes.fromhex('20290036') in routine, 'missing tc_SPReg load'
assert bytes.fromhex('23CF00004C34') in routine, 'missing caller A7 save'
assert bytes.fromhex('2E40') in routine, 'missing task A7 handoff'

# Exact push order D2-D7 then A2-A6.
pushes=b''.join(struct.pack('>H',0x2F00+r) for r in range(2,8)) + \
       b''.join(struct.pack('>H',0x2F08+r) for r in range(2,7))
assert pushes in routine, 'missing expanded D2-D7/A2-A6 save frame'
assert bytes.fromhex('23CF00004C38') in routine, 'missing frame-SP observation'

# Restore order must be exact reverse: A6-A2 then D7-D2.
pops=b''.join(struct.pack('>H',0x205F+(r<<9)) for r in reversed(range(2,7))) + \
     b''.join(struct.pack('>H',0x201F+(r<<9)) for r in reversed(range(2,8)))
# Observation stores sit between pops, so verify each opcode individually/in order by scan.
pos=0
for r in reversed(range(2,7)):
    op=struct.pack('>H',0x205F+(r<<9)); n=routine.find(op,pos); assert n>=0; pos=n+2
for r in reversed(range(2,8)):
    op=struct.pack('>H',0x201F+(r<<9)); n=routine.find(op,pos); assert n>=0; pos=n+2

assert bytes.fromhex('2E7900004C34') in routine, 'missing caller A7 restore'
assert bytes.fromhex('4E75') in routine, 'missing safe RTS'

probe=data[0x4C00:0x4E00]
for value in (0x0000C236,0x0000D7F0,0x0000D7C4,0x00004C34,0x00004C38,
              0x22000002,0x22000003,0x22000004,0x22000005,0x22000006,0x22000007,
              0x0000E202,0x0000E203,0x0000E204,0x0000E205,0x0000E206):
    assert struct.pack('>I',value) in probe, f'missing expected M2.39 value {value:08x}'
assert bytes.fromhex('4EB900F84E00') in probe, 'missing expanded context helper call'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.38 success gate must branch into M2.39 probe.
prev=data[0x4900:0x4B00]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.38 success gate missing'
branch_abs=0x4900+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x4C00, 'M2.38 gate does not branch to M2.39 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4):
    t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.39 check PASS: {p} ({len(data)} bytes)')
print('Exec expanded preserved-register frame qualification; checksum=0xffffffff')
