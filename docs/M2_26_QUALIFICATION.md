# LibreKick M2.26 Qualification

## Scope

M2.26 qualifies the dynamic `FreeMem()` successor-only coalescing path. It complements M2.25's predecessor-only case and remains a focused Exec-compatible memory-manager slice rather than a claim of complete Exec allocator compatibility.

## Qualification result

Status: **PASS / QUALIFIED**

GitHub Actions FS-UAE qualification:

- workflow run: `34771119633` (#86)
- job: `103760778280`
- ROM size: 524288 bytes
- static checker: PASS
- ROM checksum: `0xffffffff`
- runtime screenshot semantic gate: PASS
- green ratio: `0.8911`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`
- artifact: `10321688697`
- artifact ZIP SHA-256: `a172507e8c2d4dacb1e19be94ea81e4d195d282d7bb120228f1b6046e5ad3050`
- artifact size: 9121 bytes

## Qualified behavior

The runtime probe creates a fragmented dynamic FAST free list and frees blocks that are adjacent to a free successor while their predecessor remains allocated. It checks forward coalescing, `mh_First`, free-chunk size, `mh_Free`, full restoration, and final FAST `AvailMem()` accounting.

## Qualification-history note

The first M2.26 run failed in the static checker before FS-UAE runtime because the checker incorrectly required derived setup values to occur as immediate constants in the probe. The checker was corrected in commit `6e255a97fcf6b89b3f17d94d004aded475cf668a`; the corrected qualification then passed.

## Non-claims

M2.26 does not by itself qualify all `AllocMem()`/`FreeMem()` ordering, malformed-input behavior, all memory flags, concurrency/Forbid semantics, or complete Commodore/AmigaOS 3.1 Exec behavior.
