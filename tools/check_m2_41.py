#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.41\0EXEC-CONTEXT-PC-RESUME\0' in data
assert b'exec.library\0LibreKick M2.41 private PC resume handoff slice 40.41\0' in data

handoff=data[0x5500:0x5580]
resume=data[0x5580:0x55C0]
assert bytes.fromhex('227900003514') in handoff, 'missing ThisTask load'
assert bytes.fromhex('20290036') in handoff, 'missing tc_SPReg load'
assert bytes.fromhex('23CF00004CC0') in handoff, 'missing caller A7 save'
assert bytes.fromhex('2217') in handoff, 'missing caller return-PC read'
assert bytes.fromhex('23C100004CCC') in handoff, 'missing caller PC observation'
assert bytes.fromhex('2E40') in handoff, 'missing task A7 handoff'
assert bytes.fromhex('2F3C00F85580') in handoff, 'missing private resume-PC push'
assert bytes.fromhex('23CF00004CC4') in handoff, 'missing frame-SP observation'
assert bytes.fromhex('4E75') in handoff, 'missing task-stack RTS transfer'
assert bytes.fromhex('23CF00004CC8') in resume, 'missing resumed A7 observation'
assert bytes.fromhex('23FC4C4B343100004CD0') in resume, 'missing arrival marker'
assert bytes.fromhex('2E7900004CC0') in resume, 'missing caller A7 restore'
assert bytes.fromhex('4E75') in resume, 'missing caller-stack RTS'

probe=data[0x5300:0x5500]
for value in (0x0000D7F0,0x0000D7EC,0x0000D6C0,0x0000D6BC,
              0x00004CC0,0x00004CC4,0x00004CC8,0x00004CCC,0x00004CD0,
              0x4C4B3431,0x00F85580):
    assert struct.pack('>I',value) in probe or value==0x00F85580, f'missing expected PC-resume value {value:08x}'
assert probe.count(bytes.fromhex('4EB900F85500')) >= 2, 'expected two PC-resume handoff calls'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.40 success gate must branch into M2.41 probe.
prev=data[0x4F00:0x5100]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.40 success gate missing'
branch_abs=0x4F00+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x5300, 'M2.40 gate does not branch to M2.41 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4):
    t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.41 check PASS: {p} ({len(data)} bytes)')
print('Exec private task-stack PC resume handoff qualification; checksum=0xffffffff')
