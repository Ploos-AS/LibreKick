#!/usr/bin/env python3
"""Build LibreKick M2.12: AvailMem MEMF_LARGEST semantics across CHIP/FAST regions."""
from pathlib import Path
import struct, sys
from make_m2_11_rom import (
    ROM_SIZE, ROM_BASE, SP, PC, EXEC_BASE, COLOR00, CIAA_PRA, CIAA_DDRA,
    MEMHDR, MEM_BASE, MEM_SIZE, MH_ATTR, MH_FIRST, MH_LOWER, MH_UPPER, MH_FREE,
    FAST_HDR, FAST_BASE, FAST_SIZE, MARKER_OFF, IDENT_OFF,
    ml, mw, mb, bclr0, vector, branch, patch, cmpd0, cmpabs, ones,
    alloc_wrapper_code, free_wrapper_code, relocate_region,
    allocmem_core_code, freemem_code,
    CHIP_ALLOC_OFF, CHIP_FREE_OFF, FAST_ALLOC_OFF, FAST_FREE_OFF,
    MEMF_CHIP, MEMF_FAST, MEMF_CLEAR, MEMF_TOTAL,
)

MEMF_LARGEST=0x00020000
IDSTRING_ADDR=ROM_BASE+IDENT_OFF
CHIP_LARGEST_OFF=0x1200
FAST_LARGEST_OFF=0x1300
FUNCS={198:ROM_BASE+0x0B00,210:ROM_BASE+0x0C00,216:ROM_BASE+0x0D00}


def largest_code(header):
    """Return largest mc_Bytes in one MemHeader free-list."""
    q=bytearray(bytes.fromhex('2F012F022F08'))              # save d1,d2,a0
    q+=bytes.fromhex('2079')+struct.pack('>I',header+MH_FIRST)
    q+=bytes.fromhex('7000')                                # d0=largest=0
    loop=len(q)
    q+=bytes.fromhex('22084A81'); done=branch(q,0x6700)     # current==NULL
    q+=bytes.fromhex('24280004')                            # d2=current.bytes
    q+=bytes.fromhex('B082'); keep=branch(q,0x6400)         # cmp.l d2,d0; d0>=d2
    q+=bytes.fromhex('2002')                                # d0=d2
    nxt=len(q); q+=bytes.fromhex('2050')                    # a0=current.next
    again=branch(q,0x6000)
    out=len(q); q+=bytes.fromhex('205F241F221F4E75')
    patch(q,done,out); patch(q,keep,nxt); patch(q,again,loop)
    return bytes(q)


