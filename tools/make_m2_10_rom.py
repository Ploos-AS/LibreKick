#!/usr/bin/env python3
"""Build LibreKick M2.10: MEMF_CLEAR + first requirement filtering slice."""
from pathlib import Path
import struct, sys
from make_m2_9_rom import (
    ROM_SIZE, ROM_BASE, SP, PC, EXEC_BASE, COLOR00, CIAA_PRA, CIAA_DDRA,
    MEMHDR, MEM_BASE, MEM_SIZE, MH_ATTR, MH_FIRST, MH_LOWER, MH_UPPER, MH_FREE,
    MARKER_OFF, IDENT_OFF, ml, mw, mb, bclr0, vector, branch, patch, cmpd0,
    cmpabs, ones, allocmem_code as allocmem_core_code,
    freemem_code, availmem_code, MEMF_CHIP, MEMF_TOTAL,
)

IDSTRING_ADDR=ROM_BASE+IDENT_OFF
MEMF_FAST=0x0004
MEMF_CLEAR=0x00010000
ALLOC_CORE_OFF=0x0E00
FUNCS={198:ROM_BASE+0x0B00,210:ROM_BASE+0x0C00,216:ROM_BASE+0x0D00}


def allocmem_wrapper_code():
    """Filter requirements, call first-fit core, and clear successful allocations."""
    q=bytearray(bytes.fromhex('2F022F032F08'))               # save d2,d3,a0
    q+=bytes.fromhex('24002601')                             # d2=size, d3=requirements
    q+=bytes.fromhex('08030002')                             # btst #2,d3 (MEMF_FAST)
    reject=branch(q,0x6600)                                  # BNE reject
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+ALLOC_CORE_OFF)
    q+=bytes.fromhex('4A80'); done_null=branch(q,0x6700)      # allocation failed
    q+=bytes.fromhex('08030010')                             # btst #16,d3 (MEMF_CLEAR)
    done_plain=branch(q,0x6700)                              # no clearing requested
    q+=bytes.fromhex('2040')                                 # a0=d0
    q+=bytes.fromhex('0682000000070282FFFFFFF8')             # align saved size to 8
    loop=len(q)
    q+=bytes.fromhex('4298')                                 # clr.l (a0)+
    q+=bytes.fromhex('5982')                                 # subq.l #4,d2
    more=branch(q,0x6600)
    done=len(q)
    q+=bytes.fromhex('205F261F241F4E75')                    # restore; preserve d0
    bad=len(q)
    q+=bytes.fromhex('7000')                                 # return NULL
    bad_done=branch(q,0x6000)
    patch(q,reject,bad); patch(q,done_null,done); patch(q,done_plain,done)
    patch(q,more,loop); patch(q,bad_done,done)
    return bytes(q)


def build():
    image=bytearray([0xff])*ROM_SIZE
    struct.pack_into('>II',image,0,SP,PC)
    c=bytearray(bytes.fromhex('46FC2700'))
    c+=mb(3,CIAA_DDRA); c+=bclr0(CIAA_PRA); c+=ml(EXEC_BASE,4)
    c+=ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)
    c+=mw(0,EXEC_BASE+14)+mw(216,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(10,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
    for off,t in FUNCS.items(): c+=vector(t,EXEC_BASE-off)
    c+=mw(MEMF_CHIP,MEMHDR+MH_ATTR)+ml(MEM_BASE,MEMHDR+MH_FIRST)+ml(MEM_BASE,MEMHDR+MH_LOWER)+ml(MEM_BASE+MEM_SIZE,MEMHDR+MH_UPPER)+ml(MEM_SIZE,MEMHDR+MH_FREE)
    c+=ml(0,MEM_BASE)+ml(MEM_SIZE,MEM_BASE+4)
    # Seed payload bytes with nonzero data so MEMF_CLEAR proves more than header clearing.
    for off,val in ((8,0x11223344),(12,0x55667788),(16,0xA5A5A5A5),(20,0xDEADBEEF),(24,0xCAFEBABE),(28,0x01020304)):
        c+=ml(val,MEM_BASE+off)
    c+=mw(0x0f00,COLOR00)+b'\x4d\xf9'+struct.pack('>I',EXEC_BASE)
    fails=[]
    # FAST cannot be satisfied by this CHIP-only MemHeader and must not consume memory.
    c+=bytes.fromhex('203C00000020223C000000044EAEFF3A')
    fails.append(cmpd0(c,0))
    c+=bytes.fromhex('223C000800004EAEFF28'); fails.append(cmpd0(c,MEM_SIZE))
    fails.append(cmpabs(c,MEM_BASE,MEMHDR+MH_FIRST)); fails.append(cmpabs(c,MEM_SIZE,MEM_BASE+4))
    # CHIP|CLEAR allocation must succeed and clear every longword of the 0x20-byte block.
    c+=bytes.fromhex('203C00000020223C000100024EAEFF3A')
    fails.append(cmpd0(c,MEM_BASE))
    for off in range(0,0x20,4): fails.append(cmpabs(c,0,MEM_BASE+off))
    c+=bytes.fromhex('223C000800004EAEFF28'); fails.append(cmpd0(c,MEM_SIZE-0x20))
    # Return block and require complete restoration.
    c+=bytes.fromhex('227C')+struct.pack('>I',MEM_BASE)+bytes.fromhex('203C000000204EAEFF2E')
    c+=bytes.fromhex('223C000800004EAEFF28'); fails.append(cmpd0(c,MEM_SIZE))
    fails.append(cmpabs(c,MEM_BASE,MEMHDR+MH_FIRST)); fails.append(cmpabs(c,0,MEM_BASE)); fails.append(cmpabs(c,MEM_SIZE,MEM_BASE+4))
    c+=mw(0x00f0,COLOR00); done=branch(c,0x6000)
    bad=len(c); c+=mw(0x000f,COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for p in fails: patch(c,p,bad)
    patch(c,done,idle)
    if 8+len(c)>0x0B00: raise ValueError('bootstrap overlaps allocator wrapper')
    image[8:8+len(c)]=c
    routines={
        0x0B00:allocmem_wrapper_code(),
        0x0C00:freemem_code(),
        0x0D00:availmem_code(),
        ALLOC_CORE_OFF:allocmem_core_code(),
    }
    ordered=sorted(routines.items())
    for (off,code),(nxt,_) in zip(ordered,ordered[1:]+[(MARKER_OFF,b'')]):
        if off+len(code)>nxt: raise ValueError(f'routine overlap at {off:x}')
        image[off:off+len(code)]=code
    marker=b'LIBREKICK-M2.10\0EXEC-MEMF-CLEAR-REQUIREMENTS\0'
    ident=b'exec.library\0LibreKick M2.10 MEMF_CLEAR and requirement filter slice 40.10\0'
    image[MARKER_OFF:MARKER_OFF+len(marker)]=marker
    image[IDENT_OFF:IDENT_OFF+len(ident)]=ident
    struct.pack_into('>I',image,ROM_SIZE-4,0)
    total=0
    for o in range(0,ROM_SIZE-4,4): total=ones(total,struct.unpack_from('>I',image,o)[0])
    total=(total&0xffffffff)+(total>>32)
    struct.pack_into('>I',image,ROM_SIZE-4,(~total)&0xffffffff)
    return image


if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_10_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.10 ROM built: {out} ({len(data)} bytes)')
