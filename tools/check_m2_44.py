#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.44\0SHARED-EXEC-TASK-RUNTIME\0' in data
assert b'exec.library\0LibreKick M2.44 shared Exec task runtime 40.44\0' in data

# M2.43 retained prepared-task helpers remain present.
activate=data[0x5E00:0x5F00]
restore=data[0x5F00:0x6000]
target=data[0x6000:0x6100]
getsysbase=data[0x6100:0x6200]
getcurrent=data[0x6200:0x6300]
setcurrent=data[0x6300:0x6400]
assert bytes.fromhex('4EB900F85E00') in data[0x5B00:0x5E00], 'missing prepared-task activation call'
assert bytes.fromhex('2039000000044e75') == getsysbase[:8], 'shared GetSysBase bytes missing'
assert bytes.fromhex('207900000004202801144e75') == getcurrent[:12], 'shared GetCurrentTask bytes missing'
assert bytes.fromhex('207900000004214001144e75') == setcurrent[:12], 'shared SetCurrentTask bytes missing'
assert bytes.fromhex('4E75') in activate
assert bytes.fromhex('46DF4E75') in restore
assert bytes.fromhex('4E75') in target

probe=data[0x5B00:0x5E00]
# Existing M2.43 shared GetSysBase gate is retained.
assert bytes.fromhex('4EB900F861000C8000003400') in probe
# M2.44 consumes real M2 current-task state, mutates it through the shared
# setter, reads it back, and restores TASK_A before success.
assert bytes.fromhex('4EB900F862000C800000C100') in probe, 'missing GetCurrentTask/TASK_A verification'
assert bytes.fromhex('203C0000C8444EB900F86300') in probe, 'missing SetCurrentTask sentinel call'
assert bytes.fromhex('4EB900F862000C800000C844') in probe, 'missing sentinel readback'
assert bytes.fromhex('203C0000C1004EB900F86300') in probe, 'missing TASK_A restore call'
assert bytes.fromhex('0CB90000C10000003514') in probe, 'missing restored ExecBase->ThisTask verification'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# The old M2.43 success branch must now enter the M2.44 extension rather than
# jumping directly to the old idle loop.
sig=bytes.fromhex('33FC00F000DFF1806000')
gp=probe.rfind(sig); assert gp>=0
branch_abs=0x5B00+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
ext_abs=branch_abs+2+disp
assert 0x5B00 <= ext_abs < 0x5E00
assert data[ext_abs:ext_abs+6] == bytes.fromhex('4EB900F86200')

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.44 check PASS: {p} ({len(data)} bytes)')
print('Exec prepared-task activation + shared GetSysBase/GetCurrentTask/SetCurrentTask convergence; checksum=0xffffffff')
