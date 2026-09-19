#!/usr/bin/env python3
"""Build LibreKick M2.49 with a private ready-list-driven dispatcher."""
from __future__ import annotations
import struct, sys
from pathlib import Path
import make_m2_48_rom as previous
import make_m2_17_rom as runtime
from librekick_exec_abi import EXEC_BASE
from librekick_exec_runtime import THIS_TASK_OFF, TC_SPREG_OFF

ROM_BASE=runtime.ROM_BASE; COLOR00=runtime.COLOR00
DISPATCH_OFF=0x7900; DISPATCH_END=0x7B00
TASK_B_ENTRY_OFF=0x7B00; TASK_B_ENTRY_END=0x7C00
PROBE_OFF=0x7C00; PROBE_END=0x8000
META_OFF=0x8000
READY_TASK=0x0000CD20
TASK_A=previous.TASK_A; TASK_B=previous.TASK_B
STACK_B_TOP=previous.STACK_B_TOP
B_SEEN=0x0000CD24; A_SEEN=0x0000CD28
B_MAGIC=0x42323439; A_MAGIC=0x41323439
D_REGS=previous.D_REGS; A_REGS=previous.A_REGS
A_D={r:0xA3000000|r for r in D_REGS}; A_A={r:0x0000A300|r for r in A_REGS}
B_D={r:0xB3000000|r for r in D_REGS}; B_A={r:0x0000B300|r for r in A_REGS}
MARKER=b"LIBREKICK-M2.49\0PRIVATE-READY-LIST-DISPATCH\0"
IDENT=b"exec.library\0LibreKick M2.49 private ready-list dispatch 40.49\0"

w=previous.w; l=previous.l; ml=previous.ml; mw=previous.mw; cmp_l=previous.cmp_l
jsr=previous.jsr; imm_d=previous.imm_d; imm_a=previous.imm_a
push_d=previous.push_d; push_a=previous.push_a; pop_d=previous.pop_d; pop_a=previous.pop_a
branch=previous.branch; patch=previous.patch
prepared_frame=previous.prepared_frame

def dispatch_code():
    # Private single-entry ready selector. The caller does not provide the next
    # task pointer. READY_TASK is consumed, then the current task is published
    # there for the selected task to dispatch back to.
    q=bytearray()
    q+=bytes.fromhex('2079')+l(READY_TASK)                 # movea.l READY_TASK,A0
    q+=bytes.fromhex('4a88')                              # tst.l A0
    empty=branch(q,0x6700)                                # beq fail/return
    q+=bytes.fromhex('40e7')
    for r in D_REGS: q+=push_d(r)
    for r in A_REGS: q+=push_a(r)
    q+=bytes.fromhex('2279')+l(EXEC_BASE+THIS_TASK_OFF)   # current -> A1
    q+=bytes.fromhex('234f')+w(TC_SPREG_OFF)              # save A7
    q+=bytes.fromhex('23c9')+l(READY_TASK)                # READY_TASK=current
    q+=bytes.fromhex('23c8')+l(EXEC_BASE+THIS_TASK_OFF)   # ThisTask=selected
    q+=bytes.fromhex('2e68')+w(TC_SPREG_OFF)              # restore selected A7
    for r in reversed(A_REGS): q+=pop_a(r)
    for r in reversed(D_REGS): q+=pop_d(r)
    q+=bytes.fromhex('46df4e75')
    fail=len(q); q+=bytes.fromhex('4e75')
    patch(q,empty,fail)
    return bytes(q)

def task_b_code():
    q=bytearray()
    q+=cmp_l(TASK_B,EXEC_BASE+THIS_TASK_OFF); bad=branch(q,0x6600)
    q+=ml(B_MAGIC,B_SEEN)
    q+=jsr(ROM_BASE+DISPATCH_OFF)
    q+=mw(0x0f00,COLOR00)+bytes.fromhex('60fe')
    fail=len(q); q+=mw(0x0f00,COLOR00)+bytes.fromhex('60fe')
    patch(q,bad,fail)
    return bytes(q)

