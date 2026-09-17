#!/usr/bin/env python3
"""Build deterministic LibreKick A1000.12 WCS two-task switch payload/disk."""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import struct, sys
import make_a1000_2_kickdisk as previous
from librekick_exec_abi import EXEC_BASE, LIB_VERSION_OFF, LIB_REVISION_OFF, LIB_IDSTRING_OFF, EXEC_VERSION
from librekick_exec_runtime import SYSBASE_ADDR, THIS_TASK_OFF, TC_SPREG_OFF

SECTOR_SIZE=previous.SECTOR_SIZE; ADF_SIZE=previous.ADF_SIZE; WCS_SIZE=previous.WCS_SIZE
WCS_BASE=previous.WCS_BASE; RESET_SP=previous.RESET_SP; ENTRY_PC=previous.ENTRY_PC
PAYLOAD_OFFSET=previous.PAYLOAD_OFFSET; MAGIC=previous.MAGIC; FORMAT_VERSION=previous.FORMAT_VERSION
COLOR00=previous.COLOR00
REVISION=12
PAYLOAD_MARKER=b"LIBREKICK-A1000.12\0WCS-PRIVATE-TWO-TASK-CONTEXT-SWITCH\0"
DISK_MARKER=b"LIBREKICK-A1000.12\0KICKDISK-CONTAINER\0"
IDENT=b"exec.library\0LibreKick A1000.12 private two-task context switch 40.12\0"
MARKER_OFF=0xC00; IDENT_OFF=0xC80; SWITCH_OFF=0xD00; TASK_B_ENTRY_OFF=0xE00
TASK_A=0x0000CE00; TASK_B=0x0000CE80; STACK_B_TOP=0x0000EC00
B_SEEN=0x0000CD00; A_SEEN=0x0000CD04; B_MAGIC=0x42313030; A_MAGIC=0x41313030
D_REGS=list(range(2,8)); A_REGS=list(range(2,7))
A_D={r:0xA1000000|r for r in D_REGS}; A_A={r:0x0000A100|r for r in A_REGS}
B_D={r:0xB1000000|r for r in D_REGS}; B_A={r:0x0000B100|r for r in A_REGS}

def w(v): return struct.pack('>H',v)
def l(v): return struct.pack('>I',v)
def ml(v,a): return bytes.fromhex('23fc')+l(v)+l(a)
def mw(v,a): return bytes.fromhex('33fc')+w(v)+l(a)
def cmp_l(v,a): return bytes.fromhex('0cb9')+l(v)+l(a)
def imm_d(r,v): return w(0x203c+(r<<9))+l(v)
def imm_a(r,v): return w(0x207c+(r<<9))+l(v)
def push_d(r): return w(0x2f00+r)
def push_a(r): return w(0x2f08+r)
def pop_d(r): return w(0x201f+(r<<9))
def pop_a(r): return w(0x205f+(r<<9))
def jsr(a): return bytes.fromhex('4eb9')+l(a)
def branch(c,op): p=len(c); c+=w(op)+w(0); return p
def patch(c,p,t): struct.pack_into('>h',c,p+2,t-(p+2))

def switch_code():
    q=bytearray()
    q+=bytes.fromhex('40e7')
    for r in D_REGS: q+=push_d(r)
    for r in A_REGS: q+=push_a(r)
    q+=bytes.fromhex('227900000004')             # MOVEA.L $4,A1
    q+=bytes.fromhex('22690114')                 # MOVEA.L ThisTask(A1),A1
    q+=bytes.fromhex('234f0036')                 # MOVE.L A7,tc_SPReg(A1)
    q+=bytes.fromhex('227900000004')             # MOVEA.L $4,A1
    q+=bytes.fromhex('21400114')                 # MOVE.L A0,ThisTask(A1)
    q+=bytes.fromhex('2e680036')                 # MOVEA.L tc_SPReg(A0),A7
    for r in reversed(A_REGS): q+=pop_a(r)
    for r in reversed(D_REGS): q+=pop_d(r)
    q+=bytes.fromhex('46df4e75')                 # MOVE (A7)+,SR ; RTS
    return bytes(q)

def prepared_frame(entry,dvals,avals):
    # Stack layout consumed by switch_code: A6..A2, D7..D2, SR, then RTS PC.
    q=bytearray()
    for r in reversed(A_REGS): q+=l(avals[r])
    for r in reversed(D_REGS): q+=l(dvals[r])
    q+=w(0x2000)+l(entry)
    return bytes(q)

def task_b_code():
    c=bytearray(); fails=[]
    c+=cmp_l(TASK_B,EXEC_BASE+THIS_TASK_OFF); fails.append(branch(c,0x6600))
    for r in D_REGS: c+=w(0x0c80+r)+l(B_D[r]); fails.append(branch(c,0x6600))
    for r in A_REGS:
        c+=w(0x2048+r)+bytes.fromhex('b1fc')+l(B_A[r]); fails.append(branch(c,0x6600))
    c+=ml(B_MAGIC,B_SEEN)
    c+=imm_a(0,TASK_A)+jsr(WCS_BASE+SWITCH_OFF)
    bad=len(c); c+=mw(0x000f,COLOR00)+bytes.fromhex('60fe')
    for p in fails: patch(c,p,bad)
    return bytes(c)

