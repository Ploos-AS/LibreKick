#!/usr/bin/env python3
"""Build deterministic LibreKick A1000.11 WCS private CPU-context payload/disk."""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import struct, sys
from librekick_exec_abi import EXEC_BASE, LIB_VERSION_OFF, LIB_REVISION_OFF, LIB_IDSTRING_OFF, EXEC_VERSION
from librekick_exec_runtime import SYSBASE_ADDR, THIS_TASK_OFF, TC_SPREG_OFF, get_sysbase_code, get_current_task_code, set_current_task_code, swap_current_task_code, handoff_task_stack_code, jsr_absolute

SECTOR_SIZE=512
ADF_SIZE=80*2*11*SECTOR_SIZE
WCS_SIZE=256*1024
WCS_BASE=0x00FC0000
RESET_SP=0x0007FFFC
ENTRY_PC=WCS_BASE+8
PAYLOAD_OFFSET=SECTOR_SIZE
MAGIC=b"LIBREKICK-A1000\0"
FORMAT_VERSION=2
PAYLOAD_MARKER=b"LIBREKICK-A1000.11\0WCS-PRIVATE-CPU-CONTEXT-FRAME\0"
DISK_MARKER=b"LIBREKICK-A1000.11\0KICKDISK-CONTAINER\0"
IDENT=b"exec.library\0LibreKick A1000.11 private CPU context frame 40.11\0"
MARKER_OFF=0x800
IDENT_OFF=0x880
GETSYSBASE_OFF=0x900
GETCURRENTTASK_OFF=0x920
SETCURRENTTASK_OFF=0x940
SWAPCURRENTTASK_OFF=0x960
HANDOFFTASKSTACK_OFF=0x980
CONTEXT_HANDOFF_OFF=0xA00
CONTEXT_RESUME_OFF=0xB00
COLOR00=0x00DFF180
REVISION=11
TASK_SENTINEL=0x0000C700
TASK_REPLACEMENT=0x0000C900
NEW_STACK_RETURN=0x0000D7F0
TC_SPLOWER_OFF=0x3A
TC_SPUPPER_OFF=0x3E
ORIGINAL_SP_CELL=0x0000CB00
CALLER_PC_CELL=0x0000CB04
ORIGINAL_SR_CELL=0x0000CB08
RETURNED_SR_CELL=0x0000CB0A
TRANSFER_SP_CELL=0x0000CB0C
RESUME_SP_CELL=0x0000CB10
ARRIVED_CELL=0x0000CB14
ARRIVED_MAGIC=0x4C4B3131
OBS_BASE=0x0000CB20
D_REGS=list(range(2,8))
A_REGS=list(range(2,7))
REG_ORDER=[('D',r) for r in D_REGS]+[('A',r) for r in A_REGS]
D_VALUES={r:0x11000000|r for r in D_REGS}
A_VALUES={r:0x0000E100|r for r in A_REGS}
D_CLOBBERS={r:0xCC000000|r for r in D_REGS}
A_CLOBBERS={r:0x0000F100|r for r in A_REGS}
OBS_CELLS={(k,r):OBS_BASE+i*4 for i,(k,r) in enumerate(REG_ORDER)}

def _opw(w): return struct.pack('>H',w)
def _ml(v,a): return bytes.fromhex("23fc")+struct.pack(">II",v,a)
def _mw(v,a): return bytes.fromhex("33fc")+struct.pack(">H",v)+struct.pack(">I",a)
def _cmp_l(v,a): return bytes.fromhex("0cb9")+struct.pack(">II",v,a)
def _cmp_w(v,a): return bytes.fromhex("0c79")+struct.pack(">H",v)+struct.pack(">I",a)
def _cmp_d0_l(v): return bytes.fromhex("0c80")+struct.pack(">I",v)
def _move_d0_l(v): return bytes.fromhex("203c")+struct.pack(">I",v)
def _branch(c,op): p=len(c); c+=struct.pack(">HH",op,0); return p
def _patch(c,p,t):
    d=t-(p+2)
    if not -32768<=d<=32767: raise ValueError("branch displacement")
    struct.pack_into(">h",c,p+2,d)
def _push_d(r): return _opw(0x2F00+r)
def _push_a(r): return _opw(0x2F08+r)
def _pop_d(r): return _opw(0x201F+(r<<9))
def _pop_a(r): return _opw(0x205F+(r<<9))
def _imm_d(r,v): return _opw(0x203C+(r<<9))+struct.pack('>I',v)
def _imm_a(r,v): return _opw(0x207C+(r<<9))+struct.pack('>I',v)
def _store_d(r,a): return _opw(0x23C0+r)+struct.pack('>I',a)
def _store_a(r,a): return _opw(0x23C8+r)+struct.pack('>I',a)

