# M2.20 Exec AllocMem No-Region Semantics Qualification

Status: **PASS**

M2.20 changes the `AllocMem()` no-region path so requests without explicit `MEMF_CHIP` or `MEMF_FAST` prefer FAST memory, then fall back to CHIP, then to dynamically registered memory.

## Qualified scope

The runtime qualifies this compatibility slice:

- explicit `MEMF_CHIP` remains CHIP-only;
- explicit `MEMF_FAST` remains FAST-only;
- `MEMF_CHIP|MEMF_FAST` is rejected;
- no explicit region bits prefer static FAST;
- if static FAST is exhausted, no-region allocation falls back to static CHIP;
- if both static regions are exhausted, no-region allocation traverses the linked dynamic `MemHeader` list in its existing priority order and accepts the first region that can satisfy the request;
- `MEMF_CLEAR` remains compatible with dynamic-region matching;
- inherited M2.17, M2.18 and M2.19 runtime semantics remain green.

The qualified dynamic chain is priority ordered `C -> A -> B`, where C is FAST but too small for the qualified `$100` dynamic fallback request, so A is selected.

## Runtime semantic probe

1. `AllocMem($100, 0)` must return the static FAST base.
2. Consume the rest of static FAST explicitly.
3. `AllocMem($100, 0)` must fall back to static CHIP.
4. Consume the rest of static CHIP explicitly.
5. `AllocMem($100, 0)` must traverse the dynamic list and return A's payload at `$9020` after C cannot satisfy the request.
6. `AllocMem($100, MEMF_CHIP|MEMF_FAST)` must return zero.
7. Free the probe allocations so subsequent inherited semantics remain stable.

Diagnostic colours in the final qualified image use the normal convention: red = running, blue = semantic failure, green = complete PASS.

## Regression fixes captured by the checker

Two 68000-width bugs were found during qualification and are now guarded statically:

- `mh_Attributes` is WORD-sized, so D4 is cleared before loading it for a later long comparison;
- the normalized dynamic-region mode is copied with `MOVE.L D5,D1`, not `MOVE.W`, so upper requirement bits such as `MEMF_CLEAR` cannot survive in D1 and cause a false attribute mismatch.

The checker also verifies FAST-before-CHIP call ordering on the no-region path, linked dynamic traversal, the CHIP|FAST rejection probe, and the standard green/blue runtime gates.

## Static gate

```sh
make clean
make check
```

## Runtime gates

Automated GitHub Actions final cleanup run:

- workflow: `FS-UAE runtime qualification`
- run: `34758039074` (#51)
- job: `103725746213`
- qualification HEAD: `c4a761ded1e62dfbb220de27f3e8b5c109b2bbd7`
- runner: Ubuntu 24.04
- FS-UAE package: 3.1.66
- ROM size: 524288 bytes
- checksum: `0xffffffff`
- screenshot: 960x540
- green ratio: 0.8911
- blue ratio: 0.0000
- red ratio: 0.0000
- dominant RGB: `0,240,0`
- result: **PASS**
- evidence artifact: `fs-uae-runtime-qualification`
- artifact ID: `10318145908`
- artifact ZIP SHA-256: `8ab61d65879d1976135a3cb5825bcc97984e60ef8bf8e94382d20ad388af15f4`

The earlier diagnostic run #49 also passed before the temporary per-milestone failure colours were removed. Run #51 is the canonical qualification evidence for the cleaned M2.20 image.

## Non-claims

M2.20 does not claim complete Amiga Exec allocator equivalence, malformed `FreeMem()` semantics, arbitrary official allocation heuristics, or full system compatibility. It qualifies only the routing and fallback semantics explicitly exercised above on the current LibreKick memory-manager slice.

## Runtime record

- Date: 2026-09-13
- CPU/model: A500 / 68000
- Diagnostic screen: green
- Result: **PASS**
