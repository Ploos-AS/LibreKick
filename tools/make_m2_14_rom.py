#!/usr/bin/env python3
"""Build LibreKick M2.14: allocate/free through dynamically registered region."""
from pathlib import Path
import struct, sys
from make_m2_13_rom import (
    ROM_SIZE, ROM_BASE, SP, PC, EXEC_BASE, COLOR00, CIAA_PRA, CIAA_DDRA,
    MEMHDR, MEM_BASE, MEM_SIZE, MH_ATTR, MH_FIRST, MH_LOWER, MH_UPPER, MH_FREE,
    FAST_HDR, FAST_BASE, FAST_SIZE,
    MARKER_OFF, IDENT_OFF, DYN_NAME_OFF, DYN_NAME_ADDR, DYN_SLOT,
    DYN_BASE, DYN_SIZE, DYN_HEADER_SIZE, DYN_PAYLOAD, DYN_FREE,
    ml, mw, mb, bclr0, vector, branch, patch, cmpd0, cmpabs, ones,
    relocate_region, allocmem_core_code, freemem_code, largest_code,
    addmemlist_code, avail_wrapper_code,
    CHIP_ALLOC_OFF, CHIP_FREE_OFF, FAST_ALLOC_OFF, FAST_FREE_OFF,
    CHIP_LARGEST_OFF, FAST_LARGEST_OFF, ADDMEM_OFF, BASE_AVAIL_OFF,
    MEMF_CHIP, MEMF_FAST, MEMF_CLEAR, MEMF_TOTAL, MEMF_LARGEST,
)

MARKER_OFF=0x1A00
IDENT_OFF=0x1A80
DYN_NAME_OFF=0x1AE0
IDSTRING_ADDR=ROM_BASE+IDENT_OFF
DYN_NAME_ADDR=ROM_BASE+DYN_NAME_OFF
DYN_ALLOC_OFF=0x1600
DYN_FREE_OFF=0x1700
FUNCS={198:ROM_BASE+0x0B00,210:ROM_BASE+0x0C00,216:ROM_BASE+0x0D00,618:ROM_BASE+ADDMEM_OFF}


def alloc_wrapper_code():
    """Static CHIP first; FAST falls back to registered dynamic region."""
    q=bytearray(bytes.fromhex('2F022F032F08'))
    q+=bytes.fromhex('24002601')                         # d2=size, d3=reqs
    q+=bytes.fromhex('08030002'); fast=branch(q,0x6600) # FAST?
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+CHIP_ALLOC_OFF)
    common=branch(q,0x6000)
    f=len(q)
    q+=bytes.fromhex('08030001'); reject=branch(q,0x6600) # CHIP+FAST conflict
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+FAST_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); got_static=branch(q,0x6600)
    q+=bytes.fromhex('2039')+struct.pack('>I',DYN_SLOT)
    q+=bytes.fromhex('4A80'); no_dyn=branch(q,0x6700)
    q+=bytes.fromhex('2040')
    q+=bytes.fromhex('3428000E')                         # dyn attrs
    q+=bytes.fromhex('08020002'); no_dyn_fast=branch(q,0x6700)
    q+=bytes.fromhex('2002')                             # restore size d0=d2
    q+=bytes.fromhex('2203')                             # reqs d1=d3
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+DYN_ALLOC_OFF)
    after=len(q)
    q+=bytes.fromhex('4A80'); done_null=branch(q,0x6700)
    clear_common=len(q)
    q+=bytes.fromhex('08030010'); done_plain=branch(q,0x6700)
    q+=bytes.fromhex('2040')
    q+=bytes.fromhex('0682000000070282FFFFFFF8')
    loop=len(q); q+=bytes.fromhex('42985982'); more=branch(q,0x6600)
    done=len(q); q+=bytes.fromhex('205F261F241F4E75')
    bad=len(q); q+=bytes.fromhex('7000'); bad_done=branch(q,0x6000)
    patch(q,fast,f); patch(q,common,after); patch(q,reject,bad)
    patch(q,got_static,clear_common); patch(q,no_dyn,bad); patch(q,no_dyn_fast,bad)
    patch(q,done_null,done); patch(q,done_plain,done); patch(q,more,loop); patch(q,bad_done,done)
    return bytes(q)


