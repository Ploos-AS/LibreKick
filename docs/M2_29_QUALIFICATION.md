# LibreKick M2.29 qualification

## Scope

M2.29 qualifies the established 8-byte size alignment used by the dynamic `AllocMem()` and `FreeMem()` paths. It is a focused memory-manager slice, not a claim of complete Exec memory semantics.

## Qualified behavior

The runtime probe first exhausts static FAST memory and the small priority-7 dynamic FAST region C so that the alignment checks are forced into dynamic FAST region A.

The probe then verifies:

- `AllocMem(1, MEMF_FAST)` consumes 8 bytes and returns `$9020`.
- `AllocMem(9, MEMF_FAST)` consumes 16 bytes and returns `$9028`.
- `mh_First` advances to `$9038` and `mh_Free` decreases by 24 bytes.
- `FreeMem($9020, 1)` and `FreeMem($9028, 9)` apply the same alignment rules.
- Dynamic FAST region A is restored to one `$9020/$FE0` free chunk.
- Final FAST `AvailMem()` accounting is restored.

## Qualification evidence

- Qualification commit: `0356822cad9dd5073c6dab78c4ed5564473a4739`
- Workflow: `FS-UAE runtime qualification` #102
- Run ID: `34775058673`
- Job ID: `103771549356`
- ROM size: 524288 bytes
- Static checker: PASS
- ROM checksum: `0xffffffff`
- Runtime color gate: PASS
- `green_ratio=0.8911`
- `blue_ratio=0.0000`
- `red_ratio=0.0000`
- Dominant RGB: `0,240,0`
- Dominant ratio: `0.8901`
- Artifact ID: `10323266049`
- Artifact size: 9120 bytes
- Artifact SHA-256: `7fc150b1b4148f7b948eb0aaf19e3b6e44f4f995baaf23eb97895b168d211a64`
- Artifact URL: `https://github.com/Ploos-AS/LibreKick/actions/runs/34775058673/artifacts/10323266049`

## Non-claims

M2.29 does not claim complete AmigaOS V40 memory-manager compatibility, malformed `FreeMem()` handling, every memory attribute combination, or concurrency/interrupt safety. It qualifies only the explicit alignment and restoration assertions gated by the green runtime path.
