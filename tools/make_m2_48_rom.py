#!/usr/bin/env python3
"""Build LibreKick M2.48 with a private deterministic two-task context switch."""
from __future__ import annotations
import struct, sys
from pathlib import Path
import make_m2_47_rom as previous
import make_m2_17_rom as runtime
from librekick_exec_abi import EXEC_BASE
from librekick_exec_runtime import THIS_TASK_OFF, TC_SPREG_OFF

ROM_BASE=runtime.ROM_BASE
COLOR00=runtime.COLOR00
SWITCH_OFF=0x7100
SWITCH_END=0x7300
TASK_B_ENTRY_OFF=0x7300
TASK_B_ENTRY_END=0x7400
PROBE_OFF=0x7400
PROBE_END=0x7800
META_OFF=0x7800
TASK_A=0x0000CE00
TASK_B=0x0000CE80
STACK_A_TOP=0x0000E800
STACK_B_TOP=0x0000EC00
A_RETURN_SP=0x0000CD00
B_SEEN=0x0000CD04
A_SEEN=0x0000CD08
B_MAGIC=0x42323438
A_MAGIC=0x41323438
D_REGS=list(range(2,8)); A_REGS=list(range(2,7))
A_D={r:0xA2000000|r for r in D_REGS}; A_A={r:0x0000A200|r for r in A_REGS}
B_D={r:0xB2000000|r for r in D_REGS}; B_A={r:0x0000B200|r for r in A_REGS}
MARKER=b"LIBREKICK-M2.48\0PRIVATE-TWO-TASK-CONTEXT-SWITCH\0"
IDENT=b"exec.library\0LibreKick M2.48 private two-task context switch 40.48\0"

def w(v): return struct.pack('>H',v)
def l(v): return struct.pack('>I',v)
def ml(v,a): return bytes.fromhex('23fc')+l(v)+l(a)
def mw(v,a): return bytes.fromhex('33fc')+w(v)+l(a)
def cmp_l(v,a): return bytes.fromhex('0cb9')+l(v)+l(a)
def jsr(a): return bytes.fromhex('4eb9')+l(a)
def imm_d(r,v): return w(0x203C+(r<<9))+l(v)
def imm_a(r,v): return w(0x207C+(r<<9))+l(v)
def push_d(r): return w(0x2F00+r)
def push_a(r): return w(0x2F08+r)
def pop_d(r): return w(0x201F+(r<<9))
def pop_a(r): return w(0x205F+(r<<9))
def branch(c,op): p=len(c); c+=struct.pack('>HH',op,0); return p
def patch(c,p,t): struct.pack_into('>h',c,p+2,t-(p+2))

def switch_code():
    # A0 = next task. Save current task's callee context and return PC on its
    # stack, publish tc_SPReg, change ThisTask, then restore the prepared next
    # task context and RTS into its continuation.
    q=bytearray()
    q+=bytes.fromhex('40e7')                 # move.w SR,-(A7)
    for r in D_REGS: q+=push_d(r)
    for r in A_REGS: q+=push_a(r)
    q+=bytes.fromhex('2279')+l(EXEC_BASE+THIS_TASK_OFF) # movea.l ThisTask,A1
    q+=bytes.fromhex('234f')+w(TC_SPREG_OFF) # move.l A7,tc_SPReg(A1)
    q+=bytes.fromhex('23c8')+l(EXEC_BASE+THIS_TASK_OFF) # move.l A0,ThisTask
    q+=bytes.fromhex('2e68')+w(TC_SPREG_OFF) # movea.l tc_SPReg(A0),A7
    for r in reversed(A_REGS): q+=pop_a(r)
    for r in reversed(D_REGS): q+=pop_d(r)
    q+=bytes.fromhex('46df')                 # move.w (A7)+,SR
    q+=bytes.fromhex('4e75')
    return bytes(q)

def prepared_frame(entry,dvals,avals):
    # Layout consumed by switch_code restore: A6..A2, D7..D2, SR, return PC.
    # Push in inverse construction order so A7 points at saved A6.
    vals=[entry,0x2000]
    vals += [dvals[r] for r in D_REGS]
    vals += [avals[r] for r in A_REGS]
    # memory at SP must be A6,A5,...A2,D7,...D2,SR,PC
    out=bytearray()
    for r in reversed(A_REGS): out+=l(avals[r])
    for r in reversed(D_REGS): out+=l(dvals[r])
    out+=w(0x2000)+l(entry)
    return bytes(out)

def task_b_code():
    q=bytearray(); q+=ml(B_MAGIC,B_SEEN)
    q+=bytes.fromhex('207c')+l(TASK_A)       # movea.l #TASK_A,A0
    q+=jsr(ROM_BASE+SWITCH_OFF)
    q+=mw(0x000f,COLOR00)+bytes.fromhex('60fe')
    return bytes(q)

