# LibreKick M2.24 Qualification

## Scope

M2.24 qualifies the dynamic allocator head-MemChunk split path exercised by the M2.24 runtime probe. This is a focused Exec-compatible memory-manager slice; it is not a claim of complete AmigaOS Exec allocator compatibility.

## Qualification result

Status: **PASS / QUALIFIED**

GitHub Actions FS-UAE qualification:

- workflow run: `34765266877` (#75)
- job: `103744997428`
- ROM size: 524288 bytes
- static checker: PASS
- ROM checksum: `0xffffffff`
- runtime screenshot semantic gate: PASS
- green ratio: `0.8911`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- artifact: `10320131233`
- artifact ZIP SHA-256: `5fb9b58b4ea81f430b873494eb15ab86efd7020f639b572dad8b63077006e1bc`
- artifact size: 9121 bytes

## Qualified behavior

The M2.24 probe specifically exercises splitting a fitting free `MemChunk` when that chunk is the head of a dynamic `MemHeader` free list, including the resulting `mh_First` replacement/accounting checks that gate the green runtime result.

## Non-claims

M2.24 does not by itself qualify every AllocMem/FreeMem ordering, malformed-input behavior, all memory flags, concurrency/Forbid semantics, or complete Commodore/AmigaOS 3.1 Exec behavior. Those remain milestone-specific work.