def context_handoff_code():
    q=bytearray()
    q+=bytes.fromhex('40F9')+struct.pack('>I',ORIGINAL_SR_CELL)       # MOVE SR,(abs).W semantics via absolute long
    q+=bytes.fromhex('2279')+struct.pack('>I',EXEC_BASE+THIS_TASK_OFF)
    q+=bytes.fromhex('2029')+struct.pack('>H',TC_SPREG_OFF)
    q+=bytes.fromhex('23CF')+struct.pack('>I',ORIGINAL_SP_CELL)
    q+=bytes.fromhex('2217')
    q+=bytes.fromhex('23C1')+struct.pack('>I',CALLER_PC_CELL)
    q+=bytes.fromhex('2E40')
    q+=bytes.fromhex('3F39')+struct.pack('>I',ORIGINAL_SR_CELL)
    for r in D_REGS: q+=_push_d(r)
    for r in A_REGS: q+=_push_a(r)
    for r in D_REGS: q+=_imm_d(r,D_CLOBBERS[r])
    for r in A_REGS: q+=_imm_a(r,A_CLOBBERS[r])
    q+=bytes.fromhex('0A3C001F')
    q+=bytes.fromhex('2F3C')+struct.pack('>I',WCS_BASE+CONTEXT_RESUME_OFF)
    q+=bytes.fromhex('23CF')+struct.pack('>I',TRANSFER_SP_CELL)
    q+=bytes.fromhex('4E75')
    return bytes(q)

def context_resume_code():
    q=bytearray()
    q+=bytes.fromhex('23CF')+struct.pack('>I',RESUME_SP_CELL)
    q+=_ml(ARRIVED_MAGIC,ARRIVED_CELL)
    for r in reversed(A_REGS): q+=_pop_a(r)+_store_a(r,OBS_CELLS[('A',r)])
    for r in reversed(D_REGS): q+=_pop_d(r)+_store_d(r,OBS_CELLS[('D',r)])
    q+=bytes.fromhex('46DF')
    q+=bytes.fromhex('2E79')+struct.pack('>I',ORIGINAL_SP_CELL)
    q+=bytes.fromhex('4E75')
    return bytes(q)

def runtime_code():
    code=bytearray(); failures=[]; ident_addr=WCS_BASE+IDENT_OFF
    code+=_ml(EXEC_BASE,SYSBASE_ADDR)
    code+=_mw(EXEC_VERSION,EXEC_BASE+LIB_VERSION_OFF)
    code+=_mw(REVISION,EXEC_BASE+LIB_REVISION_OFF)
    code+=_ml(ident_addr,EXEC_BASE+LIB_IDSTRING_OFF)
    code+=_ml(TASK_REPLACEMENT,EXEC_BASE+THIS_TASK_OFF)
    code+=_ml(0x0000D000,TASK_REPLACEMENT+TC_SPLOWER_OFF)
    code+=_ml(0x0000D800,TASK_REPLACEMENT+TC_SPUPPER_OFF)
    code+=_ml(NEW_STACK_RETURN,TASK_REPLACEMENT+TC_SPREG_OFF)
    for a in (ORIGINAL_SP_CELL,CALLER_PC_CELL,TRANSFER_SP_CELL,RESUME_SP_CELL,ARRIVED_CELL): code+=_ml(0,a)
    code+=_mw(0,ORIGINAL_SR_CELL); code+=_mw(0,RETURNED_SR_CELL)
    for a in OBS_CELLS.values(): code+=_ml(0,a)
    code+=_cmp_l(EXEC_BASE,SYSBASE_ADDR); failures.append(_branch(code,0x6600))
    code+=_cmp_w(EXEC_VERSION,EXEC_BASE+LIB_VERSION_OFF); failures.append(_branch(code,0x6600))
    code+=_cmp_w(REVISION,EXEC_BASE+LIB_REVISION_OFF); failures.append(_branch(code,0x6600))
    for r in D_REGS: code+=_imm_d(r,D_VALUES[r])
    for r in A_REGS: code+=_imm_a(r,A_VALUES[r])
    jsr_pos=len(code); code+=jsr_absolute(WCS_BASE+CONTEXT_HANDOFF_OFF)
    expected_return=WCS_BASE+8+jsr_pos+6
    code+=bytes.fromhex('40F9')+struct.pack('>I',RETURNED_SR_CELL)
    frame_low=NEW_STACK_RETURN-2-4*len(REG_ORDER); transfer_sp=frame_low-4
    code+=_cmp_l(transfer_sp,TRANSFER_SP_CELL); failures.append(_branch(code,0x6600))
    code+=_cmp_l(frame_low,RESUME_SP_CELL); failures.append(_branch(code,0x6600))
    code+=_cmp_l(WCS_BASE+CONTEXT_RESUME_OFF,transfer_sp); failures.append(_branch(code,0x6600))
    code+=_cmp_l(ARRIVED_MAGIC,ARRIVED_CELL); failures.append(_branch(code,0x6600))
    code+=_cmp_l(expected_return,CALLER_PC_CELL); failures.append(_branch(code,0x6600))
    for r in D_REGS: code+=_cmp_l(D_VALUES[r],OBS_CELLS[('D',r)]); failures.append(_branch(code,0x6600))
    for r in A_REGS: code+=_cmp_l(A_VALUES[r],OBS_CELLS[('A',r)]); failures.append(_branch(code,0x6600))
    code+=bytes.fromhex('3039')+struct.pack('>I',ORIGINAL_SR_CELL)
    code+=bytes.fromhex('B079')+struct.pack('>I',RETURNED_SR_CELL); failures.append(_branch(code,0x6600))
    code+=_mw(0x00F0,COLOR00); good=_branch(code,0x6000)
    bad=len(code); code+=_mw(0x000F,COLOR00); idle=len(code); code+=bytes.fromhex('60fe')
    for p in failures: _patch(code,p,bad)
    _patch(code,good,idle)
    return bytes(code)

