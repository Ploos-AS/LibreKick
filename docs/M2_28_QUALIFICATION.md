# LibreKick M2.28 qualification

## Scope

M2.28 qualifies the dynamic `FreeMem()` sorted insertion path when the returned block is adjacent to neither the predecessor nor the successor free chunk. This is deliberately narrower than claiming complete Exec memory-manager compatibility.

The probe allocates four `$100` blocks from dynamic FAST region A, leaving tail chunk `$9420/$BE0`. It then frees `$9120/$100` while `$9020`, `$9220`, and `$9320` remain allocated. The required free-list topology is therefore:

`$9120/$100 -> $9420/$BE0`

with no predecessor or successor coalescing. Cleanup then restores A to a single `$9020/$FE0` chunk.

## Initial checker failure

FS-UAE qualification #96, run `34773879360`, failed before runtime because the static checker expected allocator opcode bytes `214A0010` for the `mh_First` insertion path. The dynamic `FreeMem()` implementation actually uses `29490010` (`MOVE.L A1,16(A4)`). This was a checker-only mismatch; no runtime verdict was produced.

The checker was corrected in commit `f77c762a1ae3ffa2aaa442ba1283e2ab01f5f56a`.

## Qualified run

- workflow: FS-UAE runtime qualification #97
- run: `34774350396`
- job: `103769588692`
- commit: `f77c762a1ae3ffa2aaa442ba1283e2ab01f5f56a`
- ROM size: 524288 bytes
- static checker: PASS
- checksum: `0xffffffff`
- runtime semantic gate: PASS
- green ratio: `0.8911`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`
- artifact: `10322962828`
- artifact size: 9120 bytes
- artifact SHA-256: `8dde4f1372934e9c3bfa2fbc8b009ef84566b2f9e09ea4e54b1d1db92d44e9ab`
- artifact URL: `https://github.com/Ploos-AS/LibreKick/actions/runs/34774350396/artifacts/10322962828`

## Result

M2.28 is **QUALIFIED** for the stated sorted, non-coalescing dynamic `FreeMem()` insertion behavior.

This does not claim malformed-input handling, arbitrary overlapping frees, double-free behavior, or full AmigaOS Exec memory-manager compatibility.