def avail_wrapper_code():
    """AvailMem total-free or largest-block across the two qualified regions."""
    q=bytearray(bytes.fromhex('2F022F03'))                  # save d2,d3
    q+=bytes.fromhex('08010011')                            # MEMF_LARGEST bit 17?
    largest=branch(q,0x6600)

    # Normal free-total path, retaining M2.11 region filtering.
    q+=bytes.fromhex('08010002')                            # FAST?
    t_fast=branch(q,0x6600)
    q+=bytes.fromhex('08010001')                            # CHIP?
    t_chip=branch(q,0x6600)
    q+=bytes.fromhex('2039')+struct.pack('>I',MEMHDR+MH_FREE)
    q+=bytes.fromhex('2439')+struct.pack('>I',FAST_HDR+MH_FREE)
    q+=bytes.fromhex('D082')                                # combined total free
    t_done0=branch(q,0x6000)
    tf=len(q)
    q+=bytes.fromhex('08010001')                            # CHIP also => conflict
    t_both=branch(q,0x6600)
    q+=bytes.fromhex('2039')+struct.pack('>I',FAST_HDR+MH_FREE)
    t_done1=branch(q,0x6000)
    tc=len(q)
    q+=bytes.fromhex('2039')+struct.pack('>I',MEMHDR+MH_FREE)
    t_done2=branch(q,0x6000)

    # Largest-block path.
    lp=len(q)
    q+=bytes.fromhex('08010002')                            # FAST?
    l_fast=branch(q,0x6600)
    q+=bytes.fromhex('08010001')                            # CHIP?
    l_chip=branch(q,0x6600)
    # Neither region bit: largest matching block across both regions.
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+CHIP_LARGEST_OFF)
    q+=bytes.fromhex('2400')                                # d2=chip largest
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+FAST_LARGEST_OFF)
    q+=bytes.fromhex('B480')                                # cmp.l d0,d2
    keep_fast=branch(q,0x6500)                              # d2 < d0 => keep d0
    q+=bytes.fromhex('2002')                                # else d0=d2
    l_done0=branch(q,0x6000)
    lf=len(q)
    q+=bytes.fromhex('08010001')                            # CHIP also => conflict
    l_both=branch(q,0x6600)
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+FAST_LARGEST_OFF)
    l_done1=branch(q,0x6000)
    lc=len(q)
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+CHIP_LARGEST_OFF)
    l_done2=branch(q,0x6000)

    bad=len(q); q+=bytes.fromhex('7000')
    done=len(q); q+=bytes.fromhex('261F241F4E75')

    patch(q,largest,lp)
    patch(q,t_fast,tf); patch(q,t_chip,tc); patch(q,t_both,bad)
    patch(q,t_done0,done); patch(q,t_done1,done); patch(q,t_done2,done)
    patch(q,l_fast,lf); patch(q,l_chip,lc); patch(q,l_both,bad)
    patch(q,keep_fast,l_done0); patch(q,l_done0,done); patch(q,l_done1,done); patch(q,l_done2,done)
    return bytes(q)


