#!/usr/bin/env python3
"""Build LibreKick M2.20: AllocMem no-region FAST preference with CHIP fallback."""
from pathlib import Path
import struct, sys
import make_m2_19_rom as p
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.20\0EXEC-ALLOCMEM-NOFLAG-SEMANTICS\0'
IDENT=b'exec.library\0LibreKick M2.20 AllocMem no-region semantics slice 40.20\0'


def alloc_wrapper_code_m220():
    """Explicit CHIP/FAST stay strict; no region bits prefer FAST, then CHIP, then any dynamic region."""
    # D5 is a dedicated dynamic-region mode register. Keep it separate from D4,
    # which is scratch for each MemHeader's mh_Attributes. This matters when an
    # explicit CHIP traversal skips a FAST header: reusing D4 for both mode and
    # attributes would turn the next comparison into FAST and could allocate
    # from the wrong region.
    q=bytearray(bytes.fromhex('2F022F032F042F052F082F09'))  # d2,d3,d4,d5,a0,a1
    q+=bytes.fromhex('24002601')                             # d2=size d3=requirements

    # CHIP|FAST is unsatisfiable.
    q+=bytes.fromhex('08030002'); has_fast=m.branch(q,0x6600)
    q+=bytes.fromhex('08030001'); has_chip=m.branch(q,0x6600)

    # No explicit region: FAST first, then CHIP, then any dynamic header.
    q+=bytes.fromhex('2002')
    q+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+m.FAST_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); got_nf_fast=m.branch(q,0x6600)
    q+=bytes.fromhex('2002')
    q+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+m.CHIP_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); got_nf_chip=m.branch(q,0x6600)
    q+=bytes.fromhex('7A00'); to_dyn_any=m.branch(q,0x6000) # d5 mode: 0 any

    # Explicit CHIP.
    chip=len(q)
    q+=bytes.fromhex('2002')
    q+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+m.CHIP_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); got_chip=m.branch(q,0x6600)
    q+=bytes.fromhex('7A02'); to_dyn_chip=m.branch(q,0x6000) # d5 mode: MEMF_CHIP

    # Explicit FAST; reject CHIP|FAST.
    fast=len(q)
    q+=bytes.fromhex('08030001'); reject=m.branch(q,0x6600)
    q+=bytes.fromhex('2002')
    q+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+m.FAST_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); got_fast=m.branch(q,0x6600)
    q+=bytes.fromhex('7A04')                                 # d5 mode: MEMF_FAST

    # Linked dynamic traversal. D5 remains invariant; D4 is per-header attrs.
    dyn=len(q)
    q+=bytes.fromhex('2079')+struct.pack('>I',m.DYN_HEAD)
    loop=len(q)
    q+=bytes.fromhex('20084A80'); no_dyn=m.branch(q,0x6700)
    q+=bytes.fromhex('4A85'); mode_any=m.branch(q,0x6700)
    q+=bytes.fromhex('32053828000E')                         # d1=mode; d4=attrs.w
    q+=bytes.fromhex('B284'); attr_ok=m.branch(q,0x6700)     # attrs == mode in current single-class model
    adv=len(q); q+=bytes.fromhex('2050'); again=m.branch(q,0x6000)
    try_dyn=len(q)
    q+=bytes.fromhex('2248')                                 # preserve current header in a1
    q+=bytes.fromhex('20022203')                             # restore size/requirements
    q+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+m.DYN_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); dyn_ok=m.branch(q,0x6600)
    q+=bytes.fromhex('2049')                                 # restore current header from a1 after call
    back_adv=m.branch(q,0x6000)

    # Shared success path handles MEMF_CLEAR using original request size.
    success=len(q)
    q+=bytes.fromhex('08030010'); done_plain=m.branch(q,0x6700)
    q+=bytes.fromhex('2040')
    q+=bytes.fromhex('0682000000070282FFFFFFF8')
    clear_loop=len(q); q+=bytes.fromhex('42985982'); more=m.branch(q,0x6600)
    done=len(q); q+=bytes.fromhex('225F205F2A1F281F261F241F4E75')
    bad=len(q); q+=bytes.fromhex('7000'); bad_done=m.branch(q,0x6000)

    m.patch(q,has_fast,fast); m.patch(q,has_chip,chip)
    m.patch(q,got_nf_fast,success); m.patch(q,got_nf_chip,success)
    m.patch(q,to_dyn_any,dyn); m.patch(q,got_chip,success); m.patch(q,to_dyn_chip,dyn)
    m.patch(q,reject,bad); m.patch(q,got_fast,success)
    m.patch(q,no_dyn,bad); m.patch(q,mode_any,try_dyn); m.patch(q,attr_ok,try_dyn)
    m.patch(q,again,loop); m.patch(q,dyn_ok,success); m.patch(q,back_adv,adv)
    m.patch(q,done_plain,done); m.patch(q,more,clear_loop); m.patch(q,bad_done,done)
    return bytes(q)


