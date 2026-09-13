# LibreKick M2.23 qualification

M2.23 qualifies the **dynamic AllocMem whole-chunk head replacement path** inherited from the M2.21 allocator core.

## Scope

The runtime probe constructs a fragmented dynamic FAST MemHeader A where the first free MemChunk is exactly `0x180` bytes and is followed by another free chunk. An exact `AllocMem(0x180, MEMF_FAST)` must consume that head chunk whole and update `mh_First` to the existing successor.

This complements M2.22, which qualified exact whole-chunk removal from a **non-head** position via `prev->mc_Next`.

M2.23 does not claim complete Exec memory-manager compatibility or malformed-input semantics.

## Runtime topology

Before the exact allocation, MemHeader A is checked as:

- `mh_First = $9020`
- `$9020`: `mc_Bytes=$180`, `mc_Next=$93A0`
- `$93A0`: `mc_Bytes=$C60`, `mc_Next=0`
- `mh_Free=$DE0`

After `AllocMem($180, MEMF_FAST)`:

- return value is `$9020`
- `mh_First=$93A0`
- successor chunk remains `$93A0/$C60`
- `mh_Free=$C60`

The probe then frees the live blocks, requires full coalescing back to A's original `$FE0` free payload, restores static FAST, and verifies FAST availability accounting.

## Qualification evidence

Final qualified revision:

- HEAD: `fb46ed014aba26e8c8ba0b93f0ee3379253ac69e`
- workflow: **FS-UAE runtime qualification #70**
- run ID: `34761023201`
- job ID: `103733762648`
- ROM size: `524288` bytes
- static checker: PASS
- Kickstart checksum: `0xffffffff`
- runtime gate: PASS
- `green_ratio=0.8911`
- `blue_ratio=0.0000`
- `red_ratio=0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`
- artifact ID: `10318693892`
- artifact ZIP SHA-256: `dfb89bbe1d6f514c0d94f773bb273748d05f7a0c7e93dae089b852d38606dadb`
- artifact size: `9122` bytes

The first M2.23 attempt did not reach runtime because the accumulated bootstrap probes no longer fit below `$0B00`. The M2.23 probe was therefore moved to a dedicated unused ROM window at offsets `$2200-$23FF`; this was a qualification-layout correction, not an allocator semantic fix.

## Verdict

**M2.23 QUALIFIED** for the stated whole-chunk head-replacement semantics on the automated A500/FS-UAE qualification profile.
