#!/usr/bin/env python3
"""Build LibreKick M2.42: integrated private register/SR/PC context transfer."""
from pathlib import Path
import struct, sys
import make_m2_41_rom as p
import make_m2_34_rom as a
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.42\0EXEC-CONTEXT-INTEGRATED\0'
IDENT=b'exec.library\0LibreKick M2.42 integrated private context transfer slice 40.42\0'
PROBE_OFF=0x5600
PROBE_END=0x5800
HANDOFF_OFF=0x5800
HANDOFF_END=0x5900
RESUME_OFF=0x5900
RESUME_END=0x5A00

THIS_TASK=0x00003514
TC_SPREG=0x36
TC_SPLOWER=0x3A
TC_SPUPPER=0x3E

ORIGINAL_SP_CELL=0x00004CE0
CALLER_PC_CELL=0x00004CE4
ORIGINAL_SR_CELL=0x00004CE8
RETURNED_SR_CELL=0x00004CEA
TRANSFER_SP_CELL=0x00004CEC
RESUME_SP_CELL=0x00004CF0
ARRIVED_CELL=0x00004CF4
ARRIVED_MAGIC=0x4C4B3432
OBS_BASE=0x00004D00

D_REGS=list(range(2,8))
A_REGS=list(range(2,7))
D_VALUES={r:0x42000000 | r for r in D_REGS}
A_VALUES={r:0x0000E400 | r for r in A_REGS}
D_CLOBBERS={r:0xBC000000 | r for r in D_REGS}
A_CLOBBERS={r:0x0000F400 | r for r in A_REGS}
REG_ORDER=[('D',r) for r in D_REGS]+[('A',r) for r in A_REGS]
OBS_CELLS={(kind,r):OBS_BASE+i*4 for i,(kind,r) in enumerate(REG_ORDER)}


def opw(w): return struct.pack('>H',w)
def push_d(r): return opw(0x2F00+r)
def push_a(r): return opw(0x2F08+r)
def pop_d(r): return opw(0x201F+(r<<9))
def pop_a(r): return opw(0x205F+(r<<9))
def imm_d(r,v): return opw(0x203C+(r<<9))+struct.pack('>I',v)
def imm_a(r,v): return opw(0x207C+(r<<9))+struct.pack('>I',v)
def store_d(r,addr): return opw(0x23C0+r)+struct.pack('>I',addr)
def store_a(r,addr): return opw(0x23C8+r)+struct.pack('>I',addr)


def handoff_code():
    """Save preserved registers + entry SR on the task stack, then transfer PC.

    Entry is by JSR on the caller stack. The entry SR is captured before any
    flag-changing MOVE sequence. A7 is then redirected to ThisTask->tc_SPReg.
    The captured SR word and D2-D7/A2-A6 are pushed on the task stack, those
    registers/CCR are deliberately perturbed, a private resume PC is pushed,
    and RTS transfers execution through that task-stack PC.
    """
    q=bytearray()
    q+=bytes.fromhex('40F9')+struct.pack('>I',ORIGINAL_SR_CELL)    # entry SR -> word cell
    q+=bytes.fromhex('2279')+struct.pack('>I',THIS_TASK)           # a1=ThisTask
    q+=bytes.fromhex('2029')+struct.pack('>H',TC_SPREG)            # d0=tc_SPReg
    q+=bytes.fromhex('23CF')+struct.pack('>I',ORIGINAL_SP_CELL)    # caller a7
    q+=bytes.fromhex('2217')                                       # d1=caller return PC
    q+=bytes.fromhex('23C1')+struct.pack('>I',CALLER_PC_CELL)
    q+=bytes.fromhex('2E40')                                       # task stack

    q+=bytes.fromhex('3F39')+struct.pack('>I',ORIGINAL_SR_CELL)    # saved entry SR word
    for r in D_REGS: q+=push_d(r)
    for r in A_REGS: q+=push_a(r)

    for r in D_REGS: q+=imm_d(r,D_CLOBBERS[r])
    for r in A_REGS: q+=imm_a(r,A_CLOBBERS[r])
    q+=bytes.fromhex('0A3C001F')                                   # perturb CCR only

    q+=bytes.fromhex('2F3C')+struct.pack('>I',m.ROM_BASE+RESUME_OFF)
    q+=bytes.fromhex('23CF')+struct.pack('>I',TRANSFER_SP_CELL)
    q+=bytes.fromhex('4E75')                                       # resume PC popped from task stack
    return bytes(q)


def resume_code():
    """Restore register subset and saved SR, then return to original caller.

    RTS has already consumed the synthetic resume PC, so A7 points at the low
    end of the saved register frame (A6). Stores used to observe restored
    registers may change CCR, therefore the captured SR is restored only after
    all observation stores. After MOVE (A7)+,SR only MOVEA and RTS execute.
    """
    q=bytearray()
    q+=bytes.fromhex('23CF')+struct.pack('>I',RESUME_SP_CELL)
    q+=m.ml(ARRIVED_MAGIC,ARRIVED_CELL)

    for r in reversed(A_REGS):
        q+=pop_a(r); q+=store_a(r,OBS_CELLS[('A',r)])
    for r in reversed(D_REGS):
        q+=pop_d(r); q+=store_d(r,OBS_CELLS[('D',r)])

    q+=bytes.fromhex('46DF')                                       # restore saved SR last
    q+=bytes.fromhex('2E79')+struct.pack('>I',ORIGINAL_SP_CELL)    # MOVEA: no CCR change
    q+=bytes.fromhex('4E75')                                       # original caller return PC
    return bytes(q)


