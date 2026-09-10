#!/usr/bin/env python3
"""Build LibreKick M2.6: first deterministic Exec memory-management slice."""
from pathlib import Path
import struct, sys
from make_m2_5_rom import enqueue_code, findname_code

ROM_SIZE=512*1024; ROM_BASE=0x00F80000; SP=0x0007FFFC; PC=ROM_BASE+8
EXEC_BASE=0x00003000; COLOR00=0x00DFF180; CIAA_PRA=0x00BFE001; CIAA_DDRA=0x00BFE201
STATE0=0x00003100; STATE1=0x00003104; POOL0=0x00004000; POOL1=0x00004100; BLOCK=256
MARKER_OFF=0x1200; IDENT_OFF=0x1280; IDSTRING_ADDR=ROM_BASE+IDENT_OFF
FUNCS={198:ROM_BASE+0x0B00,210:ROM_BASE+0x0B80,234:ROM_BASE+0x0800,240:ROM_BASE+0x0840,246:ROM_BASE+0x0880,252:ROM_BASE+0x08C0,258:ROM_BASE+0x0900,264:ROM_BASE+0x0940,270:ROM_BASE+0x0A00,276:ROM_BASE+0x0A80}

def ml(v,a): return b'\x23\xfc'+struct.pack('>II',v,a)
def mw(v,a): return b'\x33\xfc'+struct.pack('>H',v)+struct.pack('>I',a)
def mb(v,a): return b'\x13\xfc'+struct.pack('>H',v&0xff)+struct.pack('>I',a)
def bclr0(a): return bytes.fromhex('08B90000')+struct.pack('>I',a)
def vector(t,a): return ml(0x4EF90000|((t>>16)&0xffff),a)+mw(t&0xffff,a+4)
def branch(c,op): p=len(c); c+=struct.pack('>HH',op,0); return p
def patch(c,p,t):
    d=t-(p+2)
    if not -32768<=d<=32767: raise ValueError('branch displacement')
    struct.pack_into('>h',c,p+2,d)
def cmpd0(c,v): c+=bytes.fromhex('0C80')+struct.pack('>I',v); return branch(c,0x6600)
def ones(t,v): t+=v; return (t&0xffffffff)+(t>>32)

def allocmem_code():
    q=bytearray()
    q+=bytes.fromhex('4A80'); fail0=branch(q,0x6700)                    # size==0
    q+=bytes.fromhex('0C8000000100'); fail1=branch(q,0x6200)            # size>256
    q+=bytes.fromhex('4AB9')+struct.pack('>I',STATE0); use0=branch(q,0x6700)
    q+=bytes.fromhex('4AB9')+struct.pack('>I',STATE1); use1=branch(q,0x6700)
    fail=len(q); q+=bytes.fromhex('70004E75')
    a0=len(q); q+=ml(1,STATE0)+bytes.fromhex('203C')+struct.pack('>I',POOL0)+bytes.fromhex('4E75')
    a1=len(q); q+=ml(1,STATE1)+bytes.fromhex('203C')+struct.pack('>I',POOL1)+bytes.fromhex('4E75')
    for p in (fail0,fail1): patch(q,p,fail)
    patch(q,use0,a0); patch(q,use1,a1)
    return bytes(q)

def freemem_code():
    q=bytearray(bytes.fromhex('2209'))                                  # move.l a1,d1
    q+=bytes.fromhex('0C81')+struct.pack('>I',POOL0); c0=branch(q,0x6700)
    q+=bytes.fromhex('0C81')+struct.pack('>I',POOL1); c1=branch(q,0x6700)
    q+=bytes.fromhex('4E75')
    z0=len(q); q+=ml(0,STATE0)+bytes.fromhex('4E75')
    z1=len(q); q+=ml(0,STATE1)+bytes.fromhex('4E75')
    patch(q,c0,z0); patch(q,c1,z1); return bytes(q)

