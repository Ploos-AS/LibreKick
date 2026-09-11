#!/usr/bin/env python3
"""Build LibreKick M2.13: first AddMemList dynamic-region slice.

This slice adds the public AddMemList() ABI and dynamically registers one
additional logical memory region. The existing CHIP/FAST allocators remain the
M2.12 qualified paths; dynamic AllocMem routing is deferred to M2.14.
"""
from pathlib import Path
import struct, sys
from make_m2_12_rom import (
    ROM_SIZE, ROM_BASE, SP, PC, EXEC_BASE, COLOR00, CIAA_PRA, CIAA_DDRA,
    MEMHDR, MEM_BASE, MEM_SIZE, MH_ATTR, MH_FIRST, MH_LOWER, MH_UPPER, MH_FREE,
    FAST_HDR, FAST_BASE, FAST_SIZE,
    ml, mw, mb, bclr0, vector, branch, patch, cmpd0, cmpabs, ones,
    alloc_wrapper_code, free_wrapper_code, avail_wrapper_code as base_avail_code,
    relocate_region, allocmem_core_code, freemem_code, largest_code,
    CHIP_ALLOC_OFF, CHIP_FREE_OFF, FAST_ALLOC_OFF, FAST_FREE_OFF,
    CHIP_LARGEST_OFF, FAST_LARGEST_OFF,
    MEMF_CHIP, MEMF_FAST, MEMF_CLEAR, MEMF_TOTAL, MEMF_LARGEST,
)

MARKER_OFF=0x1800
IDENT_OFF=0x1880
IDSTRING_ADDR=ROM_BASE+IDENT_OFF
DYN_NAME_OFF=0x18E0
DYN_NAME_ADDR=ROM_BASE+DYN_NAME_OFF
DYN_SLOT=0x00004C00
DYN_BASE=0x00009000
DYN_SIZE=0x1000
DYN_HEADER_SIZE=32
DYN_PAYLOAD=DYN_BASE+DYN_HEADER_SIZE
DYN_FREE=DYN_SIZE-DYN_HEADER_SIZE
ADDMEM_OFF=0x1400
BASE_AVAIL_OFF=0x1500
FUNCS={198:ROM_BASE+0x0B00,210:ROM_BASE+0x0C00,216:ROM_BASE+0x0D00,618:ROM_BASE+ADDMEM_OFF}


def cmpabsw(c,v,a):
    c+=bytes.fromhex('0C79')+struct.pack('>H',v&0xffff)+struct.pack('>I',a)
    return branch(c,0x6600)


def addmemlist_code():
    """D0=size D1=attrs D2=pri A0=base A1=name; register one dynamic region."""
    q=bytearray(bytes.fromhex('2F032F042F0A'))               # save d3,d4,a2
    q+=bytes.fromhex('2600')                                 # d3=size
    q+=bytes.fromhex('2839')+struct.pack('>I',DYN_SLOT)      # d4=existing slot
    q+=bytes.fromhex('4A84'); occupied=branch(q,0x6600)
    q+=bytes.fromhex('0C8300000028'); too_small=branch(q,0x6500) # size < 40
    # MemHeader Node subset and public fields at base.
    q+=bytes.fromhex('42A8000042A80004')                    # ln_Succ/ln_Pred = NULL
    q+=bytes.fromhex('11420009')                             # ln_Pri = low byte d2
    q+=bytes.fromhex('2149000A')                             # ln_Name = a1
    q+=bytes.fromhex('3141000E')                             # mh_Attributes = d1.w
    q+=bytes.fromhex('45E80020')                             # a2=base+32
    q+=bytes.fromhex('214A0010214A0014')                    # mh_First/mh_Lower=a2
    q+=bytes.fromhex('2808D88321440018')                    # mh_Upper=base+size
    q+=bytes.fromhex('0483000000202143001C')                # size-=32; mh_Free=size
    q+=bytes.fromhex('429225430004')                         # first chunk next=0, bytes=d3
    q+=bytes.fromhex('23C8')+struct.pack('>I',DYN_SLOT)      # publish dynamic header
    out=len(q); q+=bytes.fromhex('245F281F261F4E75')
    patch(q,occupied,out); patch(q,too_small,out)
    return bytes(q)


