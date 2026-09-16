#!/usr/bin/env python3
"""Static validation for LibreKick A1000.9 shared-Exec WCS payload/disk."""
from hashlib import sha256
from pathlib import Path
import struct,sys
from librekick_exec_abi import EXEC_BASE,LIB_VERSION_OFF,LIB_REVISION_OFF,LIB_IDSTRING_OFF,EXEC_VERSION
from librekick_exec_runtime import SYSBASE_ADDR,THIS_TASK_OFF,get_sysbase_code,get_current_task_code,set_current_task_code,swap_current_task_code
import make_a1000_2_kickdisk as builder

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else "build/a1000")
    pp=root/"librekick-a1000.9-wcs.bin"; dp=root/"librekick-a1000.9-kickdisk.adf"
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
    assert payload[0x100:0x100+len(builder.PAYLOAD_MARKER)]==builder.PAYLOAD_MARKER
    assert payload[builder.IDENT_OFF:builder.IDENT_OFF+len(builder.IDENT)]==builder.IDENT
    gsb=get_sysbase_code(); gct=get_current_task_code(); sct=set_current_task_code(); swp=swap_current_task_code()
    assert payload[builder.GETSYSBASE_OFF:builder.GETSYSBASE_OFF+len(gsb)]==gsb
    assert payload[builder.GETCURRENTTASK_OFF:builder.GETCURRENTTASK_OFF+len(gct)]==gct
    assert payload[builder.SETCURRENTTASK_OFF:builder.SETCURRENTTASK_OFF+len(sct)]==sct
    assert payload[builder.SWAPCURRENTTASK_OFF:builder.SWAPCURRENTTASK_OFF+len(swp)]==swp
    assert gsb==bytes.fromhex("2039000000044e75")
    assert gct==bytes.fromhex("207900000004202801144e75")
    assert sct==bytes.fromhex("207900000004214001144e75")
    assert swp==bytes.fromhex("207900000004222801142140011420014e75")
    assert SYSBASE_ADDR==4 and THIS_TASK_OFF==0x114 and EXEC_BASE==0x3400
    assert (LIB_VERSION_OFF,LIB_REVISION_OFF,LIB_IDSTRING_OFF)==(20,22,24) and EXEC_VERSION==40
    assert struct.pack(">I",builder.TASK_SENTINEL) in code
    assert struct.pack(">I",builder.TASK_REPLACEMENT) in code
    print(f"A1000.9 static check PASS: {dp} ({len(disk)} bytes)")
    print(f"WCS payload={len(payload)} bytes load=${load_addr:08x} entry=${entry_pc:08x}")
    print(f"shared_exec=ExecBase@${EXEC_BASE:08x} version={EXEC_VERSION}.{builder.REVISION} primitives=GetSysBase,GetCurrentTask,SetCurrentTask,SwapCurrentTask")
    print(f"payload_sha256={sha256(payload).hexdigest()}")
    print("format=LibreKick-private bootstrap container v2; task-pointer swap is private; public scheduler/full Exec compatibility not claimed")
    return 0
if __name__=="__main__": raise SystemExit(main())