def build():
    image=bytearray(p.build())

    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0: raise ValueError('M2.41 final success gate not found')
    branch_pos=p.PROBE_OFF+gp+8

    handoff=handoff_code(); resume=resume_code()
    if HANDOFF_OFF+len(handoff)>HANDOFF_END:
        raise ValueError('M2.42 handoff helper exceeds dedicated ROM window')
    if RESUME_OFF+len(resume)>RESUME_END:
        raise ValueError('M2.42 resume helper exceeds dedicated ROM window')
    if any(b != 0xff for b in image[HANDOFF_OFF:HANDOFF_END]):
        raise ValueError('M2.42 handoff helper window is not unused')
    if any(b != 0xff for b in image[RESUME_OFF:RESUME_END]):
        raise ValueError('M2.42 resume helper window is not unused')
    image[HANDOFF_OFF:HANDOFF_OFF+len(handoff)]=handoff
    image[RESUME_OFF:RESUME_OFF+len(resume)]=resume

    c=bytearray(); fails=[]
    start_sp=0x0000D7F0
    # SR word + 11 long registers = 46 bytes. Resume PC adds another 4 bytes.
    frame_low=start_sp-2-4*len(REG_ORDER)                          # $D7C2
    transfer_sp=frame_low-4                                       # $D7BE

    c+=m.ml(0x0000D000,a.TASK_B+TC_SPLOWER)
    c+=m.ml(0x0000D800,a.TASK_B+TC_SPUPPER)
    c+=m.ml(start_sp,a.TASK_B+TC_SPREG)
    for addr in (ORIGINAL_SP_CELL,CALLER_PC_CELL,TRANSFER_SP_CELL,RESUME_SP_CELL,ARRIVED_CELL):
        c+=m.ml(0,addr)
    c+=bytes.fromhex('33FC0000')+struct.pack('>I',ORIGINAL_SR_CELL)
    c+=bytes.fromhex('33FC0000')+struct.pack('>I',RETURNED_SR_CELL)
    for addr in OBS_CELLS.values(): c+=m.ml(0,addr)

    for r in D_REGS: c+=imm_d(r,D_VALUES[r])
    for r in A_REGS: c+=imm_a(r,A_VALUES[r])

    jsr_pos=len(c)
    c+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+HANDOFF_OFF)
    expected_return=m.ROM_BASE+PROBE_OFF+jsr_pos+6

    # Capture returned SR immediately. MOVE from SR does not intentionally alter
    # the saved condition-code state; later comparisons may.
    c+=bytes.fromhex('40F9')+struct.pack('>I',RETURNED_SR_CELL)

    fails.append(m.cmpabs(c,transfer_sp,TRANSFER_SP_CELL))
    fails.append(m.cmpabs(c,frame_low,RESUME_SP_CELL))
    fails.append(m.cmpabs(c,m.ROM_BASE+RESUME_OFF,transfer_sp))
    fails.append(m.cmpabs(c,ARRIVED_MAGIC,ARRIVED_CELL))
    fails.append(m.cmpabs(c,expected_return,CALLER_PC_CELL))
    fails.append(m.cmpabs(c,a.TASK_B,THIS_TASK))
    fails.append(m.cmpabs(c,start_sp,a.TASK_B+TC_SPREG))

    for r in D_REGS: fails.append(m.cmpabs(c,D_VALUES[r],OBS_CELLS[('D',r)]))
    for r in A_REGS: fails.append(m.cmpabs(c,A_VALUES[r],OBS_CELLS[('A',r)]))

    # Physical task-stack frame endpoints remain observable after the pops.
    fails.append(m.cmpabs(c,A_VALUES[6],frame_low))
    fails.append(m.cmpabs(c,D_VALUES[2],start_sp-6))

    # Compare captured entry SR word to the SR word observed immediately after
    # the complete resume/return path.
    c+=bytes.fromhex('3039')+struct.pack('>I',ORIGINAL_SR_CELL)    # move.w entrySR,d0
    c+=bytes.fromhex('B079')+struct.pack('>I',RETURNED_SR_CELL)    # cmp.w returnedSR,d0
    fails.append(m.branch(c,0x6600))

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails: m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if PROBE_OFF+len(c)>PROBE_END:
        raise ValueError(f'M2.42 runtime probe exceeds dedicated ROM window ({len(c)} bytes)')
    if any(b != 0xff for b in image[PROBE_OFF:PROBE_OFF+len(c)]):
        raise ValueError('M2.42 runtime probe window is not unused')
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
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_42_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.42 ROM built: {out} ({len(data)} bytes)')