def runtime_code():
    c=bytearray(); fails=[]; ident_addr=WCS_BASE+IDENT_OFF
    c+=ml(EXEC_BASE,SYSBASE_ADDR)+mw(EXEC_VERSION,EXEC_BASE+LIB_VERSION_OFF)+mw(REVISION,EXEC_BASE+LIB_REVISION_OFF)+ml(ident_addr,EXEC_BASE+LIB_IDSTRING_OFF)
    c+=ml(TASK_A,EXEC_BASE+THIS_TASK_OFF)+ml(0,B_SEEN)+ml(0,A_SEEN)
    frame=prepared_frame(WCS_BASE+TASK_B_ENTRY_OFF,B_D,B_A); frame_sp=STACK_B_TOP-len(frame)
    for off in range(0,len(frame),4):
        chunk=frame[off:off+4]
        if len(chunk)==4: c+=ml(struct.unpack('>I',chunk)[0],frame_sp+off)
        else: c+=mw(struct.unpack('>H',chunk)[0],frame_sp+off)
    c+=ml(frame_sp,TASK_B+TC_SPREG_OFF)
    for r in D_REGS: c+=imm_d(r,A_D[r])
    for r in A_REGS: c+=imm_a(r,A_A[r])
    c+=imm_a(0,TASK_B)+jsr(WCS_BASE+SWITCH_OFF)
    c+=ml(A_MAGIC,A_SEEN)
    c+=cmp_l(TASK_A,EXEC_BASE+THIS_TASK_OFF); fails.append(branch(c,0x6600))
    c+=cmp_l(B_MAGIC,B_SEEN); fails.append(branch(c,0x6600))
    for r in D_REGS: c+=w(0x0c80+r)+l(A_D[r]); fails.append(branch(c,0x6600))
    for r in A_REGS:
        c+=w(0x2048+r)+bytes.fromhex('b1fc')+l(A_A[r]); fails.append(branch(c,0x6600))
    c+=mw(0x00f0,COLOR00); good=branch(c,0x6000)
    bad=len(c); c+=mw(0x000f,COLOR00); idle=len(c); c+=bytes.fromhex('60fe')
    for p in fails: patch(c,p,bad)
    patch(c,good,idle)
    return bytes(c)

def build_payload():
    payload=bytearray(WCS_SIZE); struct.pack_into('>II',payload,0,RESET_SP,ENTRY_PC)
    code=runtime_code(); sw=switch_code(); tb=task_b_code()
    if 8+len(code)>MARKER_OFF: raise ValueError('A1000.12 runtime overlaps marker')
    if SWITCH_OFF+len(sw)>TASK_B_ENTRY_OFF: raise ValueError('A1000.12 switch overlaps task B entry')
    payload[8:8+len(code)]=code; payload[MARKER_OFF:MARKER_OFF+len(PAYLOAD_MARKER)]=PAYLOAD_MARKER; payload[IDENT_OFF:IDENT_OFF+len(IDENT)]=IDENT
    payload[SWITCH_OFF:SWITCH_OFF+len(sw)]=sw; payload[TASK_B_ENTRY_OFF:TASK_B_ENTRY_OFF+len(tb)]=tb
    return bytes(payload)

def build_disk(payload):
    image=bytearray(ADF_SIZE); digest=sha256(payload).digest(); image[:len(MAGIC)]=MAGIC
    struct.pack_into('>IIIIII',image,16,FORMAT_VERSION,PAYLOAD_OFFSET,len(payload),WCS_BASE,ENTRY_PC,RESET_SP)
    image[40:72]=digest; image[80:80+len(DISK_MARKER)]=DISK_MARKER; image[PAYLOAD_OFFSET:PAYLOAD_OFFSET+len(payload)]=payload
    return bytes(image)

def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'build/a1000'); out.mkdir(parents=True,exist_ok=True)
    pp=out/'librekick-a1000.12-wcs.bin'; dp=out/'librekick-a1000.12-kickdisk.adf'
    payload=build_payload(); disk=build_disk(payload); pp.write_bytes(payload); dp.write_bytes(disk)
    print(f'A1000.12 WCS payload built: {pp} ({len(payload)} bytes)')
    print(f'A1000.12 kickdisk built: {dp} ({len(disk)} bytes)')
    print(f'exec_base=${EXEC_BASE:08x} version={EXEC_VERSION}.{REVISION} context=SR,D2-D7,A2-A6 tasks=A,B')
    print(f'payload_sha256={sha256(payload).hexdigest()}')
    print('scope=private deterministic two-task switch; public Exec scheduler not claimed')
    return 0
if __name__=='__main__': raise SystemExit(main())
