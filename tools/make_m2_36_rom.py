#!/usr/bin/env python3
"""Build LibreKick M2.36: current-task stack-context handoff foundation."""
from pathlib import Path
import struct, sys
import make_m2_35_rom as p
import make_m2_34_rom as a
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.36\0EXEC-CONTEXT-SP\0'
IDENT=b'exec.library\0LibreKick M2.36 current-task stack-context handoff slice 40.36\0'
PROBE_OFF=0x4300
PROBE_END=0x4500
CONTEXT_OFF=0x4500
CONTEXT_END=0x4540

# Classic 68k Task layout. Public AddTask documentation requires callers to
# initialise tc_SPReg/tc_SPLower/tc_SPUpper before adding a task.
TC_SPREG=0x36
TC_SPLOWER=0x3A
TC_SPUPPER=0x3E
NEXT_SP_CELL=0x00004C18


def context_code():
    """Internal handoff: capture ThisTask->tc_SPReg as the next stack pointer.

    This is intentionally not a context switch. M2.36 does not write A7, save
    registers, restore registers, or transfer execution to another task.
    """
    q=bytearray()
    q+=bytes.fromhex('2279')+struct.pack('>I',p.THIS_TASK)      # a1=ThisTask
    q+=bytes.fromhex('2029')+struct.pack('>H',TC_SPREG)         # d0=tc_SPReg
    q+=bytes.fromhex('23C0')+struct.pack('>I',NEXT_SP_CELL)     # shadow next SP
    q+=bytes.fromhex('4E75')                                    # RTS
    return bytes(q)


def build():
    image=bytearray(p.build())

    # Chain M2.35's qualified success path into the context-metadata probe.
    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0:
        raise ValueError('M2.35 final success gate not found')
    good_abs=p.PROBE_OFF+gp
    branch_pos=good_abs+8
    test_abs=PROBE_OFF

    routine=context_code()
    if CONTEXT_OFF+len(routine)>CONTEXT_END:
        raise ValueError('M2.36 context helper exceeds dedicated ROM window')
    if any(b != 0xff for b in image[CONTEXT_OFF:CONTEXT_END]):
        raise ValueError('M2.36 context helper window is not unused')
    image[CONTEXT_OFF:CONTEXT_OFF+len(routine)]=routine

    c=bytearray(); fails=[]

    # M2.35 selected task B as ThisTask. Supply valid classic Task stack
    # metadata and prove the context helper follows ThisTask->tc_SPReg.
    c+=m.ml(0x0000D000,a.TASK_B+TC_SPLOWER)
    c+=m.ml(0x0000D800,a.TASK_B+TC_SPUPPER)
    c+=m.ml(0x0000D7F0,a.TASK_B+TC_SPREG)
    c+=m.ml(0x00000000,NEXT_SP_CELL)

    c+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+CONTEXT_OFF)
    fails.append(m.cmpd0(c,0x0000D7F0))
    fails.append(m.cmpabs(c,0x0000D7F0,NEXT_SP_CELL))
    fails.append(m.cmpabs(c,a.TASK_B,p.THIS_TASK))

    # A second capture proves this is a live Task field handoff, not a fixed
    # test constant baked into the helper.
    c+=m.ml(0x0000D6C0,a.TASK_B+TC_SPREG)
    c+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+CONTEXT_OFF)
    fails.append(m.cmpd0(c,0x0000D6C0))
    fails.append(m.cmpabs(c,0x0000D6C0,NEXT_SP_CELL))

    # Existing FindTask(NULL) remains consistent with ExecBase->ThisTask.
    c+=bytes.fromhex('4DF9')+struct.pack('>I',m.EXEC_BASE)
    c+=bytes.fromhex('227C000000004EAEFEDA')
    fails.append(m.cmpd0(c,a.TASK_B))

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails:
        m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if test_abs+len(c)>PROBE_END:
        raise ValueError('M2.36 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[test_abs:test_abs+len(c)]):
        raise ValueError('M2.36 runtime probe window is not unused')
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
        raise SystemExit('usage: make_m2_36_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.36 ROM built: {out} ({len(data)} bytes)')
