#!/usr/bin/env python3
"""Build LibreKick M2.38: small register-context frame on the task stack."""
from pathlib import Path
import struct, sys
import make_m2_37_rom as p
import make_m2_34_rom as a
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.38\0EXEC-CONTEXT-REGFRAME\0'
IDENT=b'exec.library\0LibreKick M2.38 small register-context frame slice 40.38\0'
PROBE_OFF=0x4900
PROBE_END=0x4B00
CONTEXT_OFF=0x4B00
CONTEXT_END=0x4B60

ORIGINAL_SP_CELL=0x00004C24
FRAME_SP_CELL=0x00004C28
RESTORED_D2_CELL=0x00004C2C
RESTORED_A2_CELL=0x00004C30

D2_VALUE=0x12345678
A2_VALUE=0x0000E240
D2_CLOBBER=0xDEADBEEF
A2_CLOBBER=0x0000E2F0


def context_code():
    """Save/restore D2 and A2 on ThisTask's stack, then return to caller.

    M2.38 is still only a bounded context-frame primitive. It proves a small
    register subset can survive an A7 handoff by using the selected task stack
    as the save area. It does not save SR/PC or perform task-to-task transfer.
    """
    q=bytearray()
    q+=bytes.fromhex('2279')+struct.pack('>I',p.p.p.THIS_TASK)      # a1=ThisTask
    q+=bytes.fromhex('2029')+struct.pack('>H',p.p.TC_SPREG)        # d0=tc_SPReg
    q+=bytes.fromhex('23CF')+struct.pack('>I',ORIGINAL_SP_CELL)    # save caller a7
    q+=bytes.fromhex('2E40')                                       # a7=d0
    q+=bytes.fromhex('2F02')                                       # move.l d2,-(a7)
    q+=bytes.fromhex('2F0A')                                       # move.l a2,-(a7)
    q+=bytes.fromhex('23CF')+struct.pack('>I',FRAME_SP_CELL)       # frame low address
    q+=bytes.fromhex('243C')+struct.pack('>I',D2_CLOBBER)          # clobber d2
    q+=bytes.fromhex('247C')+struct.pack('>I',A2_CLOBBER)          # clobber a2
    q+=bytes.fromhex('245F')                                       # movea.l (a7)+,a2
    q+=bytes.fromhex('241F')                                       # move.l (a7)+,d2
    q+=bytes.fromhex('23C2')+struct.pack('>I',RESTORED_D2_CELL)    # observe restored d2
    q+=bytes.fromhex('23CA')+struct.pack('>I',RESTORED_A2_CELL)    # observe restored a2
    q+=bytes.fromhex('2E79')+struct.pack('>I',ORIGINAL_SP_CELL)    # restore caller a7
    q+=bytes.fromhex('4E75')                                       # RTS
    return bytes(q)


