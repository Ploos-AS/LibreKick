# LibreKick M2.22 qualification

## Scope

M2.22 qualifies dynamic `AllocMem()` whole-chunk removal when the selected free `MemChunk` is not the list head. The runtime probe specifically exercises the `prev->mc_Next = current->mc_Next` relink path after first-fit skips a smaller leading chunk.

This is a focused allocator/runtime slice, not a claim of complete Amiga Exec memory-manager compatibility.

## Qualified revision

- Revision: `5992f5237a27c639eec49763eb66e0bc68618a05`
- FS-UAE workflow: `FS-UAE runtime qualification` #63
- Run: `34759615114`
- Job: `103729990121`

## Result

PASS.

- ROM size: 524288 bytes
- static checker: PASS
- Kickstart checksum: `0xffffffff`
- runtime diagnostic: green
- `green_ratio=0.8911`
- `blue_ratio=0.0000`
- `red_ratio=0.0000`
- dominant RGB: `0,240,0`

The successful runtime path verifies that an exact-size allocation can skip a too-small head chunk, consume a later chunk whole, relink the predecessor directly to the following chunk, preserve free-byte accounting, and subsequently restore/coalesce the region through `FreeMem()`.

## Evidence artifact

- Artifact ID: `10318617063`
- Artifact ZIP SHA-256: `ddb1d61da673a286444a6bc17669a24a2cd08a89b6874b47e609273713eec437`
- Run: https://github.com/Ploos-AS/LibreKick/actions/runs/34759615114

## Note on the initial failed probe

The first M2.22 runtime probe failed because the test expected the untouched tail `MemChunk` size to equal total `mh_Free`. The allocator was correct; the probe conflated per-chunk size with aggregate free bytes. The corrected probe keeps the tail chunk at `$0b60` while `mh_Free` is `$0c60` after the exact `$180` allocation.
