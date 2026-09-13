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
    q=bytearray(bytes.fromhex('2F022F032F042F052F082F09'))
    q+=bytes.fromhex('24002601')
    q+=bytes.fromhex('08030002'); has_fast=m.branch(q,0x6600)
    q+=bytes.fromhex('08030001'); has_chip=m.branch(q,0x6600)
    q+=bytes.fromhex('2002')
    q+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+m.FAST_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); got_nf_fast=m.branch(q,0x6600)
    q+=bytes.fromhex('2002')
    q+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+m.CHIP_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); got_nf_chip=m.branch(q,0x6600)
    q+=bytes.fromhex('7A00'); to_dyn_any=m.branch(q,0x6000)
    chip=len(q)
    q+=bytes.fromhex('2002')
    q+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+m.CHIP_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); got_chip=m.branch(q,0x6600)
    q+=bytes.fromhex('7A02'); to_dyn_chip=m.branch(q,0x6000)
    fast=len(q)
    q+=bytes.fromhex('08030001'); reject=m.branch(q,0x6600)
    q+=bytes.fromhex('2002')
    q+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+m.FAST_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); got_fast=m.branch(q,0x6600)
    q+=bytes.fromhex('7A04')
    dyn=len(q)
    q+=bytes.fromhex('2079')+struct.pack('>I',m.DYN_HEAD)
    loop=len(q)
    q+=bytes.fromhex('20084A80'); no_dyn=m.branch(q,0x6700)
    q+=bytes.fromhex('4A85'); mode_any=m.branch(q,0x6700)
    # D1 originally carries the full requirements mask (e.g. MEMF_CLEAR in the
    # upper word). MOVE.W D5,D1 only replaced the low word, leaving stale upper
    # bits and making CMP.L reject an otherwise matching dynamic FAST/CHIP
    # MemHeader. Copy the complete normalized mode instead.
    q+=bytes.fromhex('220578003828000E')
    q+=bytes.fromhex('B284'); attr_ok=m.branch(q,0x6700)
    adv=len(q); q+=bytes.fromhex('2050'); again=m.branch(q,0x6000)
    try_dyn=len(q)
    q+=bytes.fromhex('2248')
    q+=bytes.fromhex('20022203')
    q+=bytes.fromhex('4EB9')+struct.pack('>I',m.ROM_BASE+m.DYN_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); dyn_ok=m.branch(q,0x6600)
    q+=bytes.fromhex('2049')
    back_adv=m.branch(q,0x6000)
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


def build():
    image=bytearray(p.build())

    # M2.17, M2.18 and M2.19 each retain a stable blue failure loop. Recolor
    # those three inherited gates before changing AllocMem so CI tells us which
    # already-qualified slice regressed. This is diagnostic only and leaves all
    # branch targets/control flow untouched.
    inherited_fail=bytes.fromhex('33FC000F00DFF18060FE')
    positions=[]; start=8
    while True:
        pos=image.find(inherited_fail,start,0x0B00)
        if pos<0: break
        positions.append(pos); start=pos+len(inherited_fail)
    if len(positions)!=3:
        raise ValueError(f'M2.20 expected 3 inherited fail gates, found {len(positions)}')
    for pos,color in zip(positions,(0x0a00,0x0aa0,0x0a0a)):
        struct.pack_into('>H',image,pos+2,color)

    code=alloc_wrapper_code_m220()
    if len(code)>0x100: raise ValueError('M2.20 AllocMem wrapper exceeds fixed slot')
    image[0x0B00:0x0C00]=b'\xff'*0x100
    image[0x0B00:0x0B00+len(code)]=code

    boot=image[8:0x0B00]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=boot.rfind(sig)
    if gp<0: raise ValueError('M2.19 final success gate not found')
    good_abs=8+gp; branch_pos=good_abs+8
    # M2.19 is the third inherited gate and has been recolored to 0x0a0a.
    fail_sig=bytes.fromhex('33FC0A0A00DFF18060FE')
    fp=boot.find(fail_sig,gp)
    if fp<0: raise ValueError('M2.19 final fail gate not found')
    test_abs=8+fp+len(fail_sig)

    c=bytearray(); fails=[]
    def alloc(size,flags,expect):
        c.extend(bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF3A'))
        fails.append(m.cmpd0(c,expect))
    def free(addr,size):
        c.extend(bytes.fromhex('227C')+struct.pack('>I',addr)+bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('4EAEFF2E'))

    alloc(0x100,0,m.FAST_BASE)
    alloc(m.FAST_SIZE-0x100,m.MEMF_FAST,m.FAST_BASE+0x100)
    alloc(0x100,0,m.MEM_BASE)
    alloc(m.MEM_SIZE-0x100,m.MEMF_CHIP,m.MEM_BASE+0x100)
    alloc(0x100,0,m.APAY)
    alloc(0x100,m.MEMF_CHIP|m.MEMF_FAST,0)

    free(m.APAY,0x100)
    free(m.FAST_BASE+0x100,m.FAST_SIZE-0x100); free(m.FAST_BASE,0x100)
    free(m.MEM_BASE+0x100,m.MEM_SIZE-0x100); free(m.MEM_BASE,0x100)

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    fail_colors=(0x0f00,0x0ff0,0x0f0f,0x00ff,0x0888,0x0f80)
    fail_offsets=[]
    for color in fail_colors:
        fail_offsets.append(len(c))
        c+=m.mw(color,m.COLOR00)+bytes.fromhex('60FE')
    idle=len(c); c+=bytes.fromhex('60FE')
    if len(fails)!=len(fail_offsets): raise ValueError('M2.20 diagnostic assertion count mismatch')
    for branch_pos_local,target in zip(fails,fail_offsets): m.patch(c,branch_pos_local,target)
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