def avail_wrapper_code():
    """Retain M2.12 behavior and include the dynamic region in total-free queries.

    M2.13 intentionally leaves dynamic MEMF_LARGEST scanning for M2.14. Since
    the qualified added region is smaller than an intact 4 KiB static region,
    the existing largest answers remain valid in this runtime probe.
    """
    q=bytearray(bytes.fromhex('2F012F022F032F08'))          # d1,d2,d3,a0
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+BASE_AVAIL_OFF)
    q+=bytes.fromhex('2600')                                # d3=base result
    q+=bytes.fromhex('08010011')                            # MEMF_LARGEST?
    done_base=branch(q,0x6600)
    q+=bytes.fromhex('2039')+struct.pack('>I',DYN_SLOT)      # d0=dynamic header
    q+=bytes.fromhex('4A80'); done_none=branch(q,0x6700)
    q+=bytes.fromhex('2040')                                # a0=header
    q+=bytes.fromhex('3428000E')                            # d2=attributes.w
    # If CHIP requested, dynamic region must carry CHIP.
    q+=bytes.fromhex('08010001'); no_chip_req=branch(q,0x6700)
    q+=bytes.fromhex('08020001'); reject_chip=branch(q,0x6700)
    chip_ok=len(q)
    # If FAST requested, dynamic region must carry FAST.
    q+=bytes.fromhex('08010002'); no_fast_req=branch(q,0x6700)
    q+=bytes.fromhex('08020002'); reject_fast=branch(q,0x6700)
    fast_ok=len(q)
    q+=bytes.fromhex('2003D0A8001C')                        # d0=base + mh_Free
    done=branch(q,0x6000)
    base_only=len(q); q+=bytes.fromhex('2003')              # d0=base result
    out=len(q); q+=bytes.fromhex('205F261F241F221F4E75')
    patch(q,done_base,base_only); patch(q,done_none,base_only)
    patch(q,no_chip_req,chip_ok); patch(q,reject_chip,base_only)
    patch(q,no_fast_req,fast_ok); patch(q,reject_fast,base_only)
    patch(q,done,out)
    return bytes(q)


