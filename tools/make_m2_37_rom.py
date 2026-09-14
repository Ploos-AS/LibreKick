#!/usr/bin/env python3
"""Build LibreKick M2.37: controlled A7 stack handoff primitive."""
from pathlib import Path
import struct, sys
import make_m2_36_rom as p
import make_m2_34_rom as a
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.37\0EXEC-CONTEXT-A7\0'
IDENT=b'exec.library\0LibreKick M2.37 controlled A7 stack handoff slice 40.37\0'
PROBE_OFF=0x4600
PROBE_END=0x4800
HANDOFF_OFF=0x4800
HANDOFF_END=0x4840

ORIGINAL_SP_CELL=0x00004C1C
OBSERVED_SP_CELL=0x00004C20
STACK_MARKER=0x4C4B3737


def handoff_code():
    """Temporarily hand A7 to ThisTask->tc_SPReg, exercise it, then restore.

    This is intentionally still not a general task context switch. The helper
    stores the caller A7, loads the selected task's tc_SPReg into A7, performs
    one predecrement stack write, records the resulting A7, restores the
    original A7, and returns normally to the caller.
    """
    q=bytearray()
    q+=bytes.fromhex('2279')+struct.pack('>I',p.p.THIS_TASK)       # a1=ThisTask
    q+=bytes.fromhex('2029')+struct.pack('>H',p.TC_SPREG)         # d0=tc_SPReg
    q+=bytes.fromhex('23CF')+struct.pack('>I',ORIGINAL_SP_CELL)   # save caller a7
    q+=bytes.fromhex('2E40')                                      # a7=d0
    q+=bytes.fromhex('2F3C')+struct.pack('>I',STACK_MARKER)       # marker,-(a7)
    q+=bytes.fromhex('23CF')+struct.pack('>I',OBSERVED_SP_CELL)   # observed switched a7
    q+=bytes.fromhex('2E79')+struct.pack('>I',ORIGINAL_SP_CELL)   # restore caller a7
    q+=bytes.fromhex('4E75')                                      # RTS on restored stack
    return bytes(q)


def build():
    image=bytearray(p.build())

    # Chain M2.36's qualified success path into the first real A7 handoff probe.
    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0:
        raise ValueError('M2.36 final success gate not found')
    good_abs=p.PROBE_OFF+gp
    branch_pos=good_abs+8
    test_abs=PROBE_OFF

    routine=handoff_code()
    if HANDOFF_OFF+len(routine)>HANDOFF_END:
        raise ValueError('M2.37 handoff helper exceeds dedicated ROM window')
    if any(b != 0xff for b in image[HANDOFF_OFF:HANDOFF_END]):
        raise ValueError('M2.37 handoff helper window is not unused')
    image[HANDOFF_OFF:HANDOFF_OFF+len(routine)]=routine

    c=bytearray(); fails=[]

    # Task B is still ThisTask from M2.35. Use a safe RAM stack range already
    # established by M2.36 and prove that A7 really operates on tc_SPReg.
    c+=m.ml(0x0000D000,a.TASK_B+p.TC_SPLOWER)
    c+=m.ml(0x0000D800,a.TASK_B+p.TC_SPUPPER)
    c+=m.ml(0x0000D7F0,a.TASK_B+p.TC_SPREG)
    c+=m.ml(0x00000000,0x0000D7EC)
    c+=m.ml(0x00000000,ORIGINAL_SP_CELL)
    c+=m.ml(0x00000000,OBSERVED_SP_CELL)

    c+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+HANDOFF_OFF)
    fails.append(m.cmpd0(c,0x0000D7F0))
    fails.append(m.cmpabs(c,STACK_MARKER,0x0000D7EC))
    fails.append(m.cmpabs(c,0x0000D7EC,OBSERVED_SP_CELL))
    fails.append(m.cmpabs(c,a.TASK_B,p.p.THIS_TASK))
    fails.append(m.cmpabs(c,0x0000D7F0,a.TASK_B+p.TC_SPREG))

    # Repeat at another SP. Returning to the probe twice is also runtime proof
    # that the caller A7 was restored before RTS.
    c+=m.ml(0x0000D6C0,a.TASK_B+p.TC_SPREG)
    c+=m.ml(0x00000000,0x0000D6BC)
    c+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+HANDOFF_OFF)
    fails.append(m.cmpd0(c,0x0000D6C0))
    fails.append(m.cmpabs(c,STACK_MARKER,0x0000D6BC))
    fails.append(m.cmpabs(c,0x0000D6BC,OBSERVED_SP_CELL))

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails:
        m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if test_abs+len(c)>PROBE_END:
        raise ValueError('M2.37 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[test_abs:test_abs+len(c)]):
        raise ValueError('M2.37 runtime probe window is not unused')
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
        raise SystemExit('usage: make_m2_37_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.37 ROM built: {out} ({len(data)} bytes)')
