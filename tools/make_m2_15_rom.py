#!/usr/bin/env python3
from pathlib import Path
import struct,sys
from make_m2_14_rom import *
MARKER_OFF=0x1C00; IDENT_OFF=0x1C80; NAME_A_OFF=0x1CE0; NAME_B_OFF=0x1D00
IDSTRING_ADDR=ROM_BASE+IDENT_OFF; NAME_A_ADDR=ROM_BASE+NAME_A_OFF; NAME_B_ADDR=ROM_BASE+NAME_B_OFF
DYN_HEAD=0x4C00; ABASE=0x9000; ASIZE=0x1000; AFREE=ASIZE-32; APAY=ABASE+32
BBASE=0xA000; BSIZE=0x800; BFREE=BSIZE-32; BPAY=BBASE+32
FUNCS={198:ROM_BASE+0x0B00,210:ROM_BASE+0x0C00,216:ROM_BASE+0x0D00,618:ROM_BASE+ADDMEM_OFF}
def cmpabsw(c,v,a):
 c+=bytes.fromhex('0C79')+struct.pack('>H',v&0xffff)+struct.pack('>I',a); return branch(c,0x6600)
def addmemlist_code():
 q=bytearray(bytes.fromhex('2F032F042F0A2F0B2600'))
 q+=bytes.fromhex('0C8300000028'); small=branch(q,0x6500)
 q+=bytes.fromhex('2839')+struct.pack('>I',DYN_HEAD)+bytes.fromhex('208442A80004114200092149000A3141000E45E80020214A0010214A00142808D883214400180483000000202143001C4292254300044A84')
 noold=branch(q,0x6700); q+=bytes.fromhex('264427480004'); pub=len(q)
 q+=bytes.fromhex('23C8')+struct.pack('>I',DYN_HEAD); out=len(q); q+=bytes.fromhex('265F245F281F261F4E75')
 patch(q,small,out); patch(q,noold,pub); return bytes(q)
def avail_wrapper_code():
 q=bytearray(bytes.fromhex('2F012F022F032F08'))
 q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+BASE_AVAIL_OFF)+bytes.fromhex('260008010011'); largest=branch(q,0x6600)
 q+=bytes.fromhex('2079')+struct.pack('>I',DYN_HEAD); loop=len(q); q+=bytes.fromhex('20084A80'); done=branch(q,0x6700)
 q+=bytes.fromhex('3428000E08010001'); nc=branch(q,0x6700); q+=bytes.fromhex('08020001'); sc=branch(q,0x6700); cok=len(q)
 q+=bytes.fromhex('08010002'); nf=branch(q,0x6700); q+=bytes.fromhex('08020002'); sf=branch(q,0x6700); fok=len(q)
 q+=bytes.fromhex('D6A8001C'); adv=len(q); q+=bytes.fromhex('2050'); again=branch(q,0x6000); base=len(q); q+=bytes.fromhex('2003'); out=len(q); q+=bytes.fromhex('205F261F241F221F4E75')
 patch(q,largest,base); patch(q,done,base); patch(q,nc,cok); patch(q,sc,adv); patch(q,nf,fok); patch(q,sf,adv); patch(q,again,loop); return bytes(q)
