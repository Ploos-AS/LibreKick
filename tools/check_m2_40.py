#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.40\0EXEC-CONTEXT-SR\0' in data
assert b'exec.library\0LibreKick M2.40 SR-aware context frame slice 40.40\0' in data

routine=data[0x5100:0x5220]
assert bytes.fromhex('227900003514') in routine, 'missing ThisTask load'
assert bytes.fromhex('20290036') in routine, 'missing tc_SPReg load'
assert bytes.fromhex('428040C0') in routine, 'missing zero-extended SR capture'
assert bytes.fromhex('3F00') in routine, 'missing SR push'
assert bytes.fromhex('0A3C001F') in routine, 'missing bounded CCR perturbation'
assert bytes.fromhex('46DF') in routine, 'missing SR restore from task stack'
assert bytes.fromhex('2E7900004C80') in routine, 'missing caller A7 restore'
assert bytes.fromhex('4E75') in routine, 'missing safe RTS'

probe=data[0x4F00:0x5100]
for value in (0x0000C236,0x0000D7F0,0x0000D7C2,0x00004C80,0x00004C84,
              0x00004C88,0x00004C8C):
    assert struct.pack('>I',value) in probe, f'missing expected SR-frame value {value:08x}'
assert bytes.fromhex('4EB900F85100') in probe, 'missing M2.40 context call'
assert bytes.fromhex('203900004C88B0B900004C8C') in probe, 'missing original/restored SR comparison'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

prev=data[0x4C00:0x4E00]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.39 success gate missing'
branch_abs=0x4C00+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x4F00, 'M2.39 gate does not branch to M2.40 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.40 check PASS: {p} ({len(data)} bytes)')
print('Exec SR-aware task-context frame qualification; checksum=0xffffffff')
