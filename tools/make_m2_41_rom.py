#!/usr/bin/env python3
"""Build LibreKick M2.41: private task-stack PC resume handoff primitive."""
from pathlib import Path
import struct, sys
import make_m2_40_rom as p
import make_m2_34_rom as a
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.41\0EXEC-CONTEXT-PC-RESUME\0'
IDENT=b'exec.library\0LibreKick M2.41 private PC resume handoff slice 40.41\0'
PROBE_OFF=0x5300
PROBE_END=0x5500
HANDOFF_OFF=0x5500
HANDOFF_END=0x5580
RESUME_OFF=0x5580
RESUME_END=0x55C0

ORIGINAL_SP_CELL=0x00004CC0
FRAME_SP_CELL=0x00004CC4
RESUME_SP_CELL=0x00004CC8
CALLER_PC_CELL=0x00004CCC
ARRIVED_CELL=0x00004CD0
ARRIVED_MAGIC=0x4C4B3431


def handoff_code():
    """Transfer PC through a synthetic resume address on ThisTask's stack.

    Entry is by JSR on the caller stack. The helper remembers the caller A7 and
    JSR return PC, switches A7 to ThisTask->tc_SPReg, pushes the private resume
    stub address, and executes RTS. RTS therefore obtains its next PC from the
    task stack. The resume stub proves arrival, restores the caller A7 and RTSes
    through the original JSR return address.

    This is intentionally not an Exec-compatible scheduler/context switch.
    """
    q=bytearray()
    q+=bytes.fromhex('2279')+struct.pack('>I',p.p.p.p.p.p.THIS_TASK)
    q+=bytes.fromhex('2029')+struct.pack('>H',p.p.p.p.p.TC_SPREG)
    q+=bytes.fromhex('23CF')+struct.pack('>I',ORIGINAL_SP_CELL)
    q+=bytes.fromhex('2217')                                      # d1=(a7), caller return PC
    q+=bytes.fromhex('23C1')+struct.pack('>I',CALLER_PC_CELL)
    q+=bytes.fromhex('2E40')                                      # task tc_SPReg -> a7
    q+=bytes.fromhex('2F3C')+struct.pack('>I',m.ROM_BASE+RESUME_OFF)
    q+=bytes.fromhex('23CF')+struct.pack('>I',FRAME_SP_CELL)
    q+=bytes.fromhex('4E75')                                      # RTS via task-stack PC
    return bytes(q)


def resume_code():
    """Private resume target reached only by popping PC from the task stack."""
    q=bytearray()
    q+=bytes.fromhex('23CF')+struct.pack('>I',RESUME_SP_CELL)
    q+=m.ml(ARRIVED_MAGIC,ARRIVED_CELL)
    q+=bytes.fromhex('2E79')+struct.pack('>I',ORIGINAL_SP_CELL)
    q+=bytes.fromhex('4E75')                                      # original caller return PC
    return bytes(q)


def build():
    image=bytearray(p.build())

    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0:
        raise ValueError('M2.40 final success gate not found')
    branch_pos=p.PROBE_OFF+gp+8

    handoff=handoff_code(); resume=resume_code()
    if HANDOFF_OFF+len(handoff)>HANDOFF_END:
        raise ValueError('M2.41 handoff helper exceeds dedicated ROM window')
    if RESUME_OFF+len(resume)>RESUME_END:
        raise ValueError('M2.41 resume stub exceeds dedicated ROM window')
    if any(b != 0xff for b in image[HANDOFF_OFF:HANDOFF_END]):
        raise ValueError('M2.41 handoff helper window is not unused')
    if any(b != 0xff for b in image[RESUME_OFF:RESUME_END]):
        raise ValueError('M2.41 resume stub window is not unused')
    image[HANDOFF_OFF:HANDOFF_OFF+len(handoff)]=handoff
    image[RESUME_OFF:RESUME_OFF+len(resume)]=resume

    c=bytearray(); fails=[]

    def one_case(start_sp):
        frame_sp=start_sp-4
        c.extend(m.ml(start_sp,a.TASK_B+p.p.p.p.p.TC_SPREG))
        c.extend(m.ml(0,frame_sp))
        for cell in (ORIGINAL_SP_CELL,FRAME_SP_CELL,RESUME_SP_CELL,CALLER_PC_CELL,ARRIVED_CELL):
            c.extend(m.ml(0,cell))

        jsr_pos=len(c)
        c.extend(bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+HANDOFF_OFF))
        expected_return=m.ROM_BASE+PROBE_OFF+jsr_pos+6

        fails.append(m.cmpabs(c,m.ROM_BASE+RESUME_OFF,frame_sp))
        fails.append(m.cmpabs(c,frame_sp,FRAME_SP_CELL))
        fails.append(m.cmpabs(c,start_sp,RESUME_SP_CELL))
        fails.append(m.cmpabs(c,expected_return,CALLER_PC_CELL))
        fails.append(m.cmpabs(c,ARRIVED_MAGIC,ARRIVED_CELL))
        fails.append(m.cmpabs(c,a.TASK_B,p.p.p.p.p.p.THIS_TASK))
        fails.append(m.cmpabs(c,start_sp,a.TASK_B+p.p.p.p.p.TC_SPREG))

    # Two independent task-stack PCs prove this is not a fixed-address accident.
    one_case(0x0000D7F0)
    one_case(0x0000D6C0)

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails: m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if PROBE_OFF+len(c)>PROBE_END:
        raise ValueError('M2.41 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[PROBE_OFF:PROBE_OFF+len(c)]):
        raise ValueError('M2.41 runtime probe window is not unused')
    image[PROBE_OFF:PROBE_OFF+len(c)]=c
    struct.pack_into('>h',image,branch_pos+2,PROBE_OFF-(branch_pos+2))

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
        raise SystemExit('usage: make_m2_41_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.41 ROM built: {out} ({len(data)} bytes)')
