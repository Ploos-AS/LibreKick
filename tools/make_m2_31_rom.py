#!/usr/bin/env python3
"""Build LibreKick M2.31: minimal Exec SetSignal current-task signal-state slice."""
from pathlib import Path
import struct, sys
import make_m2_30_rom as p
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.31\0EXEC-SETSIGNAL-CURRENT\0'
IDENT=b'exec.library\0LibreKick M2.31 SetSignal current-task signal slice 40.31\0'
PROBE_OFF=0x3300
PROBE_END=0x3500
SETSIGNAL_OFF=0x3500
SETSIGNAL_END=0x3540
SIGNAL_CELL=0x00004C14


def setsignal_code():
    """D0=newSignals, D1=signalSet -> D0=old signals.

    M2.31 keeps signal state in a dedicated bootstrap current-task cell. Later
    task milestones can move the state into the real Task layout without
    changing the public SetSignal ABI qualified here.
    """
    q=bytearray(bytes.fromhex('2F022F03'))                  # save d2,d3
    q+=bytes.fromhex('2439')+struct.pack('>I',SIGNAL_CELL)  # d2=old
    q+=bytes.fromhex('2601')                                # d3=mask
    q+=bytes.fromhex('4683')                                # not.l d3
    q+=bytes.fromhex('C483')                                # d2 &= ~mask
    q+=bytes.fromhex('C081')                                # d0 &= mask
    q+=bytes.fromhex('8480')                                # d2 |= d0
    q+=bytes.fromhex('2039')+struct.pack('>I',SIGNAL_CELL)  # d0=old return value
    q+=bytes.fromhex('23C2')+struct.pack('>I',SIGNAL_CELL)  # cell=new state
    q+=bytes.fromhex('261F241F4E75')                        # restore d3,d2; RTS
    return bytes(q)


def build():
    image=bytearray(p.build())

    # Chain M2.30 success into the next task/signal slice.
    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0:
        raise ValueError('M2.30 final success gate not found')
    good_abs=p.PROBE_OFF+gp
    branch_pos=good_abs+8
    test_abs=PROBE_OFF

    routine=setsignal_code()
    if SETSIGNAL_OFF+len(routine)>SETSIGNAL_END:
        raise ValueError('M2.31 SetSignal routine exceeds dedicated ROM window')
    if any(b != 0xff for b in image[SETSIGNAL_OFF:SETSIGNAL_END]):
        raise ValueError('M2.31 SetSignal routine window is not unused')
    image[SETSIGNAL_OFF:SETSIGNAL_OFF+len(routine)]=routine

    c=bytearray(); fails=[]
    # Install SetSignal at Exec LVO -306 and establish current-task signal state.
    c+=m.vector(m.ROM_BASE+SETSIGNAL_OFF,m.EXEC_BASE-306)
    c+=m.ml(0x12345678,SIGNAL_CELL)
    c+=bytes.fromhex('4DF9')+struct.pack('>I',m.EXEC_BASE)   # a6=ExecBase

    def set_signal(new,mask,old_expect,state_expect):
        nonlocal c
        c+=bytes.fromhex('203C')+struct.pack('>I',new)
        c+=bytes.fromhex('223C')+struct.pack('>I',mask)
        c+=bytes.fromhex('4EAEFECE')                         # SetSignal LVO -306
        fails.append(m.cmpd0(c,old_expect))
        fails.append(m.cmpabs(c,state_expect,SIGNAL_CELL))

    # Replace selected low-nibble bits while returning the previous state.
    set_signal(0x00000003,0x0000000F,0x12345678,0x12345673)
    # Selective clear.
    set_signal(0x00000000,0x00000003,0x12345673,0x12345670)
    # Selective set.
    set_signal(0xFFFFFFFF,0x0000000C,0x12345670,0x1234567C)
    # Zero mask must be a read-only operation even with arbitrary newSignals.
    set_signal(0xDEADBEEF,0x00000000,0x1234567C,0x1234567C)

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails:
        m.patch(c,fail,bad)
    m.patch(c,ok,idle)

    if test_abs+len(c)>PROBE_END:
        raise ValueError('M2.31 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[test_abs:test_abs+len(c)]):
        raise ValueError('M2.31 runtime probe window is not unused')
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
        raise SystemExit('usage: make_m2_31_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.31 ROM built: {out} ({len(data)} bytes)')