def build_payload():
    payload=bytearray(WCS_SIZE); struct.pack_into(">II",payload,0,RESET_SP,ENTRY_PC)
    code=runtime_code(); helpers=[(GETSYSBASE_OFF,get_sysbase_code()),(GETCURRENTTASK_OFF,get_current_task_code()),(SETCURRENTTASK_OFF,set_current_task_code()),(SWAPCURRENTTASK_OFF,swap_current_task_code()),(HANDOFFTASKSTACK_OFF,handoff_task_stack_code()),(CONTEXT_HANDOFF_OFF,context_handoff_code()),(CONTEXT_RESUME_OFF,context_resume_code())]
    if 8+len(code)>MARKER_OFF: raise ValueError("A1000.11 runtime overlaps payload marker")
    payload[8:8+len(code)]=code
    payload[MARKER_OFF:MARKER_OFF+len(PAYLOAD_MARKER)]=PAYLOAD_MARKER
    payload[IDENT_OFF:IDENT_OFF+len(IDENT)]=IDENT
    for off,data in helpers: payload[off:off+len(data)]=data
    return bytes(payload)

def build_disk(payload):
    image=bytearray(ADF_SIZE); digest=sha256(payload).digest(); image[:len(MAGIC)]=MAGIC
    struct.pack_into(">IIIIII",image,16,FORMAT_VERSION,PAYLOAD_OFFSET,len(payload),WCS_BASE,ENTRY_PC,RESET_SP)
    image[40:72]=digest; image[80:80+len(DISK_MARKER)]=DISK_MARKER; image[PAYLOAD_OFFSET:PAYLOAD_OFFSET+len(payload)]=payload
    return bytes(image)

def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else "build/a1000"); out.mkdir(parents=True,exist_ok=True)
    pp=out/"librekick-a1000.11-wcs.bin"; dp=out/"librekick-a1000.11-kickdisk.adf"
    payload=build_payload(); disk=build_disk(payload); pp.write_bytes(payload); dp.write_bytes(disk)
    print(f"A1000.11 WCS payload built: {pp} ({len(payload)} bytes)")
    print(f"A1000.11 kickdisk built: {dp} ({len(disk)} bytes)")
    print(f"exec_base=${EXEC_BASE:08x} version={EXEC_VERSION}.{REVISION} context=SR,D2-D7,A2-A6")
    print(f"wcs_base=${WCS_BASE:08x} entry_pc=${ENTRY_PC:08x} payload_sha256={sha256(payload).hexdigest()}")
    print("scope=private defined CPU context frame; public Exec scheduler and full task switching not claimed")
    return 0
if __name__=="__main__": raise SystemExit(main())
