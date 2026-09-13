#!/usr/bin/env python3
"""Build LibreKick M2.33: minimal Exec Wait immediate-ready signal slice."""
from pathlib import Path
import struct, sys
import make_m2_32_rom as p
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.33\0EXEC-WAIT-READY\0'
IDENT=b'exec.library\0LibreKick M2.33 Wait immediate-ready signal slice 40.33\0'
PROBE_OFF=0x3900
PROBE_END=0x3B00
WAIT_OFF=0x3B00
WAIT_END=0x3B40


def wait_code():
    """D0=signalSet -> D0=ready signals, clearing returned bits.

    M2.33 qualifies only the immediate-ready path for the single bootstrap task.
    If no requested signal is pending this provisional routine returns zero;
    scheduler-backed blocking is deliberately deferred and is not qualified.
    """
    q=bytearray(bytes.fromhex('2F012F02'))                  # save d1,d2
    q+=bytes.fromhex('2239')+struct.pack('>I',p.p.SIGNAL_CELL) # d1=current signals
    q+=bytes.fromhex('C081')                                # d0 &= d1 (ready)
    q+=bytes.fromhex('2400')                                # d2=ready
    q+=bytes.fromhex('4682')                                # d2=~ready
    q+=bytes.fromhex('C282')                                # d1 &= d2
    q+=bytes.fromhex('23C1')+struct.pack('>I',p.p.SIGNAL_CELL) # store remaining
    q+=bytes.fromhex('241F221F4E75')                        # restore d2,d1; RTS
    return bytes(q)


def build():
    image=bytearray(p.build())

    # Chain the M2.32 success gate into the Wait probe.
    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0:
        raise ValueError('M2.32 final success gate not found')
    good_abs=p.PROBE_OFF+gp
    branch_pos=good_abs+8
    test_abs=PROBE_OFF

    routine=wait_code()
    if WAIT_OFF+len(routine)>WAIT_END:
        raise ValueError('M2.33 Wait routine exceeds dedicated ROM window')
    if any(b != 0xff for b in image[WAIT_OFF:WAIT_END]):
        raise ValueError('M2.33 Wait routine window is not unused')
    image[WAIT_OFF:WAIT_OFF+len(routine)]=routine

    c=bytearray(); fails=[]
    # Install Wait at Exec LVO -318 and start with no pending signals.
    c+=m.vector(m.ROM_BASE+WAIT_OFF,m.EXEC_BASE-318)
    c+=m.ml(0x00000000,p.p.SIGNAL_CELL)
    c+=bytes.fromhex('4DF9')+struct.pack('>I',m.EXEC_BASE)   # a6=ExecBase

    # Resolve the current bootstrap task and use already-qualified Signal() to
    # populate pending signals before each immediate-ready Wait() operation.
    c+=bytes.fromhex('227C000000004EAEFEDA2240')           # FindTask(NULL); a1=d0

    def signal(mask,state_expect):
        nonlocal c
        c+=bytes.fromhex('203C')+struct.pack('>I',mask)
        c+=bytes.fromhex('4EAEFEBC')                         # Signal LVO -324
        fails.append(m.cmpabs(c,state_expect,p.p.SIGNAL_CELL))

    def wait(mask,result_expect,state_expect):
        nonlocal c
        c+=bytes.fromhex('203C')+struct.pack('>I',mask)
        c+=bytes.fromhex('4EAEFEC2')                         # Wait LVO -318
        fails.append(m.cmpd0(c,result_expect))
        fails.append(m.cmpabs(c,state_expect,p.p.SIGNAL_CELL))

    signal(0x00000015,0x00000015)
    wait(0x00000005,0x00000005,0x00000010)

    signal(0x8000000A,0x8000001A)
    wait(0x0000000A,0x0000000A,0x80000010)
    wait(0x80000010,0x80000010,0x00000000)

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails:
        m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if test_abs+len(c)>PROBE_END:
        raise ValueError('M2.33 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[test_abs:test_abs+len(c)]):
        raise ValueError('M2.33 runtime probe window is not unused')
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
        raise SystemExit('usage: make_m2_33_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.33 ROM built: {out} ({len(data)} bytes)')
