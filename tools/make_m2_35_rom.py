#!/usr/bin/env python3
"""Build LibreKick M2.35: internal ready-to-running task selection slice."""
from pathlib import Path
import struct, sys
import make_m2_34_rom as p
import make_m2_30_rom as t
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.35\0EXEC-DISPATCH-SELECT\0'
IDENT=b'exec.library\0LibreKick M2.35 ready-to-running selection slice 40.35\0'
PROBE_OFF=0x4000
PROBE_END=0x4200
DISPATCH_OFF=0x4200
DISPATCH_END=0x4240

# Classic 68k ExecBase layout.
THIS_TASK=m.EXEC_BASE+0x114
TS_RUN=2


def dispatch_code():
    """Internal scheduler foundation: select TaskReady head as current task.

    This is not exposed as Schedule(), Reschedule(), or Switch().  It removes
    one task from TaskReady, stores it in ExecBase->ThisTask and in the current
    task compatibility cell used by FindTask(NULL), and marks tc_State=TS_RUN.
    No CPU register/stack context switch is performed in M2.35.
    """
    q=bytearray()
    q+=bytes.fromhex('41F9')+struct.pack('>I',p.TASK_READY)  # a0=&TaskReady
    q+=bytes.fromhex('4EAEFEFE')                             # RemHead LVO -258
    q+=bytes.fromhex('4A80')                                 # tst.l d0
    q+=bytes.fromhex('6714')                                 # beq.s final RTS
    q+=bytes.fromhex('2240')                                 # a1=d0
    q+=bytes.fromhex('23C0')+struct.pack('>I',THIS_TASK)     # ThisTask=d0
    q+=bytes.fromhex('23C0')+struct.pack('>I',t.CURRENT_TASK_PTR)
    q+=bytes.fromhex('137C0002000F')                         # tc_State=TS_RUN
    q+=bytes.fromhex('4E75')                                 # RTS
    return bytes(q)


def build():
    image=bytearray(p.build())

    # Chain the corrected M2.34 success gate into M2.35.
    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0:
        raise ValueError('M2.34 final success gate not found')
    good_abs=p.PROBE_OFF+gp
    branch_pos=good_abs+8
    test_abs=PROBE_OFF

    routine=dispatch_code()
    if DISPATCH_OFF+len(routine)>DISPATCH_END:
        raise ValueError('M2.35 dispatcher exceeds dedicated ROM window')
    if any(b != 0xff for b in image[DISPATCH_OFF:DISPATCH_END]):
        raise ValueError('M2.35 dispatcher window is not unused')
    image[DISPATCH_OFF:DISPATCH_OFF+len(routine)]=routine

    c=bytearray(); fails=[]
    c+=bytes.fromhex('4DF9')+struct.pack('>I',m.EXEC_BASE)   # a6=ExecBase

    # M2.34 leaves TaskReady ordered B(pri7) -> A(pri2). Select the head.
    c+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+DISPATCH_OFF)
    fails.append(m.cmpd0(c,p.TASK_B))
    fails.append(m.cmpabs(c,p.TASK_B,THIS_TASK))
    fails.append(m.cmpabs(c,p.TASK_B,t.CURRENT_TASK_PTR))
    fails.append(m.cmpabs(c,0x00020000,p.TASK_B+14))         # tc_State=TS_RUN

    # Removing B must leave A as the sole TaskReady node.
    fails.append(m.cmpabs(c,p.TASK_A,p.TASK_READY+0))
    fails.append(m.cmpabs(c,p.TASK_A,p.TASK_READY+8))
    fails.append(m.cmpabs(c,p.TASK_READY+4,p.TASK_A+0))
    fails.append(m.cmpabs(c,p.TASK_READY+0,p.TASK_A+4))

    # Existing FindTask(NULL) must now resolve the selected task.
    c+=bytes.fromhex('227C00000000')                        # a1=NULL
    c+=bytes.fromhex('4EAEFEDA')                            # FindTask LVO -294
    fails.append(m.cmpd0(c,p.TASK_B))

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails:
        m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if test_abs+len(c)>PROBE_END:
        raise ValueError('M2.35 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[test_abs:test_abs+len(c)]):
        raise ValueError('M2.35 runtime probe window is not unused')
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
        raise SystemExit('usage: make_m2_35_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.35 ROM built: {out} ({len(data)} bytes)')
