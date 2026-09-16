#!/usr/bin/env python3
"""Build LibreKick M2.47 with a private SR/D2-D7/A2-A6 CPU context frame."""
from __future__ import annotations
import struct, sys
from pathlib import Path
import make_m2_46_rom as previous
import make_m2_17_rom as runtime
from librekick_exec_abi import EXEC_BASE
from librekick_exec_runtime import THIS_TASK_OFF, TC_SPREG_OFF

ROM_BASE=runtime.ROM_BASE
COLOR00=runtime.COLOR00
CONTEXT_HANDOFF_OFF=0x6B00
CONTEXT_HANDOFF_END=0x6C00
CONTEXT_RESUME_OFF=0x6C00
CONTEXT_RESUME_END=0x6D00
PROBE_OFF=0x6D00
PROBE_END=0x6E00
META_OFF=0x6E00
TASK=0x0000CA47
ORIGINAL_SP_CELL=0x0000CC00
CALLER_PC_CELL=0x0000CC04
ORIGINAL_SR_CELL=0x0000CC08
RETURNED_SR_CELL=0x0000CC0A
TRANSFER_SP_CELL=0x0000CC0C
RESUME_SP_CELL=0x0000CC10
ARRIVED_CELL=0x0000CC14
ARRIVED_MAGIC=0x4C4B3247
OBS_BASE=0x0000CC20
D_REGS=list(range(2,8)); A_REGS=list(range(2,7))
REG_ORDER=[('D',r) for r in D_REGS]+[('A',r) for r in A_REGS]
D_VALUES={r:0x12000000|r for r in D_REGS}; A_VALUES={r:0x0000E200|r for r in A_REGS}
D_CLOBBERS={r:0xCD000000|r for r in D_REGS}; A_CLOBBERS={r:0x0000F200|r for r in A_REGS}
OBS_CELLS={(k,r):OBS_BASE+i*4 for i,(k,r) in enumerate(REG_ORDER)}
MARKER=b"LIBREKICK-M2.47\0SHARED-PRIVATE-CPU-CONTEXT-FRAME\0"
IDENT=b"exec.library\0LibreKick M2.47 private CPU context frame 40.47\0"

def _opw(w): return struct.pack('>H',w)
def _ml(v,a): return bytes.fromhex('23fc')+struct.pack('>II',v,a)
def _mw(v,a): return bytes.fromhex('33fc')+struct.pack('>H',v)+struct.pack('>I',a)
def _cmp_l(v,a): return bytes.fromhex('0cb9')+struct.pack('>II',v,a)
def _branch(c,op): p=len(c); c+=struct.pack('>HH',op,0); return p
def _patch(c,p,t): struct.pack_into('>h',c,p+2,t-(p+2))
def _push_d(r): return _opw(0x2F00+r)
def _push_a(r): return _opw(0x2F08+r)
def _pop_d(r): return _opw(0x201F+(r<<9))
def _pop_a(r): return _opw(0x205F+(r<<9))
def _imm_d(r,v): return _opw(0x203C+(r<<9))+struct.pack('>I',v)
def _imm_a(r,v): return _opw(0x207C+(r<<9))+struct.pack('>I',v)
def _store_d(r,a): return _opw(0x23C0+r)+struct.pack('>I',a)
def _store_a(r,a): return _opw(0x23C8+r)+struct.pack('>I',a)
def _jsr(a): return bytes.fromhex('4eb9')+struct.pack('>I',a)

def context_handoff_code():
    q=bytearray()
    q+=bytes.fromhex('40F9')+struct.pack('>I',ORIGINAL_SR_CELL)
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
    q+=bytes.fromhex('2F3C')+struct.pack('>I',ROM_BASE+CONTEXT_RESUME_OFF)
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

