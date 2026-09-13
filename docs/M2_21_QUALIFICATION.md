# M2.21 Exec Dynamic MemChunk Traversal Qualification

Status: **PASS**

M2.21 extends the dynamic `AllocMem()` core from a single `mh_First` assumption to first-fit traversal across an arbitrary linked `MemChunk` free list.

## Qualified scope

The runtime verifies that a dynamically registered FAST `MemHeader` can be fragmented into multiple free chunks and that `AllocMem()`:

- starts at `mh_First`;
- skips a first free chunk that is too small;
- continues through `mc_Next` links;
- allocates from a later suitable chunk;
- relinks either `mh_First` or the previous chunk as required;
- updates `mh_Free` consistently;
- preserves `FreeMem()` coalescing back to one complete free chunk.

The dynamic region used by the probe is the existing FAST registration at `$9000..$9fff`, with payload beginning at `$9020`.

## Runtime semantic probe

1. Exhaust static FAST memory.
2. Allocate three `$100` blocks from dynamic FAST.
3. Free the first and third blocks while the middle block remains live, producing a fragmented free list.
4. Confirm the first free chunk is only `$100` bytes.
5. Request `$180` FAST.
6. Confirm the allocator skips the first chunk and returns `$9220` from the later free chunk.
7. Verify `mh_First`, `mc_Next`, chunk sizes and `mh_Free` accounting.
8. Free the allocation and the remaining live block.
9. Confirm the dynamic region coalesces back to one `$fe0`-byte chunk at `$9020`.
10. Restore static FAST and verify aggregate FAST availability.

Diagnostic colours: red = running, blue = semantic failure, green = complete PASS.

## Runtime gates

Automated GitHub Actions:

- workflow: `FS-UAE runtime qualification`
- run: `34758248894`
- runner: Ubuntu 24.04
- FS-UAE package: 3.1.66
- screenshot: 960x540
- green ratio: 0.8911
- blue ratio: 0.0000
- red ratio: 0.0000
- dominant RGB: `0,240,0`
- result: PASS
- evidence artifact ID: `10316894523`
- artifact SHA-256: `c4a4a9e79a6114b8ea0473a906c05ce98250ef10a488935fa271ed7b46218a7d`

## Non-claims

M2.21 qualifies first-fit traversal and split allocation from a later `MemChunk`. It does not yet separately qualify whole-chunk removal of a non-head free chunk when the request exactly consumes that chunk.

## Runtime record

- Date: 2026-09-13
- CPU/model: A500 / 68000
- ROM size: 524288 bytes
- checksum gate: `0xffffffff`
- GitHub qualification HEAD: `af9bd3080316439424e09da54de74941381702e7`
- Diagnostic screen: green
- Result: **PASS**
