#!/usr/bin/env python3
"""Build LibreKick M2.18: AvailMem(MEMF_LARGEST) across dynamic MemHeaders."""
from pathlib import Path
import struct,sys
import make_m2_17_rom as m

ROM_BASE=m.ROM_BASE; DYN_HEAD=m.DYN_HEAD; MH_ATTR=m.MH_ATTR; MH_FIRST=m.MH_FIRST
MEMF_CHIP=m.MEMF_CHIP; MEMF_FAST=m.MEMF_FAST; MEMF_LARGEST=m.MEMF_LARGEST
BASE_AVAIL_OFF=m.BASE_AVAIL_OFF
MARKER_OFF=m.MARKER_OFF; IDENT_OFF=m.IDENT_OFF
MARKER=b'LIBREKICK-M2.18\0EXEC-DYNAMIC-MEMF-LARGEST\0'
IDENT=b'exec.library\0LibreKick M2.18 dynamic MEMF_LARGEST slice 40.18\0'


def avail_wrapper_code_m218():
    # Preserve public requirements in D4. D3 carries the best result.
    q=bytearray(bytes.fromhex('2F012F022F032F042F082F09')) # d1-d4,a0,a1
    q+=bytes.fromhex('2801')                                # d4=requirements
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+BASE_AVAIL_OFF)
    q+=bytes.fromhex('2600')                                # d3=base result
    q+=bytes.fromhex('08040011'); largest=m.branch(q,0x6600)
    # M2.17 total-free path: walk dynamic headers and add matching mh_Free.
    q+=bytes.fromhex('2079')+struct.pack('>I',DYN_HEAD)
    tloop=len(q); q+=bytes.fromhex('22084A81'); tdone=m.branch(q,0x6700)
    q+=bytes.fromhex('3428000E08040001'); tnc=m.branch(q,0x6700); q+=bytes.fromhex('08020001'); tskipc=m.branch(q,0x6700); tcok=len(q)
    q+=bytes.fromhex('08040002'); tnf=m.branch(q,0x6700); q+=bytes.fromhex('08020002'); tskipf=m.branch(q,0x6700); tfok=len(q)
    q+=bytes.fromhex('D6A8001C'); tadv=len(q); q+=bytes.fromhex('2050'); tagain=m.branch(q,0x6000)
    # Largest path: each matching header, then each MemChunk in mh_First chain.
    lp=len(q); q+=bytes.fromhex('2079')+struct.pack('>I',DYN_HEAD)
    hloop=len(q); q+=bytes.fromhex('22084A81'); hdone=m.branch(q,0x6700)
    q+=bytes.fromhex('3428000E08040001'); hnc=m.branch(q,0x6700); q+=bytes.fromhex('08020001'); hskipc=m.branch(q,0x6700); hcok=len(q)
    q+=bytes.fromhex('08040002'); hnf=m.branch(q,0x6700); q+=bytes.fromhex('08020002'); hskipf=m.branch(q,0x6700); hfok=len(q)
    q+=bytes.fromhex('22680010')                            # a1=mh_First
    cloop=len(q); q+=bytes.fromhex('22094A81'); cdone=m.branch(q,0x6700)
    q+=bytes.fromhex('24290004B682'); keep=m.branch(q,0x6400) # d3>=d2
    q+=bytes.fromhex('2602')
    cnxt=len(q); q+=bytes.fromhex('2251'); cagain=m.branch(q,0x6000)
    hadv=len(q); q+=bytes.fromhex('2050'); hagain=m.branch(q,0x6000)
    done=len(q); q+=bytes.fromhex('2003')
    out=len(q); q+=bytes.fromhex('225F205F281F261F241F221F4E75')
    m.patch(q,largest,lp); m.patch(q,tdone,done); m.patch(q,tnc,tcok); m.patch(q,tskipc,tadv); m.patch(q,tnf,tfok); m.patch(q,tskipf,tadv); m.patch(q,tagain,tloop)
    m.patch(q,hdone,done); m.patch(q,hnc,hcok); m.patch(q,hskipc,hadv); m.patch(q,hnf,hfok); m.patch(q,hskipf,hadv)
    m.patch(q,cdone,hadv); m.patch(q,keep,cnxt); m.patch(q,cagain,cloop); m.patch(q,hagain,hloop)
    return bytes(q)


