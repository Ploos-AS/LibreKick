#!/usr/bin/env python3
"""Static validation for LibreKick M2.49 private ready-list dispatch."""
from pathlib import Path
import struct, sys
import make_m2_49_rom as b
import make_m2_17_rom as runtime
from librekick_exec_abi import EXEC_BASE
from librekick_exec_runtime import THIS_TASK_OFF, TC_SPREG_OFF

def main():
    path=Path(sys.argv[1] if len(sys.argv)>1 else 'build/librekick-m2_49.rom')
    rom=path.read_bytes()
    assert len(rom)==runtime.ROM_SIZE
    assert b.MARKER in rom and b.IDENT in rom
    disp=b.dispatch_code(); tb=b.task_b_code(); probe=b.probe_code()
    assert rom[b.DISPATCH_OFF:b.DISPATCH_OFF+len(disp)]==disp
    assert rom[b.TASK_B_ENTRY_OFF:b.TASK_B_ENTRY_OFF+len(tb)]==tb
    assert rom[b.PROBE_OFF:b.PROBE_OFF+len(probe)]==probe
    assert struct.pack('>I',b.READY_TASK) in disp
    assert struct.pack('>I',EXEC_BASE+THIS_TASK_OFF) in disp
    assert struct.pack('>H',TC_SPREG_OFF) in disp
    assert bytes.fromhex('2079')+struct.pack('>I',b.READY_TASK) in disp
    assert struct.pack('>I',b.TASK_B) not in disp
    assert struct.pack('>I',b.TASK_B) in probe
    assert struct.pack('>I',b.TASK_A) in probe
    assert struct.pack('>I',b.B_MAGIC) in tb and struct.pack('>I',b.B_MAGIC) in probe
    assert bytes.fromhex('40e7') in disp and bytes.fromhex('46df') in disp
    frame=b.prepared_frame(b.ROM_BASE+b.TASK_B_ENTRY_OFF,b.B_D,b.B_A)
    for r in b.D_REGS: assert struct.pack('>I',b.B_D[r]) in frame
    for r in b.A_REGS: assert struct.pack('>I',b.B_A[r]) in frame
    total=0
    for off in range(0,len(rom),4):
        total=runtime.ones(total,struct.unpack_from('>I',rom,off)[0])
    total=(total&0xffffffff)+(total>>32)
    assert total==0xffffffff, hex(total)
    print(f'M2.49 check PASS: {path} ({len(rom)} bytes)')
    print(f'dispatch={b.ROM_BASE+b.DISPATCH_OFF:#010x} ready_state={b.READY_TASK:#010x}')
    print('context=SR,D2-D7,A2-A6,tc_SPReg; selection=private ready state')
    print('checksum=0xffffffff')
    print('scope=private ready-list dispatch; public Exec scheduler not claimed')
    return 0
if __name__=='__main__': raise SystemExit(main())
