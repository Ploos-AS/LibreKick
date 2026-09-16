#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.45\0SHARED-EXEC-TASK-SWAP-RUNTIME\0' in data
assert b'exec.library\0LibreKick M2.45 shared Exec task swap runtime 40.45\0' in data
getsysbase=data[0x6100:0x6200]
getcurrent=data[0x6200:0x6300]
setcurrent=data[0x6300:0x6400]
task_probe=data[0x6400:0x6500]
swapcurrent=data[0x6500:0x6600]
swap_probe=data[0x6600:0x6700]
assert bytes.fromhex('2039000000044e75') == getsysbase[:8]
assert bytes.fromhex('207900000004202801144e75') == getcurrent[:12]
assert bytes.fromhex('207900000004214001144e75') == setcurrent[:12]
assert bytes.fromhex('207900000004222801142140011420014e75') == swapcurrent[:18], 'shared SwapCurrentTask bytes missing'
assert bytes.fromhex('203C0000C9454EB900F865000C800000C100') in swap_probe, 'missing swap-to-sentinel/old TASK_A verification'
assert bytes.fromhex('0CB90000C94500003514') in swap_probe, 'missing swapped ThisTask sentinel verification'
assert bytes.fromhex('203C0000C1004EB900F865000C800000C945') in swap_probe, 'missing swap-back/old sentinel verification'
assert bytes.fromhex('0CB90000C10000003514') in swap_probe, 'missing restored ThisTask verification'
assert bytes.fromhex('33FC00F000DFF180') in swap_probe
assert bytes.fromhex('33FC000F00DFF18060FE') in swap_probe
# M2.44 success edge must enter M2.45 at 0x6600.
sig=bytes.fromhex('33FC00F000DFF1806000')
gp=task_probe.rfind(sig); assert gp>=0
branch_abs=0x6400+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
ext_abs=branch_abs+2+disp
assert ext_abs==0x6600, f'unexpected M2.45 swap probe target {ext_abs:#x}'
assert data[ext_abs:ext_abs+6]==bytes.fromhex('203C0000C945')
def ones(t,v):
    t+=v; return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.45 check PASS: {p} ({len(data)} bytes)')
print('Shared SwapCurrentTask reversible task-pointer convergence; checksum=0xffffffff')
print('scope=private runtime primitive; public Exec scheduler/vectors/full task switch not claimed')
