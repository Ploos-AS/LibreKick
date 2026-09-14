#!/usr/bin/env python3
"""Build LibreKick M2.43: private prepared-task context activation slice."""
from pathlib import Path
import struct, sys
import make_m2_42_rom as p
import make_m2_34_rom as a
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.43\0EXEC-PREPARED-TASK-ACTIVATE\0'
IDENT=b'exec.library\0LibreKick M2.43 prepared-task context activation slice 40.43\0'
PROBE_OFF=0x5B00
PROBE_END=0x5E00
ACTIVATE_OFF=0x5E00
ACTIVATE_END=0x5F00
RESTORE_OFF=0x5F00
RESTORE_END=0x6000
TARGET_OFF=0x6000
TARGET_END=0x6100

THIS_TASK=0x00003514
CURRENT_TASK_PTR=0x00004C10
TC_STATE=15
TC_SPREG=0x36
TC_SPLOWER=0x3A
TC_SPUPPER=0x3E
TS_RUN=2

CALLER_SP_CELL=0x00004D40
CALLER_PC_CELL=0x00004D44
CALLER_SR_CELL=0x00004D48
TARGET_SR_CELL=0x00004D4A
TARGET_ENTRY_SP_CELL=0x00004D4C
ARRIVED_CELL=0x00004D50
ARRIVED_MAGIC=0x4C4B3433
OBS_BASE=0x00004D60

D_REGS=list(range(2,8))
A_REGS=list(range(2,7))
REG_ORDER=[('D',r) for r in D_REGS]+[('A',r) for r in A_REGS]
OBS_CELLS={(k,r):OBS_BASE+i*4 for i,(k,r) in enumerate(REG_ORDER)}
D_VALUES={r:0x43000000|r for r in D_REGS}
A_VALUES={r:0x0000E500|r for r in A_REGS}
TARGET_SR=0x2700
TARGET_STACK_TOP=0x0000E7F0
FRAME_LOW=TARGET_STACK_TOP-2-4*len(REG_ORDER)
TRANSFER_SP=FRAME_LOW-4
TARGET_ENTRY_SP=TARGET_STACK_TOP+4


def opw(w): return struct.pack('>H',w)
def pop_d(r): return opw(0x201F+(r<<9))
def pop_a(r): return opw(0x205F+(r<<9))
def store_d(r,addr): return opw(0x23C0+r)+struct.pack('>I',addr)
def store_a(r,addr): return opw(0x23C8+r)+struct.pack('>I',addr)


def activate_code():
    """Switch A7/ThisTask to a prebuilt TASK_A context and enter it by RTS."""
    q=bytearray()
    q+=bytes.fromhex('40F9')+struct.pack('>I',CALLER_SR_CELL)       # caller SR
    q+=bytes.fromhex('23CF')+struct.pack('>I',CALLER_SP_CELL)       # caller A7
    q+=bytes.fromhex('2017')                                        # caller return PC
    q+=bytes.fromhex('23C0')+struct.pack('>I',CALLER_PC_CELL)
    q+=m.ml(a.TASK_A,THIS_TASK)
    q+=m.ml(a.TASK_A,CURRENT_TASK_PTR)
    q+=bytes.fromhex('13FC0002')+struct.pack('>I',a.TASK_A+TC_STATE)
    q+=bytes.fromhex('2E79')+struct.pack('>I',a.TASK_A+TC_SPREG)    # prepared transfer SP
    q+=bytes.fromhex('4E75')                                        # pop RESTORE_OFF from task stack
    return bytes(q)


def restore_code():
    """Restore the prepared register/SR frame, then RTS into target entry PC."""
    q=bytearray()
    for r in reversed(A_REGS): q+=pop_a(r)
    for r in reversed(D_REGS): q+=pop_d(r)
    q+=bytes.fromhex('46DF')                                        # prepared SR
    q+=bytes.fromhex('4E75')                                        # prepared target PC
    return bytes(q)


def target_code():
    """Observe restored target state, then return to the qualification harness."""
    q=bytearray()
    q+=bytes.fromhex('40F9')+struct.pack('>I',TARGET_SR_CELL)
    q+=bytes.fromhex('23CF')+struct.pack('>I',TARGET_ENTRY_SP_CELL)
    for r in D_REGS: q+=store_d(r,OBS_CELLS[('D',r)])
    for r in A_REGS: q+=store_a(r,OBS_CELLS[('A',r)])
    q+=m.ml(ARRIVED_MAGIC,ARRIVED_CELL)
    q+=bytes.fromhex('46F9')+struct.pack('>I',CALLER_SR_CELL)       # restore harness SR
    q+=bytes.fromhex('2E79')+struct.pack('>I',CALLER_SP_CELL)
    q+=bytes.fromhex('4E75')
    return bytes(q)


