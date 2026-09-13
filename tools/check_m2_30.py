#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.30\0EXEC-FINDTASK-CURRENT\0' in data
assert b'exec.library\0LibreKick M2.30 FindTask current-task slice 40.30\0' in data
assert b'LibreKick bootstrap task\0' in data

# FindTask implementation: test A1, clean NULL for unsupported named lookup,
# and load the current-task pointer from the dedicated bootstrap cell.
routine=data[0x3200:0x3240]
assert bytes.fromhex('20094A80') in routine, 'missing FindTask name NULL test'
assert bytes.fromhex('70004E75') in routine, 'missing clean named-lookup NULL result'
assert bytes.fromhex('203900004C104E75') in routine, 'missing current-task pointer load'

probe=data[0x3000:0x3200]
# Runtime vector install uses make_m2_17_rom.vector(): it writes a JMP absolute
# instruction as two RAM writes, so the target address is deliberately split
# across the JMP opcode/high word and the following low-word write rather than
# appearing as one contiguous 32-bit immediate in the probe byte stream.
vec_addr=0x00002C00-294
vec_target=0x00F83200
vec_sig=(bytes.fromhex('23FC')+struct.pack('>I',0x4EF90000|((vec_target>>16)&0xffff))+
         struct.pack('>I',vec_addr)+bytes.fromhex('33FC')+
         struct.pack('>H',vec_target&0xffff)+struct.pack('>I',vec_addr+4))
assert vec_sig in probe, 'missing FindTask LVO -294 JMP vector install'
assert struct.pack('>I',0x0000C000) in probe, 'missing bootstrap task pointer'
assert struct.pack('>I',0x00004C10) in probe, 'missing current-task storage cell'
assert probe.count(bytes.fromhex('4EAEFEDA')) >= 3, 'expected three FindTask calls'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.29 success gate must branch into M2.30 probe.
prev=data[0x2E00:0x3000]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.29 success gate missing'
branch_abs=0x2E00+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x3000, 'M2.29 gate does not branch to M2.30 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.30 check PASS: {p} ({len(data)} bytes)')
print('Exec FindTask(NULL) current-task qualification; checksum=0xffffffff')
