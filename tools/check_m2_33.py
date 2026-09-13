#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.33\0EXEC-WAIT-READY\0' in data
assert b'exec.library\0LibreKick M2.33 Wait immediate-ready signal slice 40.33\0' in data

routine=data[0x3B00:0x3B40]
assert bytes.fromhex('223900004C14') in routine, 'missing current signal-state load'
assert bytes.fromhex('C08124004682C282') in routine, 'missing Wait ready-mask/clear core'
assert bytes.fromhex('23C100004C14') in routine, 'missing remaining signal-state store'
assert bytes.fromhex('241F221F4E75') in routine, 'missing Wait epilogue'

probe=data[0x3900:0x3B00]
# vector() writes JMP $00F83B00 into Exec LVO -318 ($32C2) using the
# inherited split MOVE.L/MOVE.W installer.
vec_addr=0x00003400-318
vec_target=0x00F83B00
vec_sig=(bytes.fromhex('23FC')+struct.pack('>I',0x4EF90000|((vec_target>>16)&0xffff))+
         struct.pack('>I',vec_addr)+bytes.fromhex('33FC')+
         struct.pack('>H',vec_target&0xffff)+struct.pack('>I',vec_addr+4))
assert vec_sig in probe, 'missing Wait LVO -318 JMP vector install'
assert struct.pack('>I',0x00004C14) in probe, 'missing signal-state cell'
assert probe.count(bytes.fromhex('4EAEFEBC')) >= 2, 'expected Signal setup calls'
assert probe.count(bytes.fromhex('4EAEFEC2')) >= 3, 'expected three Wait calls'
for value in (0x00000015,0x00000010,0x8000001A,0x80000010):
    assert struct.pack('>I',value) in probe, f'missing expected signal value {value:08x}'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.32 success gate must branch into M2.33 probe.
prev=data[0x3600:0x3800]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.32 success gate missing'
branch_abs=0x3600+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x3900, 'M2.32 gate does not branch to M2.33 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4):
    t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.33 check PASS: {p} ({len(data)} bytes)')
print('Exec Wait immediate-ready signal qualification; checksum=0xffffffff')
