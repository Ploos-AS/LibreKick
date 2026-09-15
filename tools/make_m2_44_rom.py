#!/usr/bin/env python3
"""Build LibreKick M2.44: cross-profile shared Exec task-runtime convergence."""
from pathlib import Path
import struct, sys
import make_m2_43_rom as p
import make_m2_34_rom as a
import make_m2_17_rom as m
from librekick_exec_abi import EXEC_BASE
from librekick_exec_runtime import (
    THIS_TASK_OFF,
    get_current_task_code,
    set_current_task_code,
    jsr_absolute,
)

MARKER=b'LIBREKICK-M2.44\0SHARED-EXEC-TASK-RUNTIME\0'
IDENT=b'exec.library\0LibreKick M2.44 shared Exec task runtime 40.44\0'
GETCURRENTTASK_OFF=0x6200
GETCURRENTTASK_END=0x6300
SETCURRENTTASK_OFF=0x6300
SETCURRENTTASK_END=0x6400
TASK_SENTINEL=0x0000C844


def build():
    image=bytearray(p.build())

    blocks=((GETCURRENTTASK_OFF,GETCURRENTTASK_END,get_current_task_code()),
            (SETCURRENTTASK_OFF,SETCURRENTTASK_END,set_current_task_code()))
    for lo,hi,code in blocks:
        if lo+len(code)>hi:
            raise ValueError('M2.44 helper exceeds dedicated ROM window')
        if any(b!=0xff for b in image[lo:hi]):
            raise ValueError('M2.44 ROM helper window is not unused')
        image[lo:lo+len(code)]=code

    # M2.43 ends its successful prepared-task/GetSysBase path with a green
    # diagnostic followed by BRA to its idle loop. Redirect that successful
    # branch into a fresh unused part of the same probe window. This preserves
    # all M2.43 failure branches and adds the shared task-state gate afterwards.
    probe=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=probe.rfind(sig)
    if gp<0:
        raise ValueError('M2.43 final success gate not found')
    branch_abs=p.PROBE_OFF+gp+8
    old_disp=struct.unpack_from('>h',image,branch_abs+2)[0]
    old_idle=branch_abs+2+old_disp

    # Place the extension after the old idle instruction and before untouched FF.
    ext_off=old_idle+2
    if ext_off>=p.PROBE_END or any(b!=0xff for b in image[ext_off:p.PROBE_END]):
        raise ValueError('M2.44 probe extension window is not unused')

    c=bytearray(); fails=[]

    # The M2.43 activation path leaves TASK_A as the real current task. Verify
    # that the shared GetCurrentTask primitive observes that existing state.
    c+=jsr_absolute(m.ROM_BASE+GETCURRENTTASK_OFF)
    c+=bytes.fromhex('0C80')+struct.pack('>I',a.TASK_A)
    fails.append(m.branch(c,0x6600))

    # Exercise shared SetCurrentTask with a controlled sentinel, read it back
    # through the shared getter, then restore TASK_A before completing M2.44.
    c+=bytes.fromhex('203C')+struct.pack('>I',TASK_SENTINEL)
    c+=jsr_absolute(m.ROM_BASE+SETCURRENTTASK_OFF)
    c+=jsr_absolute(m.ROM_BASE+GETCURRENTTASK_OFF)
    c+=bytes.fromhex('0C80')+struct.pack('>I',TASK_SENTINEL)
    fails.append(m.branch(c,0x6600))

    c+=bytes.fromhex('203C')+struct.pack('>I',a.TASK_A)
    c+=jsr_absolute(m.ROM_BASE+SETCURRENTTASK_OFF)
    c+=jsr_absolute(m.ROM_BASE+GETCURRENTTASK_OFF)
    c+=bytes.fromhex('0C80')+struct.pack('>I',a.TASK_A)
    fails.append(m.branch(c,0x6600))

    # Also verify the restored state directly at ExecBase->ThisTask.
    c+=bytes.fromhex('0CB9')+struct.pack('>I',a.TASK_A)+struct.pack('>I',EXEC_BASE+THIS_TASK_OFF)
    fails.append(m.branch(c,0x6600))

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails: m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if ext_off+len(c)>p.PROBE_END:
        raise ValueError(f'M2.44 runtime probe exceeds dedicated ROM window ({len(c)} extension bytes)')
    image[ext_off:ext_off+len(c)]=c
    struct.pack_into('>h',image,branch_abs+2,ext_off-(branch_abs+2))

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
    if len(sys.argv)!=2:
        raise SystemExit('usage: make_m2_44_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.44 ROM built: {out} ({len(data)} bytes)')
    print('shared_primitives=GetSysBase,GetCurrentTask,SetCurrentTask')
