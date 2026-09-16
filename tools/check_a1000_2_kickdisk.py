#!/usr/bin/env python3
"""Static validation for LibreKick A1000.10 task-stack handoff WCS payload/disk."""
from hashlib import sha256
from pathlib import Path
import struct,sys
from librekick_exec_abi import EXEC_BASE,LIB_VERSION_OFF,LIB_REVISION_OFF,LIB_IDSTRING_OFF,EXEC_VERSION
from librekick_exec_runtime import SYSBASE_ADDR,THIS_TASK_OFF,TC_SPREG_OFF,get_sysbase_code,get_current_task_code,set_current_task_code,swap_current_task_code,handoff_task_stack_code
import make_a1000_2_kickdisk as builder

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else "build/a1000")
    pp=root/"librekick-a1000.10-wcs.bin"; dp=root/"librekick-a1000.10-kickdisk.adf"
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
    gsb=get_sysbase_code(); gct=get_current_task_code(); sct=set_current_task_code(); swp=swap_current_task_code(); hts=handoff_task_stack_code()
    assert payload[builder.GETSYSBASE_OFF:builder.GETSYSBASE_OFF+len(gsb)]==gsb
    assert payload[builder.GETCURRENTTASK_OFF:builder.GETCURRENTTASK_OFF+len(gct)]==gct
    assert payload[builder.SETCURRENTTASK_OFF:builder.SETCURRENTTASK_OFF+len(sct)]==sct
    assert payload[builder.SWAPCURRENTTASK_OFF:builder.SWAPCURRENTTASK_OFF+len(swp)]==swp
    assert payload[builder.HANDOFFTASKSTACK_OFF:builder.HANDOFFTASKSTACK_OFF+len(hts)]==hts
    resume=builder.resume_code(); assert payload[builder.RESUME_OFF:builder.RESUME_OFF+len(resume)]==resume
    assert hts==bytes.fromhex("20790000000422680114234f003622092240214001142e69003620014e75")
    assert SYSBASE_ADDR==4 and THIS_TASK_OFF==0x114 and TC_SPREG_OFF==0x36 and EXEC_BASE==0x3400
    assert (LIB_VERSION_OFF,LIB_REVISION_OFF,LIB_IDSTRING_OFF)==(20,22,24) and EXEC_VERSION==40
    assert struct.pack(">I",builder.TASK_SENTINEL) in code
    assert struct.pack(">I",builder.TASK_REPLACEMENT) in code
    assert struct.pack(">I",builder.NEW_STACK_RETURN) in code
    assert struct.pack(">I",builder.WCS_BASE+builder.RESUME_OFF) in code
    print(f"A1000.10 static check PASS: {dp} ({len(disk)} bytes)")
    print(f"WCS payload={len(payload)} bytes load=${load_addr:08x} entry=${entry_pc:08x}")
    print(f"shared_exec=ExecBase@${EXEC_BASE:08x} version={EXEC_VERSION}.{builder.REVISION} primitives=GetSysBase,GetCurrentTask,SetCurrentTask,SwapCurrentTask,HandoffTaskStack")
    print(f"task_stack=tc_SPReg+0x{TC_SPREG_OFF:02x} prepared_stack=${builder.NEW_STACK_RETURN:08x} resume=${builder.WCS_BASE+builder.RESUME_OFF:08x}")
    print(f"payload_sha256={sha256(payload).hexdigest()}")
    print("scope=private cooperative stack handoff; complete register/SR context switch and public Exec scheduler not claimed")
    return 0
if __name__=="__main__": raise SystemExit(main())