def build():
    image=bytearray([0xff])*ROM_SIZE; struct.pack_into('>II',image,0,SP,PC)
    c=bytearray(bytes.fromhex('46FC2700')); c+=mb(3,CIAA_DDRA); c+=bclr0(CIAA_PRA); c+=ml(EXEC_BASE,4)
    c+=ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)
    c+=mw(0,EXEC_BASE+14)+mw(276,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(6,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
    for off,t in FUNCS.items(): c+=vector(t,EXEC_BASE-off)
    c+=ml(0,STATE0)+ml(0,STATE1)+mw(0x0f00,COLOR00)
    c+=b'\x4d\xf9'+struct.pack('>I',EXEC_BASE)                          # a6
    fails=[]
    c+=bytes.fromhex('70207200 4EAEFF3A'.replace(' ','')); fails.append(cmpd0(c,POOL0))
    c+=mw(0x0f80,COLOR00)
    c+=bytes.fromhex('70107200 4EAEFF3A'.replace(' ','')); fails.append(cmpd0(c,POOL1))
    c+=mw(0x0ff0,COLOR00)
    c+=bytes.fromhex('70087200 4EAEFF3A'.replace(' ','')); c+=bytes.fromhex('4A80'); fails.append(branch(c,0x6600))
    c+=bytes.fromhex('227C')+struct.pack('>I',POOL0)+bytes.fromhex('7020 4EAEFF2E'.replace(' ',''))
    c+=mw(0x008f,COLOR00)
    c+=bytes.fromhex('70407200 4EAEFF3A'.replace(' ','')); fails.append(cmpd0(c,POOL0))
    c+=mw(0x00f0,COLOR00); done=branch(c,0x6000); bad=len(c); c+=mw(0x000f,COLOR00); idle=len(c); c+=bytes.fromhex('60FE')
    for p in fails: patch(c,p,bad)
    patch(c,done,idle)
    if 8+len(c)>0x0800: raise ValueError('bootstrap overlaps routines')
    image[8:8+len(c)]=c
    routines={
      0x0800:bytes.fromhex('2F002F082F092F0A200A4A80671220122280234A00042040214900042489601020102280234800042440254900042089245F225F205F201F4E75'),
      0x0840:bytes.fromhex('2F002F082F092010228023480004204021490004206F00042089225F205F201F4E75'),
      0x0880:bytes.fromhex('2F002F082F092028000841E8000422882340000420402089206F000421490008225F205F201F4E75'),
      0x08C0:bytes.fromhex('2F002F012F082F0920290004221120402081204121400004225F205F221F201F4E75'),
      0x0900:bytes.fromhex('2F012F082F09201022402211670A208122412348000460027000225F205F221F4E75'),
      0x0940:bytes.fromhex('2F012F082F0920280008224022290004670E214100082241224141E80004228860027000225F205F221F4E75'),
      0x0A00:enqueue_code(),0x0A80:findname_code(),0x0B00:allocmem_code(),0x0B80:freemem_code()}
    ordered=sorted(routines.items())
    for (off,code),(nxt,_) in zip(ordered,ordered[1:]+[(MARKER_OFF,b'')]):
        if off+len(code)>nxt: raise ValueError(f'routine overlap at {off:x}')
        image[off:off+len(code)]=code
    marker=b'LIBREKICK-M2.6\0EXEC-ALLOCMEM-FREEMEM\0'; ident=b'exec.library\0LibreKick M2.6 deterministic memory slice 40.6\0'
    image[MARKER_OFF:MARKER_OFF+len(marker)]=marker; image[IDENT_OFF:IDENT_OFF+len(ident)]=ident
    struct.pack_into('>I',image,ROM_SIZE-4,0); total=0
    for o in range(0,ROM_SIZE-4,4): total=ones(total,struct.unpack_from('>I',image,o)[0])
    total=(total&0xffffffff)+(total>>32); struct.pack_into('>I',image,ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_6_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data); print(f'M2.6 ROM built: {out} ({len(data)} bytes)')
