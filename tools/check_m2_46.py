#!/usr/bin/env python3
"""Static validation for LibreKick M2.46."""
from pathlib import Path
import struct,sys
import make_m2_46_rom as b
from librekick_exec_runtime import handoff_task_stack_code,TC_SPREG_OFF

def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)

def main():
    p=Path(sys.argv[1] if len(sys.argv)>1 else "build/librekick-m2_46.rom"); data=p.read_bytes()
    assert len(data)==512*1024
    helper=handoff_task_stack_code(); assert helper==bytes.fromhex("20790000000422680114234f003622092240214001142e69003620014e75")
    assert data[b.HANDOFF_OFF:b.HANDOFF_OFF+len(helper)]==helper
    probe=b.probe_code(); assert data[b.PROBE_OFF:b.PROBE_OFF+len(probe)]==probe
    resume=b.resume_code(); assert data[b.RESUME_OFF:b.RESUME_OFF+len(resume)]==resume
    assert b.MARKER in data and b.IDENT in data
    assert TC_SPREG_OFF==0x36
    assert struct.pack(">I",b.TASK_A) in probe and struct.pack(">I",b.TASK_B) in probe and struct.pack(">I",b.NEW_STACK_RETURN) in probe
    assert bytes.fromhex("33fc00f000dff18060fe") in probe and bytes.fromhex("33fc000f00dff18060fe") in probe
    t=0
    for off in range(0,len(data),4):
        t=ones(t,struct.unpack_from(">I",data,off)[0])
    t=(t&0xffffffff)+(t>>32)
    assert t==0xffffffff, f"bad checksum {t:08x}"
    print(f"M2.46 check PASS: {p} ({len(data)} bytes)")
    print(f"HandoffTaskStack=${b.ROM_BASE+b.HANDOFF_OFF:08x} tc_SPReg=+0x{TC_SPREG_OFF:02x} probe=${b.ROM_BASE+b.PROBE_OFF:08x} resume=${b.ROM_BASE+b.RESUME_OFF:08x}")
    print("Shared HandoffTaskStack reversible stack/task convergence; checksum=0xffffffff")
    print("scope=private cooperative stack handoff; complete register/SR context switch and public Exec scheduler not claimed")
    return 0
if __name__=="__main__": raise SystemExit(main())