def build():
    image=bytearray([0xff])*ROM_SIZE
    struct.pack_into('>II',image,0,SP,PC)
    c=bytearray(bytes.fromhex('46FC2700'))
    c+=mb(3,CIAA_DDRA); c+=bclr0(CIAA_PRA); c+=ml(EXEC_BASE,4)
    c+=ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)
    c+=mw(0,EXEC_BASE+14)+mw(216,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(12,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
    for off,t in FUNCS.items(): c+=vector(t,EXEC_BASE-off)

    # Same two logical regions qualified in M2.11.
    c+=mw(MEMF_CHIP,MEMHDR+MH_ATTR)+ml(MEM_BASE,MEMHDR+MH_FIRST)+ml(MEM_BASE,MEMHDR+MH_LOWER)+ml(MEM_BASE+MEM_SIZE,MEMHDR+MH_UPPER)+ml(MEM_SIZE,MEMHDR+MH_FREE)
    c+=ml(0,MEM_BASE)+ml(MEM_SIZE,MEM_BASE+4)
    c+=mw(MEMF_FAST,FAST_HDR+MH_ATTR)+ml(FAST_BASE,FAST_HDR+MH_FIRST)+ml(FAST_BASE,FAST_HDR+MH_LOWER)+ml(FAST_BASE+FAST_SIZE,FAST_HDR+MH_UPPER)+ml(FAST_SIZE,FAST_HDR+MH_FREE)
    c+=ml(0,FAST_BASE)+ml(FAST_SIZE,FAST_BASE+4)

    c+=mw(0x0f00,COLOR00)+b'\x4d\xf9'+struct.pack('>I',EXEC_BASE)
    fails=[]
    def avail(flags,expect):
        nonlocal c
        c+=bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF28')
        fails.append(cmpd0(c,expect))
    def alloc(size,flags,expect):
        nonlocal c
        c+=bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF3A')
        fails.append(cmpd0(c,expect))
    def free(addr,size):
        nonlocal c
        c+=bytes.fromhex('227C')+struct.pack('>I',addr)+bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('4EAEFF2E')

    # Baseline: combined largest is one region, not the sum.
    avail(MEMF_LARGEST,0x1000)
    avail(MEMF_CHIP|MEMF_LARGEST,0x1000)
    avail(MEMF_FAST|MEMF_LARGEST,0x1000)

    # Fragment CHIP: free list becomes $5000/$100 -> $5300/$D00.
    alloc(0x100,MEMF_CHIP,MEM_BASE)
    alloc(0x200,MEMF_CHIP,MEM_BASE+0x100)
    alloc(0x100,MEMF_CHIP,MEM_BASE+0x300)
    free(MEM_BASE,0x100)
    free(MEM_BASE+0x300,0x100)
    avail(MEMF_CHIP,0x0E00)
    avail(MEMF_CHIP|MEMF_LARGEST,0x0D00)
    avail(MEMF_TOTAL,0x1E00)
    avail(MEMF_LARGEST,0x1000)                              # FAST still intact

    # Shrink FAST largest below CHIP's largest; combined largest must now be CHIP D00.
    alloc(0x400,MEMF_FAST,FAST_BASE)
    avail(MEMF_FAST,0x0C00)
    avail(MEMF_FAST|MEMF_LARGEST,0x0C00)
    avail(MEMF_LARGEST,0x0D00)
    avail(MEMF_TOTAL,0x1A00)
    avail(MEMF_CHIP|MEMF_FAST|MEMF_LARGEST,0)

    # Restore both regions and re-check totals/largest.
    free(FAST_BASE,0x400)
    free(MEM_BASE+0x100,0x200)
    avail(MEMF_CHIP,MEM_SIZE); avail(MEMF_FAST,FAST_SIZE)
    avail(MEMF_TOTAL,MEM_SIZE+FAST_SIZE); avail(MEMF_LARGEST,0x1000)
    fails.append(cmpabs(c,MEM_BASE,MEMHDR+MH_FIRST)); fails.append(cmpabs(c,MEM_SIZE,MEM_BASE+4))
    fails.append(cmpabs(c,FAST_BASE,FAST_HDR+MH_FIRST)); fails.append(cmpabs(c,FAST_SIZE,FAST_BASE+4))

    c+=mw(0x00f0,COLOR00); done_branch=branch(c,0x6000)
    bad=len(c); c+=mw(0x000f,COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for p in fails: patch(c,p,bad)
    patch(c,done_branch,idle)
    if 8+len(c)>0x0B00: raise ValueError('bootstrap overlaps M2.12 routines')
    image[8:8+len(c)]=c

    fast_alloc=relocate_region(allocmem_core_code(),MEMHDR,FAST_HDR)
    fast_free=relocate_region(freemem_code(),MEMHDR,FAST_HDR)
    routines={
        0x0B00:alloc_wrapper_code(),
        0x0C00:free_wrapper_code(),
        0x0D00:avail_wrapper_code(),
        CHIP_ALLOC_OFF:allocmem_core_code(),
        CHIP_FREE_OFF:freemem_code(),
        FAST_ALLOC_OFF:fast_alloc,
        FAST_FREE_OFF:fast_free,
        CHIP_LARGEST_OFF:largest_code(MEMHDR),
        FAST_LARGEST_OFF:largest_code(FAST_HDR),
    }
    ordered=sorted(routines.items())
    for (off,code),(nxt,_) in zip(ordered,ordered[1:]+[(MARKER_OFF,b'')]):
        if off+len(code)>nxt: raise ValueError(f'routine overlap at {off:x}')
        image[off:off+len(code)]=code

    marker=b'LIBREKICK-M2.12\0EXEC-AVAILMEM-LARGEST\0'
    ident=b'exec.library\0LibreKick M2.12 AvailMem MEMF_LARGEST slice 40.12\0'
    image[MARKER_OFF:MARKER_OFF+len(marker)]=marker
    image[IDENT_OFF:IDENT_OFF+len(ident)]=ident
    struct.pack_into('>I',image,ROM_SIZE-4,0)
    total=0
    for o in range(0,ROM_SIZE-4,4): total=ones(total,struct.unpack_from('>I',image,o)[0])
    total=(total&0xffffffff)+(total>>32)
    struct.pack_into('>I',image,ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_12_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.12 ROM built: {out} ({len(data)} bytes)')
