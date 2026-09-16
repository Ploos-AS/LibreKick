#!/usr/bin/env python3
"""Build LibreKick M2.46 by converging private HandoffTaskStack into retained ROM."""
from __future__ import annotations
import struct, sys
from pathlib import Path
import make_m2_45_rom as previous
import make_m2_17_rom as runtime
from librekick_exec_abi import EXEC_BASE
from librekick_exec_runtime import THIS_TASK_OFF, TC_SPREG_OFF, handoff_task_stack_code, jsr_absolute

ROM_BASE=runtime.ROM_BASE
COLOR00=runtime.COLOR00
TASK_A=previous.a.TASK_A
HANDOFF_OFF=0x6700
HANDOFF_END=0x6800
PROBE_OFF=0x6800
PROBE_END=0x6900
RESUME_OFF=0x6900
RESUME_END=0x6A00
TASK_B=0x0000CA46
NEW_STACK_RETURN=0x0000D9F0
MARKER=b"LIBREKICK-M2.46\0SHARED-EXEC-TASK-STACK-HANDOFF\0"
IDENT=b"exec.library\0LibreKick M2.46 shared Exec task stack handoff 40.46\0"

def _ml(v,a): return bytes.fromhex("23fc")+struct.pack(">II",v,a)
def _cmp_l(v,a): return bytes.fromhex("0cb9")+struct.pack(">II",v,a)
def _cmp_d0(v): return bytes.fromhex("0c80")+struct.pack(">I",v)
def _move_d0(v): return bytes.fromhex("203c")+struct.pack(">I",v)
def _branch(c,op): p=len(c); c+=struct.pack(">HH",op,0); return p
def _patch(c,p,t): struct.pack_into(">h",c,p+2,t-(p+2))

def probe_code():
    c=bytearray(); bad=[]
    c+=_ml(0,TASK_A+TC_SPREG_OFF)
    c+=_ml(NEW_STACK_RETURN,TASK_B+TC_SPREG_OFF)
    c+=_ml(ROM_BASE+RESUME_OFF,NEW_STACK_RETURN)
    c+=_move_d0(TASK_B); c+=jsr_absolute(ROM_BASE+HANDOFF_OFF)
    c+=_cmp_d0(TASK_B); bad.append(_branch(c,0x6600))
    c+=_cmp_l(TASK_A,EXEC_BASE+THIS_TASK_OFF); bad.append(_branch(c,0x6600))
    c+=_cmp_l(NEW_STACK_RETURN,TASK_B+TC_SPREG_OFF); bad.append(_branch(c,0x6600))
    c+=_cmp_l(0,TASK_A+TC_SPREG_OFF); bad.append(_branch(c,0x6600))
    c+=bytes.fromhex("33fc00f000dff18060fe")
    fail=len(c); c+=bytes.fromhex("33fc000f00dff18060fe")
    for p in bad: _patch(c,p,fail)
    return bytes(c)

def resume_code():
    return jsr_absolute(ROM_BASE+HANDOFF_OFF)+bytes.fromhex("60fe")

def build():
    rom=bytearray(previous.build())
    helper=handoff_task_stack_code(); probe=probe_code(); resume=resume_code()
    for lo,hi in ((HANDOFF_OFF,HANDOFF_END),(PROBE_OFF,PROBE_END),(RESUME_OFF,RESUME_END)):
        if any(b != 0xFF for b in rom[lo:hi]): raise ValueError(f"M2.46 ROM window {lo:#x}..{hi:#x} is not free")
    if len(helper)>HANDOFF_END-HANDOFF_OFF or len(probe)>PROBE_END-PROBE_OFF or len(resume)>RESUME_END-RESUME_OFF: raise ValueError("M2.46 code exceeds dedicated ROM window")
    rom[HANDOFF_OFF:HANDOFF_OFF+len(helper)]=helper
    rom[PROBE_OFF:PROBE_OFF+len(probe)]=probe
    rom[RESUME_OFF:RESUME_OFF+len(resume)]=resume
    # M2.45 patches its successful green gate to a word-displacement BRA.W
    # into the local idle loop. Redirect that existing success edge into the
    # M2.46 stack-handoff probe. The displacement bytes are variable, so match
    # only the green write plus BRA.W opcode, as M2.45 itself does for M2.44.
    sig=bytes.fromhex("33fc00f000dff1806000")
    window=rom[previous.SWAP_PROBE_OFF:previous.SWAP_PROBE_END]
    rel=window.rfind(sig)
    if rel<0: raise ValueError("M2.45 success gate not found")
    branch=previous.SWAP_PROBE_OFF+rel+8
    disp=PROBE_OFF-(branch+2)
    struct.pack_into(">h",rom,branch+2,disp)
    # Retain deterministic identity in an unused area.
    meta=0x6A00
    if any(b != 0xFF for b in rom[meta:meta+0x100]): raise ValueError("M2.46 metadata window not free")
    rom[meta:meta+len(MARKER)]=MARKER
    rom[meta+0x60:meta+0x60+len(IDENT)]=IDENT
    # Replace the inherited milestone identity as well, matching M2.45 policy.
    rom[runtime.MARKER_OFF:runtime.IDENT_OFF]=b"\xff"*(runtime.IDENT_OFF-runtime.MARKER_OFF)
    rom[runtime.MARKER_OFF:runtime.MARKER_OFF+len(MARKER)]=MARKER
    rom[runtime.IDENT_OFF:runtime.NAME_A_OFF]=b"\xff"*(runtime.NAME_A_OFF-runtime.IDENT_OFF)
    rom[runtime.IDENT_OFF:runtime.IDENT_OFF+len(IDENT)]=IDENT
    struct.pack_into(">I",rom,runtime.ROM_SIZE-4,0)
    total=0
    for off in range(0,runtime.ROM_SIZE-4,4):
        total=runtime.ones(total,struct.unpack_from(">I",rom,off)[0])
    total=(total&0xffffffff)+(total>>32)
    struct.pack_into(">I",rom,runtime.ROM_SIZE-4,(~total)&0xffffffff)
    return bytes(rom)

def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else "build/librekick-m2_46.rom"); out.parent.mkdir(parents=True,exist_ok=True); data=build(); out.write_bytes(data)
    print(f"M2.46 ROM built: {out} ({len(data)} bytes)")
    print("shared_primitives=GetSysBase,GetCurrentTask,SetCurrentTask,SwapCurrentTask,HandoffTaskStack")
    print("scope=private cooperative stack handoff; complete register/SR context switch and public Exec scheduler not claimed")
if __name__=="__main__": main()
