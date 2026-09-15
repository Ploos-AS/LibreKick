#!/usr/bin/env python3
"""Build deterministic LibreKick A1000.7 WCS shared-Exec payload/disk."""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import struct, sys
from librekick_exec_abi import EXEC_BASE, LIB_VERSION_OFF, LIB_REVISION_OFF, LIB_IDSTRING_OFF, EXEC_VERSION
from librekick_exec_runtime import SYSBASE_ADDR, THIS_TASK_OFF, get_sysbase_code, get_current_task_code, jsr_absolute

SECTOR_SIZE=512
ADF_SIZE=80*2*11*SECTOR_SIZE
WCS_SIZE=256*1024
WCS_BASE=0x00FC0000
RESET_SP=0x0007FFFC
ENTRY_PC=WCS_BASE+8
PAYLOAD_OFFSET=SECTOR_SIZE
MAGIC=b"LIBREKICK-A1000\0"
FORMAT_VERSION=2
PAYLOAD_MARKER=b"LIBREKICK-A1000.7\0WCS-SHARED-EXEC-TASK-RUNTIME\0"
DISK_MARKER=b"LIBREKICK-A1000.7\0KICKDISK-CONTAINER\0"
IDENT=b"exec.library\0LibreKick A1000.7 shared Exec task runtime 40.7\0"
IDENT_OFF=0x180
GETSYSBASE_OFF=0x200
GETCURRENTTASK_OFF=0x220
COLOR00=0x00DFF180
REVISION=7
TASK_SENTINEL=0x0000C700

def _ml(v,a): return bytes.fromhex("23fc")+struct.pack(">II",v,a)
def _mw(v,a): return bytes.fromhex("33fc")+struct.pack(">H",v)+struct.pack(">I",a)
def _cmp_l(v,a): return bytes.fromhex("0cb9")+struct.pack(">II",v,a)
def _cmp_w(v,a): return bytes.fromhex("0c79")+struct.pack(">H",v)+struct.pack(">I",a)
def _cmp_d0_l(v): return bytes.fromhex("0c80")+struct.pack(">I",v)
def _branch(c,op):
    p=len(c); c+=struct.pack(">HH",op,0); return p
def _patch(c,p,t):
    d=t-(p+2)
    if not -32768<=d<=32767: raise ValueError("branch displacement")
    struct.pack_into(">h",c,p+2,d)

def runtime_code():
    code=bytearray(); failures=[]
    ident_addr=WCS_BASE+IDENT_OFF
    code+=_ml(EXEC_BASE,SYSBASE_ADDR)
    code+=_mw(EXEC_VERSION,EXEC_BASE+LIB_VERSION_OFF)
    code+=_mw(REVISION,EXEC_BASE+LIB_REVISION_OFF)
    code+=_ml(ident_addr,EXEC_BASE+LIB_IDSTRING_OFF)
    code+=_ml(TASK_SENTINEL,EXEC_BASE+THIS_TASK_OFF)
    code+=_cmp_l(EXEC_BASE,SYSBASE_ADDR); failures.append(_branch(code,0x6600))
    code+=_cmp_w(EXEC_VERSION,EXEC_BASE+LIB_VERSION_OFF); failures.append(_branch(code,0x6600))
    code+=_cmp_w(REVISION,EXEC_BASE+LIB_REVISION_OFF); failures.append(_branch(code,0x6600))
    code+=_cmp_l(ident_addr,EXEC_BASE+LIB_IDSTRING_OFF); failures.append(_branch(code,0x6600))
    code+=_cmp_l(TASK_SENTINEL,EXEC_BASE+THIS_TASK_OFF); failures.append(_branch(code,0x6600))
    code+=jsr_absolute(WCS_BASE+GETSYSBASE_OFF)
    code+=_cmp_d0_l(EXEC_BASE); failures.append(_branch(code,0x6600))
    code+=jsr_absolute(WCS_BASE+GETCURRENTTASK_OFF)
    code+=_cmp_d0_l(TASK_SENTINEL); failures.append(_branch(code,0x6600))
    code+=_mw(0x00F0,COLOR00); good=_branch(code,0x6000)
    bad=len(code); code+=_mw(0x000F,COLOR00)
    idle=len(code); code+=bytes.fromhex("60fe")
    for p in failures: _patch(code,p,bad)
    _patch(code,good,idle)
    return bytes(code)

def build_payload():
    payload=bytearray(WCS_SIZE); struct.pack_into(">II",payload,0,RESET_SP,ENTRY_PC)
    code=runtime_code(); gsb=get_sysbase_code(); gct=get_current_task_code()
    if 8+len(code)>0x100: raise ValueError("A1000.7 runtime overlaps payload marker")
    payload[8:8+len(code)]=code
    payload[0x100:0x100+len(PAYLOAD_MARKER)]=PAYLOAD_MARKER
    payload[IDENT_OFF:IDENT_OFF+len(IDENT)]=IDENT
    payload[GETSYSBASE_OFF:GETSYSBASE_OFF+len(gsb)]=gsb
    payload[GETCURRENTTASK_OFF:GETCURRENTTASK_OFF+len(gct)]=gct
    return bytes(payload)

def build_disk(payload):
    image=bytearray(ADF_SIZE); digest=sha256(payload).digest()
    image[:len(MAGIC)]=MAGIC
    struct.pack_into(">IIIIII",image,16,FORMAT_VERSION,PAYLOAD_OFFSET,len(payload),WCS_BASE,ENTRY_PC,RESET_SP)
    image[40:72]=digest; image[80:80+len(DISK_MARKER)]=DISK_MARKER
    image[PAYLOAD_OFFSET:PAYLOAD_OFFSET+len(payload)]=payload
    return bytes(image)

def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else "build/a1000"); out.mkdir(parents=True,exist_ok=True)
    pp=out/"librekick-a1000.7-wcs.bin"; dp=out/"librekick-a1000.7-kickdisk.adf"
    payload=build_payload(); disk=build_disk(payload); pp.write_bytes(payload); dp.write_bytes(disk)
    print(f"A1000.7 WCS payload built: {pp} ({len(payload)} bytes)")
    print(f"A1000.7 kickdisk built: {dp} ({len(disk)} bytes)")
    print(f"exec_base=${EXEC_BASE:08x} version={EXEC_VERSION}.{REVISION} shared_primitives=GetSysBase,GetCurrentTask")
    print(f"wcs_base=${WCS_BASE:08x} entry_pc=${ENTRY_PC:08x} payload_sha256={sha256(payload).hexdigest()}")
    return 0
if __name__=="__main__": raise SystemExit(main())
