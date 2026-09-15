# A1000.8 Qualification

Status: **EMULATOR QUALIFIED / PASS**

A1000.8 extends the stock-A1000 WCS runtime with the shared internal Exec primitive `SetCurrentTask`, alongside `GetSysBase` and `GetCurrentTask`.

This milestone does **not** claim a public Exec scheduler, public `FindTask()` compatibility, public negative-vector compatibility, full Exec compatibility, or real-hardware qualification.

## Qualified revision

- commit: `12f64a44694b612e08941bf6ec85236beea53a25`
- GitHub Actions run: `35016333485`
- job: `104540585570`
- runner OS: Ubuntu 24.04.5 LTS
- runner image: `ubuntu-24.04` version `20260907.300.1`
- FS-UAE: `3.1.66-2build2`

## Build and static qualification

The runner built:

- `librekick-a1000.3-bootstrap.rom`: 65,536 bytes
- `librekick-a1000.8-wcs.bin`: 262,144 bytes
- `librekick-a1000.8-kickdisk.adf`: 901,120 bytes

A1000.8 reported:

- ExecBase: `$00003400`
- version: `40.8`
- shared primitives: `GetSysBase`, `GetCurrentTask`, `SetCurrentTask`
- WCS base: `$00fc0000`
- WCS entry: `$00fc0008`
- payload SHA-256: `c40052cb9aab872fd8f420f41bc1ccfffc83dfaee196e48f0995217af9629efd`

The A1000.8 kickdisk static checker passed. The retained A1000.3 bootstrap static checker also passed with reset SP `$0003fffc` and reset PC `$00f80008`.

## Runtime qualification

The A1000.3 DF0 bootstrap loaded and entered the A1000.8 WCS payload under FS-UAE. The runtime exercised the shared internal Exec task-state path and reached the green success gate.

Captured diagnostic result:

- image: 960x540
- green ratio: `0.9010`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.9010`
- result: `FS-UAE runtime gate PASS: green diagnostic screen`

The milestone therefore qualifies the A1000 WCS execution path containing `GetSysBase`, `GetCurrentTask`, and `SetCurrentTask` in the automated emulator environment.

## Evidence artifact

The qualifying run retained all ten expected evidence/build files, including the A1000.8 WCS payload and kickdisk.

- artifact: `librekick-a1000-bootstrap-runtime-qualification`
- artifact ID: `10415787223`
- artifact size: 5,501 bytes
- artifact ZIP SHA-256: `97022a96b07af733c27f16321cbaf79e7d2c2ef375fab9c06ef0a255124f6d40`

## Scope

A1000.8 is an emulator-qualified internal shared-runtime milestone. It establishes controlled current-task state mutation on the A1000 WCS path, but deliberately stops short of claiming scheduling, task switching through public Exec APIs, or complete `exec.library` compatibility.

Real A1000 hardware qualification remains separate.
