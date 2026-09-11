#!/usr/bin/env python3
"""Build LibreKick M2.11: two logical MemHeader regions (CHIP + FAST)."""
from pathlib import Path
import struct, sys
from make_m2_10_rom import (
    ROM_SIZE, ROM_BASE, SP, PC, EXEC_BASE, COLOR00, CIAA_PRA, CIAA_DDRA,
    MEMHDR, MEM_BASE, MEM_SIZE, MH_ATTR, MH_FIRST, MH_LOWER, MH_UPPER, MH_FREE,
    MARKER_OFF, IDENT_OFF, ml, mw, mb, bclr0, vector, branch, patch, cmpd0,
    cmpabs, ones, allocmem_core_code, freemem_code,
    MEMF_CHIP, MEMF_TOTAL, MEMF_FAST, MEMF_CLEAR,
)

FAST_HDR=0x00004A00
FAST_BASE=0x00007000
FAST_SIZE=0x1000
IDSTRING_ADDR=ROM_BASE+IDENT_OFF
CHIP_ALLOC_OFF=0x0E00
CHIP_FREE_OFF=0x0F00
FAST_ALLOC_OFF=0x1000
FAST_FREE_OFF=0x1100
FUNCS={198:ROM_BASE+0x0B00,210:ROM_BASE+0x0C00,216:ROM_BASE+0x0D00}


def relocate_region(code, old_hdr, new_hdr):
    """Relocate absolute mh_First/mh_Free references in an already-qualified core."""
    out=bytearray(code)
    for field in (MH_FIRST, MH_FREE):
        old=struct.pack('>I',old_hdr+field)
        new=struct.pack('>I',new_hdr+field)
        if old not in out:
            raise ValueError(f'missing relocatable MemHeader field {field}')
        out=out.replace(old,new)
    return bytes(out)


def alloc_wrapper_code():
    # D0=size, D1=requirements. Exactly CHIP+FAST is unsatisfiable because no
    # single region has both attributes. With neither set, prefer CHIP.
    q=bytearray(bytes.fromhex('2F022F032F08'))
    q+=bytes.fromhex('24002601')                         # d2=size, d3=requirements
    q+=bytes.fromhex('08030002')                         # FAST?
    fast=branch(q,0x6600)
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+CHIP_ALLOC_OFF)
    after_alloc=branch(q,0x6000)
    f=len(q)
    q+=bytes.fromhex('08030001')                         # CHIP too?
    reject=branch(q,0x6600)
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+FAST_ALLOC_OFF)
    common=len(q)
    q+=bytes.fromhex('4A80'); done_null=branch(q,0x6700)
    q+=bytes.fromhex('08030010')                         # MEMF_CLEAR?
    done_plain=branch(q,0x6700)
    q+=bytes.fromhex('2040')                             # a0=result
    q+=bytes.fromhex('0682000000070282FFFFFFF8')         # align saved size
    loop=len(q)
    q+=bytes.fromhex('4298')                             # clr.l (a0)+
    q+=bytes.fromhex('5982')                             # subq.l #4,d2
    more=branch(q,0x6600)
    done=len(q)
    q+=bytes.fromhex('205F261F241F4E75')
    bad=len(q); q+=bytes.fromhex('7000'); bad_done=branch(q,0x6000)
    patch(q,fast,f); patch(q,after_alloc,common); patch(q,reject,bad)
    patch(q,done_null,done); patch(q,done_plain,done); patch(q,more,loop); patch(q,bad_done,done)
    return bytes(q)


def free_wrapper_code():
    # Route by address: the two qualified regions are disjoint and ordered.
    q=bytearray(bytes.fromhex('2F01'))                    # save d1
    q+=bytes.fromhex('2209')                              # d1=a1
    q+=bytes.fromhex('0C81')+struct.pack('>I',FAST_BASE)
    fast=branch(q,0x6400)                                 # BCC: addr >= FAST_BASE
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+CHIP_FREE_OFF)
    done_branch=branch(q,0x6000)
    f=len(q); q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+FAST_FREE_OFF)
    done=len(q); q+=bytes.fromhex('221F4E75')
    patch(q,fast,f); patch(q,done_branch,done)
    return bytes(q)


def avail_wrapper_code():
    # D1 flags. CHIP selects CHIP, FAST selects FAST, both is unsatisfiable.
    # With neither region bit set (including MEMF_TOTAL), return sum of both.
    q=bytearray(bytes.fromhex('2F02'))                    # save d2
    q+=bytes.fromhex('08010002')                          # FAST?
    fast=branch(q,0x6600)
    q+=bytes.fromhex('08010001')                          # CHIP?
    chip=branch(q,0x6600)
    q+=bytes.fromhex('2039')+struct.pack('>I',MEMHDR+MH_FREE)
    q+=bytes.fromhex('2439')+struct.pack('>I',FAST_HDR+MH_FREE)
    q+=bytes.fromhex('D082')                              # add.l d2,d0
    done0=branch(q,0x6000)
    f=len(q)
    q+=bytes.fromhex('08010001')                          # CHIP also?
    both=branch(q,0x6600)
    q+=bytes.fromhex('2039')+struct.pack('>I',FAST_HDR+MH_FREE)
    done1=branch(q,0x6000)
    ch=len(q); q+=bytes.fromhex('2039')+struct.pack('>I',MEMHDR+MH_FREE)
    done2=branch(q,0x6000)
    bad=len(q); q+=bytes.fromhex('7000')
    done=len(q); q+=bytes.fromhex('241F4E75')
    patch(q,fast,f); patch(q,chip,ch); patch(q,both,bad)
    patch(q,done0,done); patch(q,done1,done); patch(q,done2,done)
    return bytes(q)


