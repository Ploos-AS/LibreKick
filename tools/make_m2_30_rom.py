#!/usr/bin/env python3
"""Build LibreKick M2.30: minimal Exec FindTask(NULL) current-task slice."""
from pathlib import Path
import struct, sys
import make_m2_29_rom as p
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.30\0EXEC-FINDTASK-CURRENT\0'
IDENT=b'exec.library\0LibreKick M2.30 FindTask current-task slice 40.30\0'
PROBE_OFF=0x3000
PROBE_END=0x3200
FINDTASK_OFF=0x3200
FINDTASK_END=0x3240
CURRENT_TASK_PTR=0x00004C10
TASK_ADDR=0x0000C000
TASK_NAME_OFF=0x3280
TASK_NAME_ADDR=m.ROM_BASE+TASK_NAME_OFF


def findtask_code():
    """A1=name. M2.30 qualifies only name==NULL -> current task."""
    q=bytearray(bytes.fromhex('20094A80'))
    current=m.branch(q,0x6700)
    q+=bytes.fromhex('70004E75')               # named lookup not implemented yet
    cur=len(q)
    q+=bytes.fromhex('2039')+struct.pack('>I',CURRENT_TASK_PTR)+bytes.fromhex('4E75')
    m.patch(q,current,cur)
    return bytes(q)


def build():
    image=bytearray(p.build())

    # Chain M2.29 success into the first tasking slice.
    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0: raise ValueError('M2.29 final success gate not found')
    good_abs=p.PROBE_OFF+gp; branch_pos=good_abs+8
    test_abs=PROBE_OFF

    routine=findtask_code()
    if FINDTASK_OFF+len(routine)>FINDTASK_END:
        raise ValueError('M2.30 FindTask routine exceeds dedicated ROM window')
    if any(b != 0xff for b in image[FINDTASK_OFF:FINDTASK_END]):
        raise ValueError('M2.30 FindTask routine window is not unused')
    image[FINDTASK_OFF:FINDTASK_OFF+len(routine)]=routine

    c=bytearray(); fails=[]
    # Install the public Exec vector at LVO -294 and establish a minimal
    # bootstrap current-task pointer. The Task structure itself is deliberately
    # only a sentinel in this slice; later task milestones will populate it.
    c+=m.vector(m.ROM_BASE+FINDTASK_OFF,m.EXEC_BASE-294)
    c+=m.ml(TASK_ADDR,CURRENT_TASK_PTR)
    c+=m.ml(TASK_NAME_ADDR,TASK_ADDR+10)

    # FindTask(NULL) must return the current task pointer.
    c+=bytes.fromhex('227C000000004EAEFEDA')
    fails.append(m.cmpd0(c,TASK_ADDR))

    # Named lookup is intentionally outside this slice and must fail cleanly.
    c+=bytes.fromhex('43F9')+struct.pack('>I',TASK_NAME_ADDR)+bytes.fromhex('4EAEFEDA4A80')
    named_nonnull=m.branch(c,0x6600); fails.append(named_nonnull)

    # Re-check NULL after the unsupported named query to prove current-task
    # state remains intact.
    c+=bytes.fromhex('227C000000004EAEFEDA')
    fails.append(m.cmpd0(c,TASK_ADDR))

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails: m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if test_abs+len(c)>PROBE_END:
        raise ValueError('M2.30 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[test_abs:test_abs+len(c)]):
        raise ValueError('M2.30 runtime probe window is not unused')
    image[test_abs:test_abs+len(c)]=c
    struct.pack_into('>h',image,branch_pos+2,test_abs-(branch_pos+2))

    name=b'LibreKick bootstrap task\0'
    if TASK_NAME_OFF+len(name)>=m.ROM_SIZE-4:
        raise ValueError('M2.30 task name outside ROM')
    image[TASK_NAME_OFF:TASK_NAME_OFF+len(name)]=name

    image[m.MARKER_OFF:m.IDENT_OFF]=b'\xff'*(m.IDENT_OFF-m.MARKER_OFF)
    image[m.MARKER_OFF:m.MARKER_OFF+len(MARKER)]=MARKER
    image[m.IDENT_OFF:m.NAME_A_OFF]=b'\xff'*(m.NAME_A_OFF-m.IDENT_OFF)
    image[m.IDENT_OFF:m.IDENT_OFF+len(IDENT)]=IDENT

    struct.pack_into('>I',image,m.ROM_SIZE-4,0); total=0
    for off in range(0,m.ROM_SIZE-4,4): total=m.ones(total,struct.unpack_from('>I',image,off)[0])
    total=(total&0xffffffff)+(total>>32)
    struct.pack_into('>I',image,m.ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_30_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.30 ROM built: {out} ({len(data)} bytes)')
