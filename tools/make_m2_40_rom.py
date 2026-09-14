#!/usr/bin/env python3
"""Build LibreKick M2.40: SR-aware task context frame slice."""
from pathlib import Path
import struct, sys
import make_m2_39_rom as p
import make_m2_34_rom as a
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.40\0EXEC-CONTEXT-SR\0'
IDENT=b'exec.library\0LibreKick M2.40 SR-aware context frame slice 40.40\0'
PROBE_OFF=0x4F00
PROBE_END=0x5100
CONTEXT_OFF=0x5100
CONTEXT_END=0x5220

ORIGINAL_SP_CELL=0x00004C80
FRAME_SP_CELL=0x00004C84
ORIGINAL_SR_CELL=0x00004C88
RESTORED_SR_CELL=0x00004C8C

D_REGS=list(range(2,8))
A_REGS=list(range(2,7))
D_VALUES={r:0x32000000 | r for r in D_REGS}
A_VALUES={r:0x0000E300 | r for r in A_REGS}
D_CLOBBERS={r:0xCD000000 | r for r in D_REGS}
A_CLOBBERS={r:0x0000F300 | r for r in A_REGS}
REG_ORDER=[('D',r) for r in D_REGS]+[('A',r) for r in A_REGS]
OBS_BASE=0x00004C90
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


def context_code():
    """Save SR plus D2-D7/A2-A6 on ThisTask's stack and restore them.

    The routine deliberately perturbs CCR bits only, then restores the complete
    captured SR as the final context operation. It still does not capture a
    resumable PC or transfer execution to another task.
    """
    q=bytearray()
    q+=bytes.fromhex('2279')+struct.pack('>I',p.p.p.p.p.THIS_TASK)
    q+=bytes.fromhex('2029')+struct.pack('>H',p.p.p.p.TC_SPREG)
    q+=bytes.fromhex('23CF')+struct.pack('>I',ORIGINAL_SP_CELL)
    q+=bytes.fromhex('2E40')

    # Capture SR zero-extended in D0, record it, and save the 16-bit SR first.
    q+=bytes.fromhex('428040C0')
    q+=bytes.fromhex('23C0')+struct.pack('>I',ORIGINAL_SR_CELL)
    q+=bytes.fromhex('3F00')

    for r in D_REGS:
        q+=push_d(r)
    for r in A_REGS:
        q+=push_a(r)
    q+=bytes.fromhex('23CF')+struct.pack('>I',FRAME_SP_CELL)

    for r in D_REGS:
        q+=imm_d(r,D_CLOBBERS[r])
    for r in A_REGS:
        q+=imm_a(r,A_CLOBBERS[r])

    # Perturb only CCR bits; supervisor/interrupt state is left untouched.
    q+=bytes.fromhex('0A3C001F')

    for r in reversed(A_REGS):
        q+=pop_a(r); q+=store_a(r,OBS_CELLS[('A',r)])
    for r in reversed(D_REGS):
        q+=pop_d(r); q+=store_d(r,OBS_CELLS[('D',r)])

    # SR is restored last so subsequent MOVE operations cannot change CCR.
    q+=bytes.fromhex('46DF')
    q+=bytes.fromhex('428040C0')
    q+=bytes.fromhex('23C0')+struct.pack('>I',RESTORED_SR_CELL)
    q+=bytes.fromhex('2E79')+struct.pack('>I',ORIGINAL_SP_CELL)
    q+=bytes.fromhex('4E75')
    return bytes(q)


def build():
    image=bytearray(p.build())
    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0: raise ValueError('M2.39 final success gate not found')
    branch_pos=p.PROBE_OFF+gp+8

    routine=context_code()
    if CONTEXT_OFF+len(routine)>CONTEXT_END:
        raise ValueError('M2.40 context helper exceeds dedicated ROM window')
    if any(b != 0xff for b in image[CONTEXT_OFF:CONTEXT_END]):
        raise ValueError('M2.40 context helper window is not unused')
    image[CONTEXT_OFF:CONTEXT_OFF+len(routine)]=routine

    c=bytearray(); fails=[]
    start_sp=0x0000D7F0
    frame_sp=start_sp-2-4*len(REG_ORDER)

    c+=m.ml(0x0000D000,a.TASK_B+p.p.p.p.TC_SPLOWER)
    c+=m.ml(0x0000D800,a.TASK_B+p.p.p.p.TC_SPUPPER)
    c+=m.ml(start_sp,a.TASK_B+p.p.p.p.TC_SPREG)
    for cell in [ORIGINAL_SP_CELL,FRAME_SP_CELL,ORIGINAL_SR_CELL,RESTORED_SR_CELL]:
        c+=m.ml(0,cell)

    for r in D_REGS: c+=imm_d(r,D_VALUES[r])
    for r in A_REGS: c+=imm_a(r,A_VALUES[r])
    c+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+CONTEXT_OFF)

    fails.append(m.cmpabs(c,frame_sp,FRAME_SP_CELL))
    fails.append(m.cmpabs(c,a.TASK_B,p.p.p.p.p.THIS_TASK))
    fails.append(m.cmpabs(c,start_sp,a.TASK_B+p.p.p.p.TC_SPREG))
    for r in D_REGS: fails.append(m.cmpabs(c,D_VALUES[r],OBS_CELLS[('D',r)]))
    for r in A_REGS: fails.append(m.cmpabs(c,A_VALUES[r],OBS_CELLS[('A',r)]))

    # Original and restored zero-extended SR values must match exactly.
    c+=bytes.fromhex('2039')+struct.pack('>I',ORIGINAL_SR_CELL)
    c+=bytes.fromhex('B0B9')+struct.pack('>I',RESTORED_SR_CELL)
    fails.append(m.branch(c,0x6600))

    # Physical frame: low end contains A6; highest saved item is the SR word.
    fails.append(m.cmpabs(c,A_VALUES[6],frame_sp))

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails: m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if PROBE_OFF+len(c)>PROBE_END:
        raise ValueError('M2.40 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[PROBE_OFF:PROBE_OFF+len(c)]):
        raise ValueError('M2.40 runtime probe window is not unused')
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
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_40_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.40 ROM built: {out} ({len(data)} bytes)')