def probe_code():
    c=bytearray(); bad=[]
    c+=ml(0,B_SEEN)+ml(0,A_SEEN)
    frame=prepared_frame(ROM_BASE+TASK_B_ENTRY_OFF,B_D,B_A)
    b_sp=STACK_B_TOP-len(frame)
    for i in range(0,len(frame),4):
        chunk=frame[i:i+4]
        if len(chunk)==4: c+=ml(struct.unpack('>I',chunk)[0],b_sp+i)
        else: c+=mw(struct.unpack('>H',chunk)[0],b_sp+i)
    c+=ml(b_sp,TASK_B+TC_SPREG_OFF)
    c+=ml(TASK_A,EXEC_BASE+THIS_TASK_OFF)
    c+=ml(TASK_B,READY_TASK)
    for r in D_REGS: c+=imm_d(r,A_D[r])
    for r in A_REGS: c+=imm_a(r,A_A[r])
    c+=jsr(ROM_BASE+DISPATCH_OFF)
    c+=ml(A_MAGIC,A_SEEN)
    c+=cmp_l(TASK_A,EXEC_BASE+THIS_TASK_OFF); bad.append(branch(c,0x6600))
    c+=cmp_l(TASK_B,READY_TASK); bad.append(branch(c,0x6600))
    c+=cmp_l(B_MAGIC,B_SEEN); bad.append(branch(c,0x6600))
    c+=cmp_l(A_MAGIC,A_SEEN); bad.append(branch(c,0x6600))
    c+=mw(0x00f0,COLOR00); good=branch(c,0x6000)
    fail=len(c); c+=mw(0x0f00,COLOR00); idle=len(c); c+=bytes.fromhex('60fe')
    for p in bad: patch(c,p,fail)
    patch(c,good,idle)
    return bytes(c)

def build():
    rom=bytearray(previous.build())
    disp=dispatch_code(); tb=task_b_code(); probe=probe_code()
    for lo,hi,data in ((DISPATCH_OFF,DISPATCH_END,disp),(TASK_B_ENTRY_OFF,TASK_B_ENTRY_END,tb),(PROBE_OFF,PROBE_END,probe)):
        if any(b!=0xff for b in rom[lo:hi]): raise ValueError(f'M2.49 ROM window {lo:#x}..{hi:#x} is not free')
        if len(data)>hi-lo: raise ValueError(f'M2.49 code exceeds window at {lo:#x}')
        rom[lo:lo+len(data)]=data
    sig=bytes.fromhex('33fc00f000dff1806000')
    window=rom[previous.PROBE_OFF:previous.PROBE_END]; rel=window.rfind(sig)
    if rel<0: raise ValueError('M2.48 success gate not found')
    branch_at=previous.PROBE_OFF+rel+8
    trampoline=None
    for candidate in range(previous.PROBE_END-6,branch_at+1,-2):
        if all(b==0xff for b in rom[candidate:candidate+6]):
            d=candidate-(branch_at+2)
            if -128<=d<=127 and d!=0: trampoline=candidate; break
    if trampoline is None: raise ValueError('no M2.48 trampoline slot for M2.49')
    rom[branch_at:branch_at+2]=bytes((0x60,(trampoline-(branch_at+2))&0xff))
    rom[trampoline:trampoline+6]=bytes.fromhex('4ef9')+l(ROM_BASE+PROBE_OFF)
    if any(b!=0xff for b in rom[META_OFF:META_OFF+0x100]): raise ValueError('M2.49 metadata window not free')
    rom[META_OFF:META_OFF+len(MARKER)]=MARKER; rom[META_OFF+0x60:META_OFF+0x60+len(IDENT)]=IDENT
    rom[runtime.MARKER_OFF:runtime.IDENT_OFF]=b'\xff'*(runtime.IDENT_OFF-runtime.MARKER_OFF); rom[runtime.MARKER_OFF:runtime.MARKER_OFF+len(MARKER)]=MARKER
    rom[runtime.IDENT_OFF:runtime.NAME_A_OFF]=b'\xff'*(runtime.NAME_A_OFF-runtime.IDENT_OFF); rom[runtime.IDENT_OFF:runtime.IDENT_OFF+len(IDENT)]=IDENT
    struct.pack_into('>I',rom,runtime.ROM_SIZE-4,0); total=0
    for off in range(0,runtime.ROM_SIZE-4,4): total=runtime.ones(total,struct.unpack_from('>I',rom,off)[0])
    total=(total&0xffffffff)+(total>>32); struct.pack_into('>I',rom,runtime.ROM_SIZE-4,(~total)&0xffffffff)
    return bytes(rom)

def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'build/librekick-m2_49.rom'); out.parent.mkdir(parents=True,exist_ok=True)
    data=build(); out.write_bytes(data)
    print(f'M2.49 ROM built: {out} ({len(data)} bytes)')
    print('scope=private ready-list dispatch; public Exec scheduler not claimed')
if __name__=='__main__': main()
