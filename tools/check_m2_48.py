#!/usr/bin/env python3
"""Static validation for LibreKick M2.48."""
from pathlib import Path
import struct, sys
import make_m2_48_rom as b


def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)


def main():
    p=Path(sys.argv[1] if len(sys.argv)>1 else 'build/librekick-m2_48.rom')
    data=p.read_bytes()
    assert len(data)==512*1024
    sw=b.switch_code(); tb=b.task_b_code(); probe=b.probe_code()
    assert data[b.SWITCH_OFF:b.SWITCH_OFF+len(sw)]==sw
    assert data[b.TASK_B_ENTRY_OFF:b.TASK_B_ENTRY_OFF+len(tb)]==tb
    assert data[b.PROBE_OFF:b.PROBE_OFF+len(probe)]==probe
    assert b.MARKER in data and b.IDENT in data
    assert b.TASK_A != b.TASK_B
    assert b.STACK_A_TOP != b.STACK_B_TOP
    assert b.D_REGS==list(range(2,8)) and b.A_REGS==list(range(2,7))
    assert bytes.fromhex('40e7') in sw and bytes.fromhex('46df') in sw
    assert struct.pack('>I',b.EXEC_BASE+b.THIS_TASK_OFF) in sw
    assert struct.pack('>H',b.TC_SPREG_OFF) in sw
    assert struct.pack('>I',b.B_MAGIC) in probe
    assert struct.pack('>I',b.A_MAGIC) in probe
    assert bytes.fromhex('33fc00f000dff180') in probe
    assert bytes.fromhex('33fc000f00dff180') in probe
    t=0
    for off in range(0,len(data),4):
        t=ones(t,struct.unpack_from('>I',data,off)[0])
    t=(t&0xffffffff)+(t>>32)
    assert t==0xffffffff, f'bad checksum {t:08x}'
    print(f'M2.48 check PASS: {p} ({len(data)} bytes)')
    print(f'switch=${b.ROM_BASE+b.SWITCH_OFF:08x} task_b=${b.ROM_BASE+b.TASK_B_ENTRY_OFF:08x} probe=${b.ROM_BASE+b.PROBE_OFF:08x}')
    print('context=SR,D2-D7,A2-A6,tc_SPReg; tasks=A,B; checksum=0xffffffff')
    print('scope=private deterministic two-task switch; public Exec scheduler not claimed')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