def build():
    image=bytearray(p.build())

    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0:
        raise ValueError('M2.37 final success gate not found')
    good_abs=p.PROBE_OFF+gp
    branch_pos=good_abs+8
    test_abs=PROBE_OFF

    routine=context_code()
    if CONTEXT_OFF+len(routine)>CONTEXT_END:
        raise ValueError('M2.38 register-context helper exceeds dedicated ROM window')
    if any(b != 0xff for b in image[CONTEXT_OFF:CONTEXT_END]):
        raise ValueError('M2.38 register-context helper window is not unused')
    image[CONTEXT_OFF:CONTEXT_OFF+len(routine)]=routine

    c=bytearray(); fails=[]

    # Task B remains ThisTask. Its stack is prepared in safe RAM. D2 and A2 are
    # caller-selected values that must survive save -> clobber -> restore on the
    # task stack. Push order D2 then A2 gives A2 at SP-8 and D2 at SP-4.
    c+=m.ml(0x0000D000,a.TASK_B+p.p.TC_SPLOWER)
    c+=m.ml(0x0000D800,a.TASK_B+p.p.TC_SPUPPER)
    c+=m.ml(0x0000D7F0,a.TASK_B+p.p.TC_SPREG)
    c+=m.ml(0x00000000,0x0000D7E8)
    c+=m.ml(0x00000000,0x0000D7EC)
    c+=m.ml(0x00000000,ORIGINAL_SP_CELL)
    c+=m.ml(0x00000000,FRAME_SP_CELL)
    c+=m.ml(0x00000000,RESTORED_D2_CELL)
    c+=m.ml(0x00000000,RESTORED_A2_CELL)

    c+=bytes.fromhex('243C')+struct.pack('>I',D2_VALUE)            # d2=value
    c+=bytes.fromhex('247C')+struct.pack('>I',A2_VALUE)            # a2=value
    c+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+CONTEXT_OFF)

    fails.append(m.cmpabs(c,A2_VALUE,0x0000D7E8))
    fails.append(m.cmpabs(c,D2_VALUE,0x0000D7EC))
    fails.append(m.cmpabs(c,0x0000D7E8,FRAME_SP_CELL))
    fails.append(m.cmpabs(c,D2_VALUE,RESTORED_D2_CELL))
    fails.append(m.cmpabs(c,A2_VALUE,RESTORED_A2_CELL))
    fails.append(m.cmpabs(c,a.TASK_B,p.p.p.THIS_TASK))
    fails.append(m.cmpabs(c,0x0000D7F0,a.TASK_B+p.p.TC_SPREG))

    # A second independent frame catches fixed-address or stale-state bugs.
    c+=m.ml(0x0000D6C0,a.TASK_B+p.p.TC_SPREG)
    c+=m.ml(0x00000000,0x0000D6B8)
    c+=m.ml(0x00000000,0x0000D6BC)
    c+=bytes.fromhex('243C')+struct.pack('>I',0x89ABCDEF)
    c+=bytes.fromhex('247C')+struct.pack('>I',0x0000E280)
    c+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+CONTEXT_OFF)
    fails.append(m.cmpabs(c,0x0000E280,0x0000D6B8))
    fails.append(m.cmpabs(c,0x89ABCDEF,0x0000D6BC))
    fails.append(m.cmpabs(c,0x0000D6B8,FRAME_SP_CELL))
    fails.append(m.cmpabs(c,0x89ABCDEF,RESTORED_D2_CELL))
    fails.append(m.cmpabs(c,0x0000E280,RESTORED_A2_CELL))

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails:
        m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if test_abs+len(c)>PROBE_END:
        raise ValueError('M2.38 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[test_abs:test_abs+len(c)]):
        raise ValueError('M2.38 runtime probe window is not unused')
    image[test_abs:test_abs+len(c)]=c
    struct.pack_into('>h',image,branch_pos+2,test_abs-(branch_pos+2))

    image[m.MARKER_OFF:m.IDENT_OFF]=b'\xff'*(m.IDENT_OFF-m.MARKER_OFF)
    image[m.MARKER_OFF:m.MARKER_OFF+len(MARKER)]=MARKER
    image[m.IDENT_OFF:m.NAME_A_OFF]=b'\xff'*(m.NAME_A_OFF-m.IDENT_OFF)
    image[m.IDENT_OFF:m.IDENT_OFF+len(IDENT)]=IDENT

    struct.pack_into('>I',image,m.ROM_SIZE-4,0)
    total=0
    for off in range(0,m.ROM_SIZE-4,4):
        total=m.ones(total,struct.unpack_from('>I',image,off)[0])
    total=(total&0xffffffff)+(total>>32)
    struct.pack_into('>I',image,m.ROM_SIZE-4,(~total)&0xffffffff)
    return image


if __name__=='__main__':
    if len(sys.argv)!=2:
        raise SystemExit('usage: make_m2_38_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.38 ROM built: {out} ({len(data)} bytes)')
