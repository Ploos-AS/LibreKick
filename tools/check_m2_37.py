#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.37\0EXEC-CONTEXT-A7\0' in data
assert b'exec.library\0LibreKick M2.37 controlled A7 stack handoff slice 40.37\0' in data

routine=data[0x4800:0x4840]
assert bytes.fromhex('227900003514') in routine, 'missing ExecBase->ThisTask load'
assert bytes.fromhex('20290036') in routine, 'missing classic tc_SPReg +$36 load'
assert bytes.fromhex('23CF00004C1C') in routine, 'missing caller A7 save'
assert bytes.fromhex('2E40') in routine, 'missing tc_SPReg -> A7 handoff'
assert bytes.fromhex('2F3C4C4B3737') in routine, 'missing switched-stack marker push'
assert bytes.fromhex('23CF00004C20') in routine, 'missing switched A7 observation'
assert bytes.fromhex('2E7900004C1C') in routine, 'missing caller A7 restore'
assert bytes.fromhex('4E75') in routine, 'missing safe RTS'

probe=data[0x4600:0x4800]
for value in (0x0000C236,0x0000D000,0x0000D800,0x0000D7F0,0x0000D7EC,
              0x0000D6C0,0x0000D6BC,0x00004C1C,0x00004C20,0x4C4B3737):
    assert struct.pack('>I',value) in probe, f'missing expected A7 handoff value {value:08x}'
assert probe.count(bytes.fromhex('4EB900F84800')) >= 2, 'expected two A7 handoff calls'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.36 success gate must branch into M2.37 probe.
prev=data[0x4300:0x4500]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.36 success gate missing'
branch_abs=0x4300+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x4600, 'M2.36 gate does not branch to M2.37 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4):
    t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.37 check PASS: {p} ({len(data)} bytes)')
print('Exec controlled A7 stack-handoff qualification; checksum=0xffffffff')
