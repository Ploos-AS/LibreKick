# A1000.7 Qualification

Status: **EMULATOR QUALIFIED / PASS**

A1000.7 extends the stock-A1000 WCS runtime with a second shared internal Exec primitive, `GetCurrentTask`, alongside `GetSysBase`.

This milestone does **not** claim public `FindTask()` compatibility, public Exec negative-vector compatibility, full Exec compatibility, or real-hardware qualification.

## Qualified revision

Runtime-qualified revision before the evidence-retention cleanup:

- commit: `cd233044d69f8887aa81f8a7813a82c5583da05f`
- GitHub Actions run: `35007832551`
- job: `104511966515`
- runner: Ubuntu 24.04.5 LTS (`ubuntu-24.04`)
- FS-UAE: `3.1.66-2build2`

## Build and static qualification

The runner built:

- `librekick-a1000.3-bootstrap.rom`: 65,536 bytes
- `librekick-a1000.7-wcs.bin`: 262,144 bytes
- `librekick-a1000.7-kickdisk.adf`: 901,120 bytes

A1000.7 reported:

- ExecBase: `$00003400`
- version: `40.7`
- shared primitives: `GetSysBase`, `GetCurrentTask`
- WCS base: `$00fc0000`
- WCS entry: `$00fc0008`
- payload SHA-256: `41fc37cae1cb62a4d6a435c4f3327f269c5060a1fed319c48b55cc4dbd7b0a31`

The A1000.7 kickdisk static checker passed. The A1000.3 bootstrap static checker also passed.

## Runtime qualification

The A1000.3 bootstrap loaded the A1000.7 WCS payload from DF0 under FS-UAE. The WCS runtime executed both shared internal Exec primitives and reached the success gate.

Captured diagnostic result:

- image: 960x540
- green ratio: `0.9010`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.9010`
- result: `FS-UAE runtime gate PASS: green diagnostic screen`

This proves the A1000.7 WCS slice executes the shared `GetSysBase` and `GetCurrentTask` path successfully in the automated emulator qualification environment.

## Evidence artifact

The qualifying run uploaded artifact:

- name: `librekick-a1000-bootstrap-runtime-qualification`
- artifact ID: `10412920204`
- ZIP SHA-256: `7c2d85aa07ed5d57e91601690ea942e336fb4c6c4499a8d172000e49f57e44ba`

That run still contained stale A1000.6 artifact path entries, so the runtime evidence bundle retained the generic runtime evidence but omitted the newly generated A1000.7 WCS/kickdisk files. The workflow was corrected immediately after qualification to retain the A1000.7 files on subsequent runs.

## Scope

A1000.7 is an emulator-qualified internal runtime milestone. Remaining work includes broader shared Exec runtime convergence, eventual public Exec ABI/vector work, and separate real A1000 hardware qualification.