def free_wrapper_code():
    """Route frees to CHIP, static FAST, or registered dynamic region by address."""
    q=bytearray(bytes.fromhex('2F012F02'))
    q+=bytes.fromhex('22092409')                         # d1=addr,d2=addr
    q+=bytes.fromhex('0C81')+struct.pack('>I',DYN_PAYLOAD)
    dyn=branch(q,0x6400)                                 # >= dyn payload
    q+=bytes.fromhex('0C81')+struct.pack('>I',FAST_BASE)
    fast=branch(q,0x6400)
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+CHIP_FREE_OFF)
    done0=branch(q,0x6000)
    fs=len(q); q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+FAST_FREE_OFF)
    done1=branch(q,0x6000)
    dy=len(q)
    q+=bytes.fromhex('2039')+struct.pack('>I',DYN_SLOT)
    q+=bytes.fromhex('4A80'); done_no=branch(q,0x6700)
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+DYN_FREE_OFF)
    done=len(q); q+=bytes.fromhex('241F221F4E75')
    patch(q,dyn,dy); patch(q,fast,fs); patch(q,done0,done); patch(q,done1,done); patch(q,done_no,done)
    return bytes(q)


def build():
    image=bytearray([0xff])*ROM_SIZE; struct.pack_into('>II',image,0,SP,PC)
    c=bytearray(bytes.fromhex('46FC2700')); c+=mb(3,CIAA_DDRA); c+=bclr0(CIAA_PRA); c+=ml(EXEC_BASE,4)
    c+=ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)
    c+=mw(0,EXEC_BASE+14)+mw(618,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(14,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
    for off,t in FUNCS.items(): c+=vector(t,EXEC_BASE-off)
    c+=mw(MEMF_CHIP,MEMHDR+MH_ATTR)+ml(MEM_BASE,MEMHDR+MH_FIRST)+ml(MEM_BASE,MEMHDR+MH_LOWER)+ml(MEM_BASE+MEM_SIZE,MEMHDR+MH_UPPER)+ml(MEM_SIZE,MEMHDR+MH_FREE)+ml(0,MEM_BASE)+ml(MEM_SIZE,MEM_BASE+4)
    c+=mw(MEMF_FAST,FAST_HDR+MH_ATTR)+ml(FAST_BASE,FAST_HDR+MH_FIRST)+ml(FAST_BASE,FAST_HDR+MH_LOWER)+ml(FAST_BASE+FAST_SIZE,FAST_HDR+MH_UPPER)+ml(FAST_SIZE,FAST_HDR+MH_FREE)+ml(0,FAST_BASE)+ml(FAST_SIZE,FAST_BASE+4)
    c+=ml(0,DYN_SLOT)
    c+=mw(0x0f00,COLOR00)+b'\x4d\xf9'+struct.pack('>I',EXEC_BASE)
    fails=[]
    def avail(flags,expect):
        nonlocal c
        c+=bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF28'); fails.append(cmpd0(c,expect))
    def alloc(size,flags,expect):
        nonlocal c
        c+=bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF3A'); fails.append(cmpd0(c,expect))
    def free(addr,size):
        nonlocal c
        c+=bytes.fromhex('227C')+struct.pack('>I',addr)+bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('4EAEFF2E')

    # Register dynamic FAST region.
    c+=bytes.fromhex('203C')+struct.pack('>I',DYN_SIZE)+bytes.fromhex('223C')+struct.pack('>I',MEMF_FAST)+bytes.fromhex('243C00000005')
    c+=bytes.fromhex('207C')+struct.pack('>I',DYN_BASE)+bytes.fromhex('227C')+struct.pack('>I',DYN_NAME_ADDR)+bytes.fromhex('4EAEFD96')
    fails.append(cmpabs(c,DYN_BASE,DYN_SLOT))
    avail(MEMF_FAST,FAST_SIZE+DYN_FREE)

    # Exhaust static FAST, then require fallback allocation from dynamic region.
    alloc(FAST_SIZE,MEMF_FAST,FAST_BASE)
    alloc(0x100,MEMF_FAST|MEMF_CLEAR,DYN_PAYLOAD)
    for off in range(0,0x100,4): fails.append(cmpabs(c,0,DYN_PAYLOAD+off))
    avail(MEMF_FAST,DYN_FREE-0x100)
    fails.append(cmpabs(c,DYN_PAYLOAD+0x100,DYN_BASE+MH_FIRST))
    fails.append(cmpabs(c,DYN_FREE-0x100,DYN_BASE+MH_FREE))

    # Free routes must restore dynamic then static FAST regions independently.
    free(DYN_PAYLOAD,0x100)
    fails.append(cmpabs(c,DYN_PAYLOAD,DYN_BASE+MH_FIRST)); fails.append(cmpabs(c,DYN_FREE,DYN_BASE+MH_FREE))
    free(FAST_BASE,FAST_SIZE)
    avail(MEMF_FAST,FAST_SIZE+DYN_FREE)
    fails.append(cmpabs(c,FAST_BASE,FAST_HDR+MH_FIRST)); fails.append(cmpabs(c,FAST_SIZE,FAST_HDR+MH_FREE))

    c+=mw(0x00f0,COLOR00); good=branch(c,0x6000)
    bad=len(c); c+=mw(0x000f,COLOR00); idle=len(c); c+=bytes.fromhex('60FE')
    for p in fails: patch(c,p,bad)
    patch(c,good,idle)
    if 8+len(c)>0x0B00: raise ValueError('bootstrap overlaps M2.14 routines')
    image[8:8+len(c)]=c

    dyn_alloc=relocate_region(allocmem_core_code(),MEMHDR,DYN_BASE)
    dyn_free=relocate_region(freemem_code(),MEMHDR,DYN_BASE)
    fast_alloc=relocate_region(allocmem_core_code(),MEMHDR,FAST_HDR)
    fast_free=relocate_region(freemem_code(),MEMHDR,FAST_HDR)
    routines={0x0B00:alloc_wrapper_code(),0x0C00:free_wrapper_code(),0x0D00:avail_wrapper_code(),
              CHIP_ALLOC_OFF:allocmem_core_code(),CHIP_FREE_OFF:freemem_code(),FAST_ALLOC_OFF:fast_alloc,FAST_FREE_OFF:fast_free,
              CHIP_LARGEST_OFF:largest_code(MEMHDR),FAST_LARGEST_OFF:largest_code(FAST_HDR),ADDMEM_OFF:addmemlist_code(),BASE_AVAIL_OFF:base_avail_code(),
              DYN_ALLOC_OFF:dyn_alloc,DYN_FREE_OFF:dyn_free}
    ordered=sorted(routines.items())
    for (off,code),(nxt,_) in zip(ordered,ordered[1:]+[(MARKER_OFF,b'')]):
        if off+len(code)>nxt: raise ValueError(f'routine overlap at {off:x}')
        image[off:off+len(code)]=code
    marker=b'LIBREKICK-M2.14\0EXEC-DYNAMIC-ALLOC-FREE\0'; ident=b'exec.library\0LibreKick M2.14 dynamic AllocMem FreeMem slice 40.14\0'; name=b'M2.14 dynamic FAST\0'
    image[MARKER_OFF:MARKER_OFF+len(marker)]=marker; image[IDENT_OFF:IDENT_OFF+len(ident)]=ident; image[DYN_NAME_OFF:DYN_NAME_OFF+len(name)]=name
    struct.pack_into('>I',image,ROM_SIZE-4,0); total=0
    for o in range(0,ROM_SIZE-4,4): total=ones(total,struct.unpack_from('>I',image,o)[0])
    total=(total&0xffffffff)+(total>>32); struct.pack_into('>I',image,ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_14_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data); print(f'M2.14 ROM built: {out} ({len(data)} bytes)')