def build():
    image=bytearray([0xff])*ROM_SIZE
    struct.pack_into('>II',image,0,SP,PC)
    c=bytearray(bytes.fromhex('46FC2700'))
    c+=mb(3,CIAA_DDRA); c+=bclr0(CIAA_PRA); c+=ml(EXEC_BASE,4)
    c+=ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)
    # Extend negative size through AddMemList(-618).
    c+=mw(0,EXEC_BASE+14)+mw(618,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(13,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
    for off,t in FUNCS.items(): c+=vector(t,EXEC_BASE-off)

    # Retain the two statically qualified M2.12 regions.
    c+=mw(MEMF_CHIP,MEMHDR+MH_ATTR)+ml(MEM_BASE,MEMHDR+MH_FIRST)+ml(MEM_BASE,MEMHDR+MH_LOWER)+ml(MEM_BASE+MEM_SIZE,MEMHDR+MH_UPPER)+ml(MEM_SIZE,MEMHDR+MH_FREE)
    c+=ml(0,MEM_BASE)+ml(MEM_SIZE,MEM_BASE+4)
    c+=mw(MEMF_FAST,FAST_HDR+MH_ATTR)+ml(FAST_BASE,FAST_HDR+MH_FIRST)+ml(FAST_BASE,FAST_HDR+MH_LOWER)+ml(FAST_BASE+FAST_SIZE,FAST_HDR+MH_UPPER)+ml(FAST_SIZE,FAST_HDR+MH_FREE)
    c+=ml(0,FAST_BASE)+ml(FAST_SIZE,FAST_BASE+4)
    c+=ml(0,DYN_SLOT)

    c+=mw(0x0f00,COLOR00)+b'\x4d\xf9'+struct.pack('>I',EXEC_BASE)
    fails=[]
    def avail(flags,expect):
        nonlocal c
        c+=bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF28')
        fails.append(cmpd0(c,expect))

    # Baseline totals before dynamic registration.
    avail(MEMF_FAST,FAST_SIZE)
    avail(MEMF_TOTAL,MEM_SIZE+FAST_SIZE)

    # Add one dynamic FAST region. AddMemList ABI: D0,D1,D2,A0,A1.
    c+=bytes.fromhex('203C')+struct.pack('>I',DYN_SIZE)
    c+=bytes.fromhex('223C')+struct.pack('>I',MEMF_FAST)
    c+=bytes.fromhex('243C00000005')
    c+=bytes.fromhex('207C')+struct.pack('>I',DYN_BASE)
    c+=bytes.fromhex('227C')+struct.pack('>I',DYN_NAME_ADDR)
    c+=bytes.fromhex('4EAEFD96')                            # JSR -618(a6)

    # Header/chunk creation and publication.
    fails.append(cmpabs(c,DYN_BASE,DYN_SLOT))
    fails.append(cmpabsw(c,MEMF_FAST,DYN_BASE+MH_ATTR))
    fails.append(cmpabs(c,DYN_NAME_ADDR,DYN_BASE+10))
    fails.append(cmpabs(c,DYN_PAYLOAD,DYN_BASE+MH_FIRST))
    fails.append(cmpabs(c,DYN_PAYLOAD,DYN_BASE+MH_LOWER))
    fails.append(cmpabs(c,DYN_BASE+DYN_SIZE,DYN_BASE+MH_UPPER))
    fails.append(cmpabs(c,DYN_FREE,DYN_BASE+MH_FREE))
    fails.append(cmpabs(c,0,DYN_PAYLOAD))
    fails.append(cmpabs(c,DYN_FREE,DYN_PAYLOAD+4))

    # Dynamic region contributes to total-free FAST/ANY accounting.
    avail(MEMF_FAST,FAST_SIZE+DYN_FREE)
    avail(MEMF_TOTAL,MEM_SIZE+FAST_SIZE+DYN_FREE)
    # Existing largest remains 4 KiB in this slice (dynamic largest traversal deferred).
    avail(MEMF_FAST|MEMF_LARGEST,FAST_SIZE)
    avail(MEMF_LARGEST,FAST_SIZE)

    c+=mw(0x00f0,COLOR00); pass_branch=branch(c,0x6000)
    bad=len(c); c+=mw(0x000f,COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for p in fails: patch(c,p,bad)
    patch(c,pass_branch,idle)
    if 8+len(c)>0x0B00: raise ValueError('bootstrap overlaps M2.13 routines')
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
        ADDMEM_OFF:addmemlist_code(),
        BASE_AVAIL_OFF:base_avail_code(),
    }
    ordered=sorted(routines.items())
    for (off,code),(nxt,_) in zip(ordered,ordered[1:]+[(MARKER_OFF,b'')]):
        if off+len(code)>nxt: raise ValueError(f'routine overlap at {off:x}')
        image[off:off+len(code)]=code

    marker=b'LIBREKICK-M2.13\0EXEC-ADDMEMLIST-DYNAMIC\0'
    ident=b'exec.library\0LibreKick M2.13 AddMemList dynamic-region slice 40.13\0'
    name=b'M2.13 dynamic FAST\0'
    image[MARKER_OFF:MARKER_OFF+len(marker)]=marker
    image[IDENT_OFF:IDENT_OFF+len(ident)]=ident
    image[DYN_NAME_OFF:DYN_NAME_OFF+len(name)]=name
    struct.pack_into('>I',image,ROM_SIZE-4,0)
    total=0
    for o in range(0,ROM_SIZE-4,4): total=ones(total,struct.unpack_from('>I',image,o)[0])
    total=(total&0xffffffff)+(total>>32)
    struct.pack_into('>I',image,ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_13_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.13 ROM built: {out} ({len(data)} bytes)')
