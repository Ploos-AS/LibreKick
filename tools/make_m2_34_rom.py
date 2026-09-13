#!/usr/bin/env python3
"""Build LibreKick M2.34: minimal Exec AddTask ready-list registration slice."""
from pathlib import Path
import struct, sys
import make_m2_33_rom as p
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.34\0EXEC-ADDTASK-READY\0'
IDENT=b'exec.library\0LibreKick M2.34 AddTask ready-list registration slice 40.34\0'
PROBE_OFF=0x3C00
PROBE_END=0x3E00
ADDTASK_OFF=0x3E00
ADDTASK_END=0x3E40

# Classic 68k ExecBase layout: ThisTask=$114, TaskReady=$196, TaskWait=$1A4.
TASK_READY=m.EXEC_BASE+0x196
TASK_A=0x0000C100
TASK_B=0x0000C200
TS_READY=3
NT_TASK=1


def addtask_code():
    """A1=task, A2=initialPC, A3=finalPC -> D0=task.

    M2.34 intentionally qualifies only registration of a prepared Task node on
    ExecBase->TaskReady, priority ordered via the already-qualified Enqueue().
    It does not create an initial CPU context, launch the task, or reschedule.
    """
    q=bytearray()
    q+=bytes.fromhex('41F9')+struct.pack('>I',TASK_READY)    # a0=&TaskReady
    q+=bytes.fromhex('4EAEFEF2')                            # Enqueue LVO -270
    q+=bytes.fromhex('137C0003000F')                        # tc_State=TS_READY
    q+=bytes.fromhex('20094E75')                            # d0=a1; RTS
    return bytes(q)


def build():
    image=bytearray(p.build())

    # Chain M2.33 success into the first scheduler/task-list foundation slice.
    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0:
        raise ValueError('M2.33 final success gate not found')
    good_abs=p.PROBE_OFF+gp
    branch_pos=good_abs+8
    test_abs=PROBE_OFF

    routine=addtask_code()
    if ADDTASK_OFF+len(routine)>ADDTASK_END:
        raise ValueError('M2.34 AddTask routine exceeds dedicated ROM window')
    if any(b != 0xff for b in image[ADDTASK_OFF:ADDTASK_END]):
        raise ValueError('M2.34 AddTask routine window is not unused')
    image[ADDTASK_OFF:ADDTASK_OFF+len(routine)]=routine

    c=bytearray(); fails=[]
    c+=m.vector(m.ROM_BASE+ADDTASK_OFF,m.EXEC_BASE-282)
    c+=bytes.fromhex('4DF9')+struct.pack('>I',m.EXEC_BASE)   # a6=ExecBase

    # NewList(&SysBase->TaskReady), with NT_TASK list type.
    c+=m.ml(TASK_READY+4,TASK_READY+0)
    c+=m.ml(0,TASK_READY+4)
    c+=m.ml(TASK_READY+0,TASK_READY+8)
    c+=m.mw(0x0100,TASK_READY+12)

    def init_task(addr,pri):
        nonlocal c
        c+=m.ml(0,addr+0)
        c+=m.ml(0,addr+4)
        c+=m.mw((NT_TASK<<8)|(pri & 0xff),addr+8)
        c+=m.ml(0,addr+10)                                  # ln_Name=NULL in probe
        c+=m.ml(0,addr+14)                                  # flags/state/nesting

    init_task(TASK_A,2)
    init_task(TASK_B,7)

    def add_task(addr,initial,final):
        nonlocal c
        c+=bytes.fromhex('43F9')+struct.pack('>I',addr)      # a1=task
        c+=bytes.fromhex('45F9')+struct.pack('>I',initial)   # a2=initialPC (ABI-visible)
        c+=bytes.fromhex('47F9')+struct.pack('>I',final)     # a3=finalPC (ABI-visible)
        c+=bytes.fromhex('4EAEFEE6')                         # AddTask LVO -282
        fails.append(m.cmpd0(c,addr))
        fails.append(m.cmpabs(c,0x00030000,addr+14))         # tc_State == TS_READY

    # Lower-priority task first, then higher-priority task. AddTask must use the
    # existing priority-sorted Enqueue behavior for TaskReady.
    add_task(TASK_A,0x00F83F00,0x00F83F10)
    fails.append(m.cmpabs(c,TASK_A,TASK_READY+0))
    fails.append(m.cmpabs(c,TASK_A,TASK_READY+8))
    fails.append(m.cmpabs(c,TASK_READY+4,TASK_A+0))
    fails.append(m.cmpabs(c,TASK_READY+0,TASK_A+4))

    add_task(TASK_B,0x00F83F20,0x00F83F30)
    fails.append(m.cmpabs(c,TASK_B,TASK_READY+0))
    fails.append(m.cmpabs(c,TASK_A,TASK_READY+8))
    fails.append(m.cmpabs(c,TASK_A,TASK_B+0))
    fails.append(m.cmpabs(c,TASK_READY+0,TASK_B+4))
    fails.append(m.cmpabs(c,TASK_READY+4,TASK_A+0))
    fails.append(m.cmpabs(c,TASK_B,TASK_A+4))

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails:
        m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if test_abs+len(c)>PROBE_END:
        raise ValueError('M2.34 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[test_abs:test_abs+len(c)]):
        raise ValueError('M2.34 runtime probe window is not unused')
    image[test_abs:test_abs+len(c)]=c
    struct.pack_into('>h',image,branch_pos+2,test_abs-(branch_pos+2))

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
        raise SystemExit('usage: make_m2_34_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.34 ROM built: {out} ({len(data)} bytes)')
