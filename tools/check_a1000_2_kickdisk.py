#!/usr/bin/env python3
"""Static validation for LibreKick A1000.11 private CPU-context WCS payload/disk."""
from hashlib import sha256
from pathlib import Path
import struct,sys
from librekick_exec_abi import EXEC_BASE,LIB_VERSION_OFF,LIB_REVISION_OFF,LIB_IDSTRING_OFF,EXEC_VERSION
from librekick_exec_runtime import SYSBASE_ADDR,THIS_TASK_OFF,TC_SPREG_OFF,get_sysbase_code,get_current_task_code,set_current_task_code,swap_current_task_code,handoff_task_stack_code
import make_a1000_2_kickdisk as builder

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else "build/a1000")
    pp=root/"librekick-a1000.11-wcs.bin"; dp=root/"librekick-a1000.11-kickdisk.adf"
    payload=pp.read_bytes(); disk=dp.read_bytes()
    assert len(payload)==builder.WCS_SIZE and len(disk)==builder.ADF_SIZE
    assert disk[:len(builder.MAGIC)]==builder.MAGIC
    version,offset,length,load_addr,entry_pc,reset_sp=struct.unpack_from(">IIIIII",disk,16)
    assert version==builder.FORMAT_VERSION and offset==builder.PAYLOAD_OFFSET and length==builder.WCS_SIZE
    assert (load_addr,entry_pc,reset_sp)==(builder.WCS_BASE,builder.ENTRY_PC,builder.RESET_SP)
    assert disk[40:72]==sha256(payload).digest() and disk[offset:offset+length]==payload
    assert disk[80:80+len(builder.DISK_MARKER)]==builder.DISK_MARKER
    assert struct.unpack_from(">II",payload,0)==(builder.RESET_SP,builder.ENTRY_PC)
    code=builder.runtime_code(); assert payload[8:8+len(code)]==code
    assert payload[builder.MARKER_OFF:builder.MARKER_OFF+len(builder.PAYLOAD_MARKER)]==builder.PAYLOAD_MARKER
    assert payload[builder.IDENT_OFF:builder.IDENT_OFF+len(builder.IDENT)]==builder.IDENT
    helpers=((builder.GETSYSBASE_OFF,get_sysbase_code()),(builder.GETCURRENTTASK_OFF,get_current_task_code()),(builder.SETCURRENTTASK_OFF,set_current_task_code()),(builder.SWAPCURRENTTASK_OFF,swap_current_task_code()),(builder.HANDOFFTASKSTACK_OFF,handoff_task_stack_code()),(builder.CONTEXT_HANDOFF_OFF,builder.context_handoff_code()),(builder.CONTEXT_RESUME_OFF,builder.context_resume_code()))
    for off,data in helpers: assert payload[off:off+len(data)]==data
    assert SYSBASE_ADDR==4 and THIS_TASK_OFF==0x114 and TC_SPREG_OFF==0x36 and EXEC_BASE==0x3400
    assert (LIB_VERSION_OFF,LIB_REVISION_OFF,LIB_IDSTRING_OFF)==(20,22,24) and EXEC_VERSION==40
    assert builder.REVISION==11
    assert builder.D_REGS==list(range(2,8)) and builder.A_REGS==list(range(2,7))
    assert struct.pack(">I",builder.ARRIVED_MAGIC) in builder.context_resume_code()
    assert struct.pack(">I",builder.WCS_BASE+builder.CONTEXT_RESUME_OFF) in builder.context_handoff_code()
    assert bytes.fromhex('3F39')+struct.pack('>I',builder.ORIGINAL_SR_CELL) in builder.context_handoff_code()
    assert bytes.fromhex('46DF') in builder.context_resume_code()
    print(f"A1000.11 static check PASS: {dp} ({len(disk)} bytes)")
    print(f"WCS payload={len(payload)} bytes load=${load_addr:08x} entry=${entry_pc:08x}")
    print(f"shared_exec=ExecBase@${EXEC_BASE:08x} version={EXEC_VERSION}.{builder.REVISION}")
    print("context_frame=SR,D2-D7,A2-A6; private save/restore round trip")
    print(f"payload_sha256={sha256(payload).hexdigest()}")
    print("scope=private defined CPU context frame; public Exec scheduler and full task switching not claimed")
    return 0
if __name__=="__main__": raise SystemExit(main())
