# LibreKick M2.27 qualification

## Scope

M2.27 qualifies the bidirectional coalescing path in the dynamic `FreeMem()` core. The focused runtime probe creates two free `MemChunk` neighbors with one live `$100` allocation between them, then frees that middle allocation. A single `FreeMem()` call must merge with both the successor and predecessor and restore one complete dynamic FAST-A chunk.

This is a focused qualification slice. It does not claim complete Exec memory-manager compatibility, malformed-input behavior, or every possible free-list topology.

## Qualified topology

Dynamic FAST region A:

- header `$9000`
- payload `$9020`
- full payload size `$0FE0`

The probe exhausts static FAST and allocates three `$100` blocks from A. It then frees the first and third allocations, producing:

- `$9020/$0100 -> $9220/$0DE0`
- `$9120/$0100` remains allocated between them
- aggregate `mh_Free = $0EE0`

Freeing `$9120/$0100` must coalesce both directions and leave:

- `mh_First = $9020`
- `$9020.next = 0`
- `$9020.bytes = $0FE0`
- `mh_Free = $0FE0`

The probe then restores static FAST and checks aggregate FAST availability.

## Evidence

Qualification commit: `4fc1691fcb1dd5bedd79422feac202d499e79ff5`

GitHub Actions workflow: **FS-UAE runtime qualification #91**

- run: `34773557471`
- job: `103767419584`
- ROM size: 524288 bytes
- static checker: PASS
- ROM checksum: `0xffffffff`
- runtime gate: PASS
- `green_ratio = 0.8911`
- `blue_ratio = 0.0000`
- `red_ratio = 0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`

Artifact:

- ID: `10322966626`
- size: 9121 bytes
- SHA-256: `817c5fecf725bd24b08efc2dadc43df1410d31eeec4ebd6e56df948e1e683c51`
- URL: `https://github.com/Ploos-AS/LibreKick/actions/runs/34773557471/artifacts/10322966626`

## Result

**M2.27 QUALIFIED.** The tested dynamic `FreeMem()` path correctly coalesces one newly freed block with both adjacent free chunks in the qualified topology.