def probe_code():
    c=bytearray(); bad=[]
    c+=ml(0,B_SEEN)+ml(0,A_SEEN)
    # Task B prepared frame lives below STACK_B_TOP.
    frame=prepared_frame(ROM_BASE+TASK_B_ENTRY_OFF,B_D,B_A)
    b_sp=STACK_B_TOP-len(frame)
    for i in range(0,len(frame),4):
        chunk=frame[i:i+4]
        if len(chunk)==4: c+=ml(struct.unpack('>I',chunk)[0],b_sp+i)
        elif len(chunk)==2: c+=mw(struct.unpack('>H',chunk)[0],b_sp+i)
    c+=ml(b_sp,TASK_B+TC_SPREG_OFF)
    c+=ml(TASK_A,EXEC_BASE+THIS_TASK_OFF)
    for r in D_REGS: c+=imm_d(r,A_D[r])
    for r in A_REGS: c+=imm_a(r,A_A[r])
    c+=bytes.fromhex('207c')+l(TASK_B)
    c+=jsr(ROM_BASE+SWITCH_OFF)
    c+=ml(A_MAGIC,A_SEEN)
    c+=cmp_l(TASK_A,EXEC_BASE+THIS_TASK_OFF); bad.append(branch(c,0x6600))
    c+=cmp_l(B_MAGIC,B_SEEN); bad.append(branch(c,0x6600))
    c+=cmp_l(A_MAGIC,A_SEEN); bad.append(branch(c,0x6600))
    c+=mw(0x00f0,COLOR00); good=branch(c,0x6000)
    fail=len(c); c+=mw(0x000f,COLOR00); idle=len(c); c+=bytes.fromhex('60fe')
    for p in bad: patch(c,p,fail)
    patch(c,good,idle)
    return bytes(c)

def build():
    rom=bytearray(previous.build())
    sw=switch_code(); tb=task_b_code(); probe=probe_code()
    for lo,hi,data in ((SWITCH_OFF,SWITCH_END,sw),(TASK_B_ENTRY_OFF,TASK_B_ENTRY_END,tb),(PROBE_OFF,PROBE_END,probe)):
        if any(b!=0xff for b in rom[lo:hi]): raise ValueError(f'M2.48 ROM window {lo:#x}..{hi:#x} is not free')
        if len(data)>hi-lo: raise ValueError(f'M2.48 code exceeds window at {lo:#x}')
        rom[lo:lo+len(data)]=data
    # Chain from the M2.47 green terminal branch through an in-range trampoline.
    sig=bytes.fromhex('33fc00f000dff1806000')
    window=rom[previous.PROBE_OFF:previous.PROBE_END]
    rel=window.rfind(sig)
    if rel<0: raise ValueError('M2.47 success gate not found')
    branch_at=previous.PROBE_OFF+rel+8
    trampoline=None
    for candidate in range(previous.PROBE_END-6,branch_at+1,-2):
        if all(b==0xff for b in rom[candidate:candidate+6]):
            disp=candidate-(branch_at+2)
            if -128<=disp<=127 and disp!=0: trampoline=candidate; break
    if trampoline is None: raise ValueError('no M2.47 trampoline slot for M2.48')
    rom[branch_at:branch_at+2]=bytes((0x60,(trampoline-(branch_at+2))&0xff))
    rom[trampoline:trampoline+6]=bytes.fromhex('4ef9')+l(ROM_BASE+PROBE_OFF)
    if any(b!=0xff for b in rom[META_OFF:META_OFF+0x100]): raise ValueError('M2.48 metadata window not free')
    rom[META_OFF:META_OFF+len(MARKER)]=MARKER; rom[META_OFF+0x60:META_OFF+0x60+len(IDENT)]=IDENT
    rom[runtime.MARKER_OFF:runtime.IDENT_OFF]=b'\xff'*(runtime.IDENT_OFF-runtime.MARKER_OFF); rom[runtime.MARKER_OFF:runtime.MARKER_OFF+len(MARKER)]=MARKER
    rom[runtime.IDENT_OFF:runtime.NAME_A_OFF]=b'\xff'*(runtime.NAME_A_OFF-runtime.IDENT_OFF); rom[runtime.IDENT_OFF:runtime.IDENT_OFF+len(IDENT)]=IDENT
    struct.pack_into('>I',rom,runtime.ROM_SIZE-4,0); total=0
    for off in range(0,runtime.ROM_SIZE-4,4): total=runtime.ones(total,struct.unpack_from('>I',rom,off)[0])
    total=(total&0xffffffff)+(total>>32); struct.pack_into('>I',rom,runtime.ROM_SIZE-4,(~total)&0xffffffff)
    return bytes(rom)

def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'build/librekick-m2_48.rom'); out.parent.mkdir(parents=True,exist_ok=True); data=build(); out.write_bytes(data)
    print(f'M2.48 ROM built: {out} ({len(data)} bytes)')
    print('scope=private deterministic two-task context switch; public Exec scheduler not claimed')
if __name__=='__main__': main()
