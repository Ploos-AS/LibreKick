#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.34\0EXEC-ADDTASK-READY\0' in data
assert b'exec.library\0LibreKick M2.34 AddTask ready-list registration slice 40.34\0' in data

routine=data[0x3E00:0x3E40]
assert bytes.fromhex('41F900003574') in routine, 'missing TaskReady address load'
assert bytes.fromhex('4EAEFEF2') in routine, 'missing Enqueue LVO -270 call'
assert bytes.fromhex('137C0003000F') in routine, 'missing tc_State=TS_READY store'
assert bytes.fromhex('20094E75') in routine, 'missing AddTask return task pointer'

probe=data[0x3C00:0x3E00]
# AddTask vector: ExecBase $3400 + LVO -282 = $32E6, target $00F83E00.
vec_addr=0x00003400-282
vec_target=0x00F83E00
vec_sig=(bytes.fromhex('23FC')+struct.pack('>I',0x4EF90000|((vec_target>>16)&0xffff))+
         struct.pack('>I',vec_addr)+bytes.fromhex('33FC')+
         struct.pack('>H',vec_target&0xffff)+struct.pack('>I',vec_addr+4))
assert vec_sig in probe, 'missing AddTask LVO -282 JMP vector install'

# TaskReady classic ExecBase offset and two prepared Task nodes.
assert struct.pack('>I',0x00003574) in probe, 'missing ExecBase->TaskReady reference'
for addr in (0x0000C100,0x0000C200):
    assert struct.pack('>I',addr) in probe, f'missing task address {addr:08x}'
assert probe.count(bytes.fromhex('4EAEFEE6')) >= 2, 'expected two AddTask calls'
# Probe priorities/type words: NT_TASK=1, priorities 2 and 7.
assert bytes.fromhex('33FC01020000C108') in probe, 'missing task A type/priority initialization'
assert bytes.fromhex('33FC01070000C208') in probe, 'missing task B type/priority initialization'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.33 success gate must branch into M2.34 probe.
prev=data[0x3900:0x3B00]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.33 success gate missing'
branch_abs=0x3900+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x3C00, 'M2.33 gate does not branch to M2.34 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4):
    t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.34 check PASS: {p} ({len(data)} bytes)')
print('Exec AddTask ready-list registration qualification; checksum=0xffffffff')