def probe_code():
    c=bytearray(); bad=[]
    c+=_ml(TASK,EXEC_BASE+THIS_TASK_OFF); c+=_ml(0,TASK+TC_SPREG_OFF)
    for a in (ORIGINAL_SP_CELL,CALLER_PC_CELL,TRANSFER_SP_CELL,RESUME_SP_CELL,ARRIVED_CELL): c+=_ml(0,a)
    c+=_mw(0,ORIGINAL_SR_CELL); c+=_mw(0,RETURNED_SR_CELL)
    for a in OBS_CELLS.values(): c+=_ml(0,a)
    for r in D_REGS: c+=_imm_d(r,D_VALUES[r])
    for r in A_REGS: c+=_imm_a(r,A_VALUES[r])
    jsr_pos=len(c); c+=_jsr(ROM_BASE+CONTEXT_HANDOFF_OFF)
    expected_return=ROM_BASE+PROBE_OFF+jsr_pos+6
    c+=bytes.fromhex('40F9')+struct.pack('>I',RETURNED_SR_CELL)
    c+=_cmp_l(ARRIVED_MAGIC,ARRIVED_CELL); bad.append(_branch(c,0x6600))
    c+=_cmp_l(expected_return,CALLER_PC_CELL); bad.append(_branch(c,0x6600))
    for r in D_REGS: c+=_cmp_l(D_VALUES[r],OBS_CELLS[('D',r)]); bad.append(_branch(c,0x6600))
    for r in A_REGS: c+=_cmp_l(A_VALUES[r],OBS_CELLS[('A',r)]); bad.append(_branch(c,0x6600))
    c+=bytes.fromhex('3039')+struct.pack('>I',ORIGINAL_SR_CELL)
    c+=bytes.fromhex('B079')+struct.pack('>I',RETURNED_SR_CELL); bad.append(_branch(c,0x6600))
    c+=_mw(0x00F0,COLOR00); good=_branch(c,0x6000)
    fail=len(c); c+=_mw(0x000F,COLOR00); idle=len(c); c+=bytes.fromhex('60fe')
    for p in bad: _patch(c,p,fail)
    _patch(c,good,idle)
    return bytes(c)

def build():
    rom=bytearray(previous.build())
    hand=context_handoff_code(); resume=context_resume_code(); probe=probe_code()
    for lo,hi,data in ((CONTEXT_HANDOFF_OFF,CONTEXT_HANDOFF_END,hand),(CONTEXT_RESUME_OFF,CONTEXT_RESUME_END,resume),(PROBE_OFF,PROBE_END,probe)):
        if any(b!=0xFF for b in rom[lo:hi]): raise ValueError(f'M2.47 ROM window {lo:#x}..{hi:#x} is not free')
        if len(data)>hi-lo: raise ValueError(f'M2.47 code exceeds window at {lo:#x}')
        rom[lo:lo+len(data)]=data
    sig=bytes.fromhex('33fc00f000dff1806000')
    window=rom[previous.PROBE_OFF:previous.PROBE_END]; rel=window.rfind(sig)
    if rel<0: raise ValueError('M2.46 success gate not found')
    branch=previous.PROBE_OFF+rel+8; struct.pack_into('>h',rom,branch+2,PROBE_OFF-(branch+2))
    if any(b!=0xFF for b in rom[META_OFF:META_OFF+0x100]): raise ValueError('M2.47 metadata window not free')
    rom[META_OFF:META_OFF+len(MARKER)]=MARKER; rom[META_OFF+0x60:META_OFF+0x60+len(IDENT)]=IDENT
    rom[runtime.MARKER_OFF:runtime.IDENT_OFF]=b'\xff'*(runtime.IDENT_OFF-runtime.MARKER_OFF); rom[runtime.MARKER_OFF:runtime.MARKER_OFF+len(MARKER)]=MARKER
    rom[runtime.IDENT_OFF:runtime.NAME_A_OFF]=b'\xff'*(runtime.NAME_A_OFF-runtime.IDENT_OFF); rom[runtime.IDENT_OFF:runtime.IDENT_OFF+len(IDENT)]=IDENT
    struct.pack_into('>I',rom,runtime.ROM_SIZE-4,0); total=0
    for off in range(0,runtime.ROM_SIZE-4,4): total=runtime.ones(total,struct.unpack_from('>I',rom,off)[0])
    total=(total&0xffffffff)+(total>>32); struct.pack_into('>I',rom,runtime.ROM_SIZE-4,(~total)&0xffffffff)
    return bytes(rom)

def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'build/librekick-m2_47.rom'); out.parent.mkdir(parents=True,exist_ok=True); data=build(); out.write_bytes(data)
    print(f'M2.47 ROM built: {out} ({len(data)} bytes)')
    print('context=SR,D2-D7,A2-A6; scope=private context frame, public Exec scheduler not claimed')
if __name__=='__main__': main()
