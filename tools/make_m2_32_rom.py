#!/usr/bin/env python3
"""Build LibreKick M2.32: minimal Exec Signal current-task signal delivery slice."""
from pathlib import Path
import struct, sys
import make_m2_31_rom as p
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.32\0EXEC-SIGNAL-CURRENT\0'
IDENT=b'exec.library\0LibreKick M2.32 Signal current-task delivery slice 40.32\0'
PROBE_OFF=0x3600
PROBE_END=0x3800
SIGNAL_OFF=0x3800
SIGNAL_END=0x3840


def signal_code():
    """A1=task, D0=signalSet.

    M2.32 has exactly one bootstrap/current task, so this first Signal slice
    qualifies signal delivery to that task only. A1 is ABI-visible but task
    selection/scheduling is deferred until the task model grows beyond one task.
    """
    q=bytearray(bytes.fromhex('2F01'))                       # save d1
    q+=bytes.fromhex('2239')+struct.pack('>I',p.SIGNAL_CELL) # d1=current signals
    q+=bytes.fromhex('8280')                                 # d1 |= d0
    q+=bytes.fromhex('23C1')+struct.pack('>I',p.SIGNAL_CELL) # store new signals
    q+=bytes.fromhex('221F4E75')                             # restore d1; RTS
    return bytes(q)


def build():
    image=bytearray(p.build())

    # Chain the M2.31 success gate into the Signal probe.
    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0:
        raise ValueError('M2.31 final success gate not found')
    good_abs=p.PROBE_OFF+gp
    branch_pos=good_abs+8
    test_abs=PROBE_OFF

    routine=signal_code()
    if SIGNAL_OFF+len(routine)>SIGNAL_END:
        raise ValueError('M2.32 Signal routine exceeds dedicated ROM window')
    if any(b != 0xff for b in image[SIGNAL_OFF:SIGNAL_END]):
        raise ValueError('M2.32 Signal routine window is not unused')
    image[SIGNAL_OFF:SIGNAL_OFF+len(routine)]=routine

    c=bytearray(); fails=[]
    # Install Signal at Exec LVO -324 and reset the current-task signal state.
    c+=m.vector(m.ROM_BASE+SIGNAL_OFF,m.EXEC_BASE-324)
    c+=m.ml(0x00000010,p.SIGNAL_CELL)
    c+=bytes.fromhex('4DF9')+struct.pack('>I',m.EXEC_BASE)   # a6=ExecBase

    # Resolve the bootstrap current task through the already-qualified M2.30 API
    # and keep it in A1 for the Signal() calls.
    c+=bytes.fromhex('227C000000004EAEFEDA2240')           # FindTask(NULL); a1=d0
    fails.append(m.cmpabs(c,p.p.TASK_ADDR,p.p.CURRENT_TASK_PTR))

    def signal(mask,state_expect):
        nonlocal c
        c+=bytes.fromhex('203C')+struct.pack('>I',mask)
        c+=bytes.fromhex('4EAEFEBC')                         # Signal LVO -324
        fails.append(m.cmpabs(c,state_expect,p.SIGNAL_CELL))

    signal(0x00000005,0x00000015)
    signal(0x0000000A,0x0000001F)
    signal(0x80000000,0x8000001F)
    signal(0x00000000,0x8000001F)

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails:
        m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if test_abs+len(c)>PROBE_END:
        raise ValueError('M2.32 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[test_abs:test_abs+len(c)]):
        raise ValueError('M2.32 runtime probe window is not unused')
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
        raise SystemExit('usage: make_m2_32_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.32 ROM built: {out} ({len(data)} bytes)')
