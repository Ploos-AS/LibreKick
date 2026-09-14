#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.42\0EXEC-CONTEXT-INTEGRATED\0' in data
assert b'exec.library\0LibreKick M2.42 integrated private context transfer slice 40.42\0' in data

handoff=data[0x5800:0x5900]
resume=data[0x5900:0x5A00]
assert bytes.fromhex('40F900004CE8') in handoff, 'missing entry SR capture'
assert bytes.fromhex('227900003514') in handoff, 'missing ThisTask load'
assert bytes.fromhex('20290036') in handoff, 'missing tc_SPReg load'
assert bytes.fromhex('23CF00004CE0') in handoff, 'missing caller A7 save'
assert bytes.fromhex('2217') in handoff, 'missing caller return-PC read'
assert bytes.fromhex('23C100004CE4') in handoff, 'missing caller return-PC store'
assert bytes.fromhex('2E40') in handoff, 'missing task-stack A7 handoff'
assert bytes.fromhex('3F3900004CE8') in handoff, 'missing captured SR push'
for op in ('2F02','2F03','2F04','2F05','2F06','2F07','2F0A','2F0B','2F0C','2F0D','2F0E'):
    assert bytes.fromhex(op) in handoff, f'missing preserved-register save {op}'
assert bytes.fromhex('0A3C001F') in handoff, 'missing CCR perturbation'
assert bytes.fromhex('2F3C00F85900') in handoff, 'missing private resume-PC push'
assert bytes.fromhex('23CF00004CEC') in handoff, 'missing transfer-SP observation'
assert bytes.fromhex('4E75') in handoff, 'missing task-stack RTS transfer'

assert bytes.fromhex('23CF00004CF0') in resume, 'missing resume-SP observation'
assert bytes.fromhex('23FC4C4B343200004CF4') in resume, 'missing arrival marker'
assert bytes.fromhex('46DF') in resume, 'missing final SR restore'
assert bytes.fromhex('2E7900004CE0') in resume, 'missing caller A7 restore'
assert resume.rfind(bytes.fromhex('46DF')) < resume.rfind(bytes.fromhex('2E7900004CE0')), 'SR restore must precede only MOVEA/RTS tail'
assert bytes.fromhex('4E75') in resume, 'missing caller RTS'

probe=data[0x5600:0x5800]
for value in (0x0000D7F0,0x0000D7C2,0x0000D7BE,0x0000D7EA,
              0x00004CE0,0x00004CE4,0x00004CE8,0x00004CEA,
              0x00004CEC,0x00004CF0,0x00004CF4,0x4C4B3432,
              0x42000002,0x0000E406):
    assert struct.pack('>I',value) in probe or value in (0x00004CE8,0x00004CEA), f'missing expected M2.42 value {value:08x}'
assert bytes.fromhex('4EB900F85800') in probe, 'missing integrated context handoff call'
assert bytes.fromhex('40F900004CEA') in probe, 'missing returned SR capture'
assert bytes.fromhex('303900004CE8B07900004CEA') in probe, 'missing SR roundtrip comparison'
assert bytes.fromhex('33FC00F000DFF180') in probe
assert bytes.fromhex('33FC000F00DFF18060FE') in probe

# M2.41 success gate must branch into M2.42 probe.
prev=data[0x5300:0x5500]; sig=bytes.fromhex('33FC00F000DFF1806000')
gp=prev.rfind(sig); assert gp>=0, 'M2.41 success gate missing'
branch_abs=0x5300+gp+8
disp=struct.unpack_from('>h',data,branch_abs+2)[0]
assert branch_abs+2+disp==0x5600, 'M2.41 gate does not branch to M2.42 probe'

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4):
    t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.42 check PASS: {p} ({len(data)} bytes)')
print('Exec integrated private register/SR/PC context-transfer qualification; checksum=0xffffffff')
