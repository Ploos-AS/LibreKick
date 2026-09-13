#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.32\0EXEC-SIGNAL-CURRENT\0' in data
assert b'exec.library\0LibreKick M2.32 Signal current-task delivery slice 40.32\0' in data

routine=data[0x3800:0x3840]
assert bytes.fromhex('223900004C14') in routine, 'missing current signal-state load'
assert bytes.fromhex('8280') in routine, 'missing Signal OR operation'
assert bytes.fromhex('23C100004C14') in routine, 'missing signal-state store'
assert bytes.fromhex('221F4E75') in routine, 'missing Signal epilogue'

probe=data[0x3600:0x3800]
# Signal vector: LVO -324 at ExecBase $3400 -> $32BC, target $00F83800.
vec_addr=0x00003400-324
vec_target=0x00F83800
vec_sig=(bytes.fromhex('23FC')+struct.pack('>I',0x4EF90000|((vec_target>>16)&0xffff))+
         struct.pack('>I',vec_addr)+bytes.fromhex('33FC')+
         struct.pack('>H',vec_target&0xffff)+struct.pack('>I',vec_addr+4))
assert vec_sig in probe, 'missing Signal LVO -324 JMP vector install'
assert bytes.fromhex('4EAEFEDA2240') in probe, 'missing FindTask(NULL) integration'
assert probe.count(bytes.fromhex('4EAEFEBC')) >= 4, 'expected four Signal calls'
for value in (0x00000015,0x0000001F,0x8000001F):
    assert struct.pack('>I',value) in probe, f'missing expected Signal state {value:08x}'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.31 success gate must branch into M2.32 probe.
prev=data[0x3300:0x3500]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.31 success gate missing'
branch_abs=0x3300+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x3600, 'M2.31 gate does not branch to M2.32 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4):
    t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.32 check PASS: {p} ({len(data)} bytes)')
print('Exec Signal current-task delivery qualification; checksum=0xffffffff')