def build():
 image=bytearray([0xff])*ROM_SIZE; struct.pack_into('>II',image,0,SP,PC); c=bytearray(bytes.fromhex('46FC2700'))
 c+=mb(3,CIAA_DDRA)+bclr0(CIAA_PRA)+ml(EXEC_BASE,4)+ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)
 c+=mw(0,EXEC_BASE+14)+mw(618,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(15,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
 for off,t in FUNCS.items(): c+=vector(t,EXEC_BASE-off)
 c+=mw(MEMF_CHIP,MEMHDR+MH_ATTR)+ml(MEM_BASE,MEMHDR+MH_FIRST)+ml(MEM_BASE,MEMHDR+MH_LOWER)+ml(MEM_BASE+MEM_SIZE,MEMHDR+MH_UPPER)+ml(MEM_SIZE,MEMHDR+MH_FREE)+ml(0,MEM_BASE)+ml(MEM_SIZE,MEM_BASE+4)
 c+=mw(MEMF_FAST,FAST_HDR+MH_ATTR)+ml(FAST_BASE,FAST_HDR+MH_FIRST)+ml(FAST_BASE,FAST_HDR+MH_LOWER)+ml(FAST_BASE+FAST_SIZE,FAST_HDR+MH_UPPER)+ml(FAST_SIZE,FAST_HDR+MH_FREE)+ml(0,FAST_BASE)+ml(FAST_SIZE,FAST_BASE+4)+ml(0,DYN_HEAD)+mw(0x0f00,COLOR00)+b'\x4d\xf9'+struct.pack('>I',EXEC_BASE)
 fails=[]
 def avail(f,e):
  nonlocal c; c+=bytes.fromhex('223C')+struct.pack('>I',f)+bytes.fromhex('4EAEFF28'); fails.append(cmpd0(c,e))
 def add(base,size,attrs,pri,name):
  nonlocal c; c+=bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('223C')+struct.pack('>I',attrs)+bytes.fromhex('243C')+struct.pack('>I',pri)+bytes.fromhex('207C')+struct.pack('>I',base)+bytes.fromhex('227C')+struct.pack('>I',name)+bytes.fromhex('4EAEFD96')
 avail(MEMF_CHIP,MEM_SIZE); avail(MEMF_FAST,FAST_SIZE); avail(MEMF_TOTAL,MEM_SIZE+FAST_SIZE)
 add(ABASE,ASIZE,MEMF_FAST,5,NAME_A_ADDR); fails += [cmpabs(c,ABASE,DYN_HEAD),cmpabs(c,0,ABASE),cmpabs(c,APAY,ABASE+MH_FIRST),cmpabs(c,AFREE,ABASE+MH_FREE)]
 add(BBASE,BSIZE,MEMF_CHIP,3,NAME_B_ADDR); fails += [cmpabs(c,BBASE,DYN_HEAD),cmpabs(c,ABASE,BBASE),cmpabs(c,0,BBASE+4),cmpabs(c,BBASE,ABASE+4),cmpabsw(c,MEMF_FAST,ABASE+MH_ATTR),cmpabsw(c,MEMF_CHIP,BBASE+MH_ATTR)]
 avail(MEMF_FAST,FAST_SIZE+AFREE); avail(MEMF_CHIP,MEM_SIZE+BFREE); avail(MEMF_TOTAL,MEM_SIZE+FAST_SIZE+AFREE+BFREE); avail(MEMF_LARGEST,0x1000)
 c+=mw(0x00f0,COLOR00); good=branch(c,0x6000); bad=len(c); c+=mw(0x000f,COLOR00); idle=len(c); c+=bytes.fromhex('60FE')
 for p in fails: patch(c,p,bad)
 patch(c,good,idle); image[8:8+len(c)]=c
 fa=relocate_region(allocmem_core_code(),MEMHDR,FAST_HDR); ff=relocate_region(freemem_code(),MEMHDR,FAST_HDR)
 routines={0x0B00:alloc_wrapper_code(),0x0C00:free_wrapper_code(),0x0D00:avail_wrapper_code(),CHIP_ALLOC_OFF:allocmem_core_code(),CHIP_FREE_OFF:freemem_code(),FAST_ALLOC_OFF:fa,FAST_FREE_OFF:ff,CHIP_LARGEST_OFF:largest_code(MEMHDR),FAST_LARGEST_OFF:largest_code(FAST_HDR),ADDMEM_OFF:addmemlist_code(),BASE_AVAIL_OFF:base_avail_code()}
 for (off,code),(nxt,_) in zip(sorted(routines.items()),sorted(routines.items())[1:]+[(MARKER_OFF,b'')]):
  if off+len(code)>nxt: raise ValueError(f'overlap {off:x}')
  image[off:off+len(code)]=code
 marker=b'LIBREKICK-M2.15\0EXEC-LINKED-DYNAMIC-MEMLIST\0'; ident=b'exec.library\0LibreKick M2.15 linked dynamic MemList slice 40.15\0'
 image[MARKER_OFF:MARKER_OFF+len(marker)]=marker; image[IDENT_OFF:IDENT_OFF+len(ident)]=ident; image[NAME_A_OFF:NAME_A_OFF+22]=b'M2.15 dynamic FAST A\0'; image[NAME_B_OFF:NAME_B_OFF+22]=b'M2.15 dynamic CHIP B\0'
 struct.pack_into('>I',image,ROM_SIZE-4,0); total=0
 for o in range(0,ROM_SIZE-4,4): total=ones(total,struct.unpack_from('>I',image,o)[0])
 total=(total&0xffffffff)+(total>>32); struct.pack_into('>I',image,ROM_SIZE-4,(~total)&0xffffffff); return image
if __name__=='__main__':
 out=Path(sys.argv[1]); d=build(); out.write_bytes(d); print(f'M2.15 ROM built: {out} ({len(d)} bytes)')
