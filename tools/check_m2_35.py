#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.35\0EXEC-DISPATCH-SELECT\0' in data
assert b'exec.library\0LibreKick M2.35 ready-to-running selection slice 40.35\0' in data

routine=data[0x4200:0x4240]
assert bytes.fromhex('41F900003596') in routine, 'missing classic TaskReady address load'
assert bytes.fromhex('4EAEFEFE') in routine, 'missing RemHead LVO -258 call'
assert bytes.fromhex('4A8067142240') in routine, 'missing empty-ready guard/current task select'
assert bytes.fromhex('23C000003514') in routine, 'missing ExecBase->ThisTask store'
assert bytes.fromhex('23C000004C10') in routine, 'missing FindTask current-task cell sync'
assert bytes.fromhex('137C0002000F') in routine, 'missing tc_State=TS_RUN store'
assert routine.count(bytes.fromhex('4E75')) >= 1, 'missing dispatcher RTS'

probe=data[0x4000:0x4200]
assert bytes.fromhex('4DF900003400') in probe, 'missing ExecBase in A6'
assert bytes.fromhex('4EB900F84200') in probe, 'missing internal dispatcher call'
for value in (0x0000C100,0x0000C200,0x00003514,0x00003596,0x00004C10):
    assert struct.pack('>I',value) in probe, f'missing expected value {value:08x}'
assert bytes.fromhex('227C000000004EAEFEDA') in probe, 'missing FindTask(NULL) integration check'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.34 success gate must branch into M2.35 probe.
prev=data[0x3C00:0x3E00]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.34 success gate missing'
branch_abs=0x3C00+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x4000, 'M2.34 gate does not branch to M2.35 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4):
    t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.35 check PASS: {p} ({len(data)} bytes)')
print('Exec ready-to-running task selection qualification; checksum=0xffffffff')