def build():
    image=bytearray([0xff])*ROM_SIZE
    struct.pack_into('>II',image,0,SP,PC)
    c=bytearray(bytes.fromhex('46FC2700'))
    c+=mb(3,CIAA_DDRA); c+=bclr0(CIAA_PRA); c+=ml(EXEC_BASE,4)
    c+=ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)
    c+=mw(0,EXEC_BASE+14)+mw(216,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(11,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
    for off,t in FUNCS.items(): c+=vector(t,EXEC_BASE-off)

    # Two logical Exec regions. On the A500 qualification machine both live in
    # ordinary addressable RAM; the second region tests FAST attribute routing.
    c+=mw(MEMF_CHIP,MEMHDR+MH_ATTR)+ml(MEM_BASE,MEMHDR+MH_FIRST)+ml(MEM_BASE,MEMHDR+MH_LOWER)+ml(MEM_BASE+MEM_SIZE,MEMHDR+MH_UPPER)+ml(MEM_SIZE,MEMHDR+MH_FREE)
    c+=ml(0,MEM_BASE)+ml(MEM_SIZE,MEM_BASE+4)
    c+=mw(MEMF_FAST,FAST_HDR+MH_ATTR)+ml(FAST_BASE,FAST_HDR+MH_FIRST)+ml(FAST_BASE,FAST_HDR+MH_LOWER)+ml(FAST_BASE+FAST_SIZE,FAST_HDR+MH_UPPER)+ml(FAST_SIZE,FAST_HDR+MH_FREE)
    c+=ml(0,FAST_BASE)+ml(FAST_SIZE,FAST_BASE+4)
    # Seed FAST allocation payload so FAST|CLEAR is an actual zeroing test.
    for off,val in ((8,0x11223344),(12,0xA5A5A5A5),(16,0xDEADBEEF),(20,0xCAFEBABE)):
        c+=ml(val,FAST_BASE+off)

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

    avail(MEMF_CHIP,MEM_SIZE)
    avail(MEMF_FAST,FAST_SIZE)
    avail(MEMF_TOTAL,MEM_SIZE+FAST_SIZE)
    alloc(0x40,MEMF_CHIP,MEM_BASE)
    alloc(0x80,MEMF_FAST|MEMF_CLEAR,FAST_BASE)
    for off in range(0,0x80,4): fails.append(cmpabs(c,0,FAST_BASE+off))
    avail(MEMF_CHIP,MEM_SIZE-0x40)
    avail(MEMF_FAST,FAST_SIZE-0x80)
    avail(MEMF_TOTAL,(MEM_SIZE-0x40)+(FAST_SIZE-0x80))
    # No region satisfies CHIP|FAST simultaneously; state must remain unchanged.
    alloc(0x20,MEMF_CHIP|MEMF_FAST,0)
    avail(MEMF_TOTAL,(MEM_SIZE-0x40)+(FAST_SIZE-0x80))
    # No region bit: deterministic CHIP preference.
    alloc(0x20,0,MEM_BASE+0x40)
    free(MEM_BASE+0x40,0x20)
    free(FAST_BASE,0x80)
    free(MEM_BASE,0x40)
    avail(MEMF_CHIP,MEM_SIZE); avail(MEMF_FAST,FAST_SIZE); avail(MEMF_TOTAL,MEM_SIZE+FAST_SIZE)
    fails.append(cmpabs(c,MEM_BASE,MEMHDR+MH_FIRST)); fails.append(cmpabs(c,MEM_SIZE,MEM_BASE+4))
    fails.append(cmpabs(c,FAST_BASE,FAST_HDR+MH_FIRST)); fails.append(cmpabs(c,FAST_SIZE,FAST_BASE+4))

    c+=mw(0x00f0,COLOR00); done=branch(c,0x6000)
    bad=len(c); c+=mw(0x000f,COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for p in fails: patch(c,p,bad)
    patch(c,done,idle)
    if 8+len(c)>0x0B00: raise ValueError('bootstrap overlaps M2.11 routines')
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
    }
    ordered=sorted(routines.items())
    for (off,code),(nxt,_) in zip(ordered,ordered[1:]+[(MARKER_OFF,b'')]):
        if off+len(code)>nxt: raise ValueError(f'routine overlap at {off:x}')
        image[off:off+len(code)]=code

    marker=b'LIBREKICK-M2.11\0EXEC-MULTI-MEMHEADER-CHIP-FAST\0'
    ident=b'exec.library\0LibreKick M2.11 CHIP/FAST multi-MemHeader slice 40.11\0'
    image[MARKER_OFF:MARKER_OFF+len(marker)]=marker
    image[IDENT_OFF:IDENT_OFF+len(ident)]=ident
    struct.pack_into('>I',image,ROM_SIZE-4,0)
    total=0
    for o in range(0,ROM_SIZE-4,4): total=ones(total,struct.unpack_from('>I',image,o)[0])
    total=(total&0xffffffff)+(total>>32)
    struct.pack_into('>I',image,ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_11_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.11 ROM built: {out} ({len(data)} bytes)')
