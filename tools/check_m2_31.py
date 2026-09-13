#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.31\0EXEC-SETSIGNAL-CURRENT\0' in data
assert b'exec.library\0LibreKick M2.31 SetSignal current-task signal slice 40.31\0' in data

routine=data[0x3500:0x3540]
assert bytes.fromhex('243900004C14') in routine, 'missing current signal-state load'
assert bytes.fromhex('26014683C483C0818480') in routine, 'missing masked SetSignal update core'
assert bytes.fromhex('203900004C14') in routine, 'missing old-signal return load'
assert bytes.fromhex('23C200004C14') in routine, 'missing signal-state store'
assert bytes.fromhex('261F241F4E75') in routine, 'missing SetSignal epilogue'

probe=data[0x3300:0x3500]
# vector() writes JMP $00F83500 into Exec LVO -306 ($32CE) using a split
# MOVE.L/MOVE.W install sequence.
vec_addr=0x00003400-306
vec_target=0x00F83500
vec_sig=(bytes.fromhex('23FC')+struct.pack('>I',0x4EF90000|((vec_target>>16)&0xffff))+
         struct.pack('>I',vec_addr)+bytes.fromhex('33FC')+
         struct.pack('>H',vec_target&0xffff)+struct.pack('>I',vec_addr+4))
assert vec_sig in probe, 'missing SetSignal LVO -306 JMP vector install'
assert struct.pack('>I',0x00004C14) in probe, 'missing signal-state cell'
assert struct.pack('>I',0x12345678) in probe, 'missing initial signal-state seed'
assert probe.count(bytes.fromhex('4EAEFECE')) >= 4, 'expected four SetSignal calls'
for value in (0x12345673,0x12345670,0x1234567C):
    assert struct.pack('>I',value) in probe, f'missing expected SetSignal state {value:08x}'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.30 success gate must branch into M2.31 probe.
prev=data[0x3000:0x3200]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.30 success gate missing'
branch_abs=0x3000+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x3300, 'M2.30 gate does not branch to M2.31 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4):
    t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.31 check PASS: {p} ({len(data)} bytes)')
print('Exec SetSignal current-task signal-state qualification; checksum=0xffffffff')