def replace_once(image, old, new, what, start=8, end=0x0B00):
    pos=image.find(old,start,end)
    if pos<0: raise ValueError(f'M2.20 could not locate {what}')
    if image.find(old,pos+1,end)>=0: raise ValueError(f'M2.20 ambiguous {what}')
    image[pos:pos+len(old)]=new


def build():
    image=bytearray(p.build())

    # M2.11 embedded a regression probe for the old deterministic no-region
    # CHIP preference. M2.20 intentionally changes that contract to FAST-first,
    # so adapt the inherited probe itself before installing the new wrapper.
    # At this point the M2.11 probe has 0x80 bytes allocated at FAST_BASE and
    # therefore the next 0x20 no-region allocation must be FAST_BASE+0x80.
    old_alloc_probe=(bytes.fromhex('203C00000020223C000000004EAEFF3A0C80')+
                     struct.pack('>I',m.MEM_BASE+0x40))
    new_alloc_probe=(bytes.fromhex('203C00000020223C000000004EAEFF3A0C80')+
                     struct.pack('>I',m.FAST_BASE+0x80))
    replace_once(image,old_alloc_probe,new_alloc_probe,'inherited M2.11 no-region expectation')

    old_free=(bytes.fromhex('227C')+struct.pack('>I',m.MEM_BASE+0x40)+
              bytes.fromhex('203C000000204EAEFF2E'))
    new_free=(bytes.fromhex('227C')+struct.pack('>I',m.FAST_BASE+0x80)+
              bytes.fromhex('203C000000204EAEFF2E'))
    replace_once(image,old_free,new_free,'inherited M2.11 no-region free')

    code=alloc_wrapper_code_m220()
    if len(code)>0x100: raise ValueError('M2.20 AllocMem wrapper exceeds fixed slot')
    image[0x0B00:0x0C00]=b'\xff'*0x100
    image[0x0B00:0x0B00+len(code)]=code

    # Chain a no-region runtime gate after M2.19's final green path.
    boot=image[8:0x0B00]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=boot.rfind(sig)
    if gp<0: raise ValueError('M2.19 final success gate not found')
    good_abs=8+gp; branch_pos=good_abs+8
    fail_sig=bytes.fromhex('33FC000F00DFF18060FE')
    fp=boot.find(fail_sig,gp)
    if fp<0: raise ValueError('M2.19 final fail gate not found')
    test_abs=8+fp+len(fail_sig)

    c=bytearray(); fails=[]
    def alloc(size,flags,expect):
        c.extend(bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF3A'))
        fails.append(m.cmpd0(c,expect))
    def free(addr,size):
        c.extend(bytes.fromhex('227C')+struct.pack('>I',addr)+bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('4EAEFF2E'))

    # No region flags must prefer static FAST when it is available.
    alloc(0x100,0,m.FAST_BASE); free(m.FAST_BASE,0x100)
    # With FAST exhausted, no-region falls back to CHIP.
    alloc(m.FAST_SIZE,m.MEMF_FAST,m.FAST_BASE)
    alloc(0x100,0,m.MEM_BASE); free(m.MEM_BASE,0x100)
    # With both static regions exhausted, no-region accepts dynamic memory in priority order.
    alloc(m.MEM_SIZE,m.MEMF_CHIP,m.MEM_BASE)
    alloc(0x100,0,m.APAY); free(m.APAY,0x100)
    # CHIP|FAST remains invalid.
    alloc(0x100,m.MEMF_CHIP|m.MEMF_FAST,0)
    free(m.FAST_BASE,m.FAST_SIZE); free(m.MEM_BASE,m.MEM_SIZE)

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00); idle=len(c); c+=bytes.fromhex('60FE')
    for x in fails: m.patch(c,x,bad)
    m.patch(c,ok,idle)
    if test_abs+len(c)>=0x0B00: raise ValueError('M2.20 runtime probe exceeds bootstrap area')
    image[test_abs:test_abs+len(c)]=c
    struct.pack_into('>h',image,branch_pos+2,test_abs-(branch_pos+2))

    image[m.MARKER_OFF:m.IDENT_OFF]=b'\xff'*(m.IDENT_OFF-m.MARKER_OFF)
    image[m.MARKER_OFF:m.MARKER_OFF+len(MARKER)]=MARKER
    image[m.IDENT_OFF:m.NAME_A_OFF]=b'\xff'*(m.NAME_A_OFF-m.IDENT_OFF)
    image[m.IDENT_OFF:m.IDENT_OFF+len(IDENT)]=IDENT

    struct.pack_into('>I',image,m.ROM_SIZE-4,0); total=0
    for off in range(0,m.ROM_SIZE-4,4): total=m.ones(total,struct.unpack_from('>I',image,off)[0])
    total=(total&0xffffffff)+(total>>32)
    struct.pack_into('>I',image,m.ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_20_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.20 ROM built: {out} ({len(data)} bytes)')
