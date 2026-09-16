#!/usr/bin/env python3
"""Build LibreKick M2.45: cross-profile shared Exec task-swap convergence."""
from pathlib import Path
import struct, sys
import make_m2_44_rom as p
import make_m2_34_rom as a
import make_m2_17_rom as m
from librekick_exec_abi import EXEC_BASE
from librekick_exec_runtime import THIS_TASK_OFF, swap_current_task_code, jsr_absolute

MARKER=b'LIBREKICK-M2.45\0SHARED-EXEC-TASK-SWAP-RUNTIME\0'
IDENT=b'exec.library\0LibreKick M2.45 shared Exec task swap runtime 40.45\0'
SWAPCURRENTTASK_OFF=0x6500
SWAPCURRENTTASK_END=0x6600
SWAP_PROBE_OFF=0x6600
SWAP_PROBE_END=0x6700
TASK_SENTINEL=0x0000C945


def build():
    image=bytearray(p.build())
    code=swap_current_task_code()
    if SWAPCURRENTTASK_OFF+len(code)>SWAPCURRENTTASK_END:
        raise ValueError('M2.45 SwapCurrentTask helper exceeds dedicated ROM window')
    if any(b!=0xff for b in image[SWAPCURRENTTASK_OFF:SWAPCURRENTTASK_END]):
        raise ValueError('M2.45 SwapCurrentTask helper window is not unused')
    image[SWAPCURRENTTASK_OFF:SWAPCURRENTTASK_OFF+len(code)]=code

    # M2.44 ends its successful task-state probe with green + BRA to idle.
    # Redirect only that success edge into the M2.45 swap probe.
    old=image[p.TASK_PROBE_OFF:p.TASK_PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=old.rfind(sig)
    if gp<0:
        raise ValueError('M2.44 final success gate not found')
    branch_abs=p.TASK_PROBE_OFF+gp+8

    if any(b!=0xff for b in image[SWAP_PROBE_OFF:SWAP_PROBE_END]):
        raise ValueError('M2.45 swap probe window is not unused')

    c=bytearray(); fails=[]
    # M2.44 restores TASK_A before entering here. Swap to a sentinel and require
    # the primitive to return the old TASK_A pointer in D0.
    c+=bytes.fromhex('203C')+struct.pack('>I',TASK_SENTINEL)
    c+=jsr_absolute(m.ROM_BASE+SWAPCURRENTTASK_OFF)
    c+=bytes.fromhex('0C80')+struct.pack('>I',a.TASK_A)
    fails.append(m.branch(c,0x6600))
    c+=bytes.fromhex('0CB9')+struct.pack('>I',TASK_SENTINEL)+struct.pack('>I',EXEC_BASE+THIS_TASK_OFF)
    fails.append(m.branch(c,0x6600))

    # Swap back to TASK_A. The returned old pointer must be the sentinel and
    # ExecBase->ThisTask must again contain TASK_A.
    c+=bytes.fromhex('203C')+struct.pack('>I',a.TASK_A)
    c+=jsr_absolute(m.ROM_BASE+SWAPCURRENTTASK_OFF)
    c+=bytes.fromhex('0C80')+struct.pack('>I',TASK_SENTINEL)
    fails.append(m.branch(c,0x6600))
    c+=bytes.fromhex('0CB9')+struct.pack('>I',a.TASK_A)+struct.pack('>I',EXEC_BASE+THIS_TASK_OFF)
    fails.append(m.branch(c,0x6600))

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails: m.patch(c,fail,bad)
    m.patch(c,ok,idle)
    if SWAP_PROBE_OFF+len(c)>SWAP_PROBE_END:
        raise ValueError(f'M2.45 runtime probe exceeds dedicated ROM window ({len(c)} bytes)')
    image[SWAP_PROBE_OFF:SWAP_PROBE_OFF+len(c)]=c
    struct.pack_into('>h',image,branch_abs+2,SWAP_PROBE_OFF-(branch_abs+2))

    image[m.MARKER_OFF:m.IDENT_OFF]=b'\xff'*(m.IDENT_OFF-m.MARKER_OFF)
    image[m.MARKER_OFF:m.MARKER_OFF+len(MARKER)]=MARKER
    image[m.IDENT_OFF:m.NAME_A_OFF]=b'\xff'*(m.NAME_A_OFF-m.IDENT_OFF)
    image[m.IDENT_OFF:m.IDENT_OFF+len(IDENT)]=IDENT
    struct.pack_into('>I',image,m.ROM_SIZE-4,0)
    total=0
    for off in range(0,m.ROM_SIZE-4,4):
        total=m.ones(total,struct.unpack_from('>I',image,off)[0])
    total=(total&0xffffffff)+(total>>32)
    struct.pack_into('>I',image,m.ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_45_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.45 ROM built: {out} ({len(data)} bytes)')
    print('shared_primitives=GetSysBase,GetCurrentTask,SetCurrentTask,SwapCurrentTask')
