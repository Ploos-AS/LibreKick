#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.38\0EXEC-CONTEXT-REGFRAME\0' in data
assert b'exec.library\0LibreKick M2.38 small register-context frame slice 40.38\0' in data

routine=data[0x4B00:0x4B60]
assert bytes.fromhex('227900003514') in routine, 'missing ThisTask load'
assert bytes.fromhex('20290036') in routine, 'missing tc_SPReg load'
assert bytes.fromhex('23CF00004C24') in routine, 'missing caller A7 save'
assert bytes.fromhex('2E40') in routine, 'missing task A7 handoff'
assert bytes.fromhex('2F022F0A') in routine, 'missing D2/A2 register saves'
assert bytes.fromhex('23CF00004C28') in routine, 'missing frame-SP observation'
assert bytes.fromhex('243CDEADBEEF') in routine, 'missing D2 clobber'
assert bytes.fromhex('247C0000E2F0') in routine, 'missing A2 clobber'
assert bytes.fromhex('245F241F') in routine, 'missing A2/D2 register restores'
assert bytes.fromhex('23C200004C2C') in routine, 'missing restored D2 observation'
assert bytes.fromhex('23CA00004C30') in routine, 'missing restored A2 observation'
assert bytes.fromhex('2E7900004C24') in routine, 'missing caller A7 restore'
assert bytes.fromhex('4E75') in routine, 'missing safe RTS'

probe=data[0x4900:0x4B00]
for value in (0x0000C236,0x0000D7F0,0x0000D7E8,0x0000D7EC,
              0x0000D6C0,0x0000D6B8,0x0000D6BC,
              0x00004C24,0x00004C28,0x00004C2C,0x00004C30,
              0x12345678,0x0000E240,0x89ABCDEF,0x0000E280):
    assert struct.pack('>I',value) in probe, f'missing expected register-frame value {value:08x}'
assert probe.count(bytes.fromhex('4EB900F84B00')) >= 2, 'expected two register-context calls'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.37 success gate must branch into M2.38 probe.
prev=data[0x4600:0x4800]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.37 success gate missing'
branch_abs=0x4600+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x4900, 'M2.37 gate does not branch to M2.38 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4):
    t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.38 check PASS: {p} ({len(data)} bytes)')
print('Exec small register-context frame qualification; checksum=0xffffffff')
