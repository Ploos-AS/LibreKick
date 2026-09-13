# LibreKick M2.25 Qualification

## Scope

M2.25 qualifies the predecessor-only dynamic `FreeMem()` coalescing path in the current Exec-compatible memory-manager slice. It is a focused qualification, not a claim of complete AmigaOS Exec allocator compatibility.

## Qualification result

Status: **PASS / QUALIFIED**

GitHub Actions FS-UAE qualification:

- workflow run: `34765523134` (#80)
- job: `103745678336`
- ROM size: 524288 bytes
- static checker: PASS
- ROM checksum: `0xffffffff`
- runtime screenshot semantic gate: PASS
- green ratio: `0.8911`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- artifact: `10320521542`
- artifact ZIP SHA-256: `43842dcce988456f9e7e4f2b1d4e2314017ed1f1055212efd9c5abb0634a6d60`
- artifact size: 9120 bytes

## Qualified behavior

The runtime probe allocates three adjacent blocks from dynamic FAST region A, frees the first block, and then frees the second while the third remains live. This forces a backward/predecessor merge without a simultaneous successor merge. The probe verifies free-list topology, merged size, `mh_Free` accounting, final full coalescing, and aggregate FAST availability before reaching the green gate.

## Non-claims

M2.25 does not by itself qualify every FreeMem edge case, malformed ranges, overlapping frees, interrupt/task concurrency, or complete AmigaOS 3.1 Exec semantics.
