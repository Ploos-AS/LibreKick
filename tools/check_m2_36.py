#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.36\0EXEC-CONTEXT-SP\0' in data
assert b'exec.library\0LibreKick M2.36 current-task stack-context handoff slice 40.36\0' in data

routine=data[0x4500:0x4540]
assert bytes.fromhex('227900003514') in routine, 'missing ExecBase->ThisTask load'
assert bytes.fromhex('20290036') in routine, 'missing classic tc_SPReg +$36 load'
assert bytes.fromhex('23C000004C18') in routine, 'missing next-SP shadow store'
assert bytes.fromhex('4E75') in routine, 'missing context helper RTS'

probe=data[0x4300:0x4500]
# Classic Task stack metadata for selected task B at $C200.
for value in (0x0000C23A,0x0000C23E,0x0000C236,0x0000D000,0x0000D800,
              0x0000D7F0,0x0000D6C0,0x00004C18,0x00003514):
    assert struct.pack('>I',value) in probe, f'missing expected context value {value:08x}'
assert probe.count(bytes.fromhex('4EB900F84500')) >= 2, 'expected two context helper calls'
assert bytes.fromhex('227C000000004EAEFEDA') in probe, 'missing FindTask(NULL) consistency check'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.35 success gate must branch into M2.36 probe.
prev=data[0x4000:0x4200]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.35 success gate missing'
branch_abs=0x4000+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x4300, 'M2.35 gate does not branch to M2.36 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4):
    t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.36 check PASS: {p} ({len(data)} bytes)')
print('Exec current-task stack-context handoff qualification; checksum=0xffffffff')