def build():
    image=bytearray(p.build())
    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0: raise ValueError('M2.42 final success gate not found')
    branch_pos=p.PROBE_OFF+gp+8

    blocks=((ACTIVATE_OFF,ACTIVATE_END,activate_code()),(RESTORE_OFF,RESTORE_END,restore_code()),(TARGET_OFF,TARGET_END,target_code()))
    for lo,hi,code in blocks:
        if lo+len(code)>hi: raise ValueError('M2.43 helper exceeds dedicated ROM window')
        if any(b!=0xff for b in image[lo:hi]): raise ValueError('M2.43 ROM helper window is not unused')
        image[lo:lo+len(code)]=code

    c=bytearray(); fails=[]
    # Build TASK_A metadata and its complete prepared context frame.
    c+=m.ml(0x0000E000,a.TASK_A+TC_SPLOWER)
    c+=m.ml(0x0000E800,a.TASK_A+TC_SPUPPER)
    c+=m.ml(TRANSFER_SP,a.TASK_A+TC_SPREG)
    c+=m.ml(m.ROM_BASE+RESTORE_OFF,TRANSFER_SP)
    addr=FRAME_LOW
    for r in reversed(A_REGS): c+=m.ml(A_VALUES[r],addr); addr+=4
    for r in reversed(D_REGS): c+=m.ml(D_VALUES[r],addr); addr+=4
    c+=bytes.fromhex('33FC')+struct.pack('>H',TARGET_SR)+struct.pack('>I',addr)
    c+=m.ml(m.ROM_BASE+TARGET_OFF,TARGET_STACK_TOP)

    for cell in (CALLER_SP_CELL,CALLER_PC_CELL,TARGET_ENTRY_SP_CELL,ARRIVED_CELL): c+=m.ml(0,cell)
    c+=bytes.fromhex('33FC0000')+struct.pack('>I',CALLER_SR_CELL)
    c+=bytes.fromhex('33FC0000')+struct.pack('>I',TARGET_SR_CELL)
    for cell in OBS_CELLS.values(): c+=m.ml(0,cell)

    jsr_pos=len(c)
    c+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+ACTIVATE_OFF)
    expected_return=m.ROM_BASE+PROBE_OFF+jsr_pos+6

    fails.append(m.cmpabs(c,a.TASK_A,THIS_TASK))
    fails.append(m.cmpabs(c,a.TASK_A,CURRENT_TASK_PTR))
    fails.append(m.cmpabs(c,TRANSFER_SP,a.TASK_A+TC_SPREG))
    fails.append(m.cmpabs(c,m.ROM_BASE+RESTORE_OFF,TRANSFER_SP))
    fails.append(m.cmpabs(c,m.ROM_BASE+TARGET_OFF,TARGET_STACK_TOP))
    fails.append(m.cmpabs(c,TARGET_ENTRY_SP,TARGET_ENTRY_SP_CELL))
    fails.append(m.cmpabs(c,ARRIVED_MAGIC,ARRIVED_CELL))
    fails.append(m.cmpabs(c,expected_return,CALLER_PC_CELL))
    for r in D_REGS: fails.append(m.cmpabs(c,D_VALUES[r],OBS_CELLS[('D',r)]))
    for r in A_REGS: fails.append(m.cmpabs(c,A_VALUES[r],OBS_CELLS[('A',r)]))
    c+=bytes.fromhex('3039')+struct.pack('>I',TARGET_SR_CELL)
    c+=bytes.fromhex('0C40')+struct.pack('>H',TARGET_SR)
    fails.append(m.branch(c,0x6600))
    # TASK_A must be marked running.
    c+=bytes.fromhex('1039')+struct.pack('>I',a.TASK_A+TC_STATE)
    c+=bytes.fromhex('0C0002')
    fails.append(m.branch(c,0x6600))

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails: m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if PROBE_OFF+len(c)>PROBE_END: raise ValueError(f'M2.43 runtime probe exceeds dedicated ROM window ({len(c)} bytes)')
    if any(b!=0xff for b in image[PROBE_OFF:PROBE_OFF+len(c)]): raise ValueError('M2.43 probe window is not unused')
    image[PROBE_OFF:PROBE_OFF+len(c)]=c
    struct.pack_into('>h',image,branch_pos+2,PROBE_OFF-(branch_pos+2))

    image[m.MARKER_OFF:m.IDENT_OFF]=b'\xff'*(m.IDENT_OFF-m.MARKER_OFF)
    image[m.MARKER_OFF:m.MARKER_OFF+len(MARKER)]=MARKER
    image[m.IDENT_OFF:m.NAME_A_OFF]=b'\xff'*(m.NAME_A_OFF-m.IDENT_OFF)
    image[m.IDENT_OFF:m.IDENT_OFF+len(IDENT)]=IDENT
    struct.pack_into('>I',image,m.ROM_SIZE-4,0)
    total=0
    for off in range(0,m.ROM_SIZE-4,4): total=m.ones(total,struct.unpack_from('>I',image,off)[0])
    total=(total&0xffffffff)+(total>>32)
    struct.pack_into('>I',image,m.ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_43_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.43 ROM built: {out} ({len(data)} bytes)')