def build():
    # Reuse the M2.17 qualified allocator/free/bootstrap, replacing only AvailMem.
    image=bytearray(m.build())
    av=avail_wrapper_code_m218()
    if len(av)>0x100: raise ValueError('M2.18 AvailMem wrapper exceeds slot')
    image[0x0D00:0x0E00]=b'\xff'*0x100; image[0x0D00:0x0D00+len(av)]=av
    # Add M2.18 runtime assertions by redirecting M2.17's success branch to spare boot area.
    boot=image[8:0x0B00]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    p=boot.find(sig)
    if p<0: raise ValueError('M2.17 success gate not found')
    good_abs=8+p; branch_pos=good_abs+8
    # Keep old red failure target intact. New tests live after the old idle loop.
    bad_sig=bytes.fromhex('33FC000F00DFF18060FE'); bp=boot.find(bad_sig,p)
    if bp<0: raise ValueError('M2.17 fail gate not found')
    test_abs=8+bp+len(bad_sig)
    c=bytearray(); fails=[]
    def avail(flags,expect):
        c.extend(bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF28'))
        fails.append(m.cmpd0(c,expect))
    # After M2.17 restores all regions: static CHIP/FAST are 0x1000;
    # dynamic A=0xfe0 FAST, B=0x7e0 CHIP, C=0xe0 FAST.
    avail(MEMF_FAST|MEMF_LARGEST,0x1000)
    avail(MEMF_CHIP|MEMF_LARGEST,0x1000)
    avail(MEMF_LARGEST,0x1000)
    # Fragment static FAST below dynamic A: allocate 0x100,0x100,0xe00 => no static free;
    # dynamic A must then be reported as largest FAST block (0xfe0).
    for size,expect in ((0x100,m.FAST_BASE),(0x100,m.FAST_BASE+0x100),(0xE00,m.FAST_BASE+0x200)):
        c.extend(bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('223C')+struct.pack('>I',MEMF_FAST)+bytes.fromhex('4EAEFF3A')); fails.append(m.cmpd0(c,expect))
    avail(MEMF_FAST|MEMF_LARGEST,m.AFREE)
    # Restore static FAST and verify largest returns to 0x1000.
    for addr,size in ((m.FAST_BASE,0x100),(m.FAST_BASE+0x100,0x100),(m.FAST_BASE+0x200,0xE00)):
        c.extend(bytes.fromhex('227C')+struct.pack('>I',addr)+bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('4EAEFF2E'))
    avail(MEMF_FAST|MEMF_LARGEST,0x1000)
    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    fail=len(c); c+=m.mw(0x000f,m.COLOR00); idle=len(c); c+=bytes.fromhex('60FE')
    for x in fails: m.patch(c,x,fail)
    m.patch(c,ok,idle)
    if test_abs+len(c)>=0x0B00: raise ValueError('M2.18 runtime probe exceeds bootstrap area')
    image[test_abs:test_abs+len(c)]=c
    # Redirect old green path to tests (Bcc displacement base = opcode+2).
    disp=test_abs-(branch_pos+2); struct.pack_into('>h',image,branch_pos+2,disp)
    # Rename marker/ident without changing fixed slots.
    image[MARKER_OFF:IDENT_OFF]=b'\xff'*(IDENT_OFF-MARKER_OFF); image[MARKER_OFF:MARKER_OFF+len(MARKER)]=MARKER
    image[IDENT_OFF:m.NAME_A_OFF]=b'\xff'*(m.NAME_A_OFF-IDENT_OFF); image[IDENT_OFF:IDENT_OFF+len(IDENT)]=IDENT
    struct.pack_into('>I',image,m.ROM_SIZE-4,0); total=0
    for o in range(0,m.ROM_SIZE-4,4): total=m.ones(total,struct.unpack_from('>I',image,o)[0])
    total=(total&0xffffffff)+(total>>32); struct.pack_into('>I',image,m.ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_18_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data); print(f'M2.18 ROM built: {out} ({len(data)} bytes)')
