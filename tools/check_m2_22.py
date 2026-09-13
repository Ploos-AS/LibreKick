#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.22\0EXEC-DYNAMIC-WHOLE-CHUNK-UNLINK\0' in data
assert b'exec.library\0LibreKick M2.22 dynamic whole-chunk unlink slice 40.22\0' in data
# M2.21 dynamic allocator must still include non-head whole-chunk relinking.
dyn=data[0x1600:0x1800]
assert bytes.fromhex('0C8300000008') in dyn, 'missing whole-chunk threshold'
assert bytes.fromhex('2451') in dyn, 'missing current.next load for whole-chunk removal'
assert bytes.fromhex('268A') in dyn, 'missing prev.next relink for non-head removal'
assert bytes.fromhex('214A0010') in dyn, 'missing mh_First replacement path'
# Runtime probe must include the exact-size $180 request and topology addresses.
boot=data[8:0x0B00]
assert bytes.fromhex('203C00000180') in boot
for value in (0x00009020,0x00009220,0x000094A0):
    assert struct.pack('>I',value) in boot
# The unchanged tail chunk at $94a0 is $b60 bytes. mh_Free after consuming the
# middle $180 chunk is $c60, so the probe must not conflate these two values.
assert struct.pack('>I',0x00000B60) in boot, 'missing corrected tail-chunk size expectation'
assert struct.pack('>I',0x00000C60) in boot, 'missing post-allocation mh_Free expectation'
assert bytes.fromhex('33FC00F000DFF180') in boot
assert bytes.fromhex('33FC000F00DFF18060FE') in boot
# Kickstart checksum must remain all ones.
def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.22 check PASS: {p} ({len(data)} bytes)')
print('Exec dynamic whole-chunk non-head unlink qualification; checksum=0xffffffff')
