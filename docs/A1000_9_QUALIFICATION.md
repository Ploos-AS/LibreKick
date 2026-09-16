# A1000.9 Qualification

Status: **EMULATOR QUALIFIED / PASS**

A1000.9 extends the stock-A1000 WCS runtime with the shared internal Exec primitive `SwapCurrentTask`, alongside `GetSysBase`, `GetCurrentTask`, and `SetCurrentTask`.

`SwapCurrentTask` atomically replaces the private `ExecBase->ThisTask` pointer supplied in D0 and returns the previous pointer in D0. D1 is scratch. This is an internal scheduler/runtime stepping stone only.

This milestone does **not** claim a public Exec scheduler, public `Switch()`/`Dispatch()`/`FindTask()` compatibility, public negative-vector compatibility, a complete task context switch, full Exec compatibility, or real-hardware qualification.

## Qualified revision

- commit: `21523bc935c4644a831baec45109993d6193d4c3`
- GitHub Actions run: `35096823217` (#96)
- job: `104796125827`
- runner OS: Ubuntu 24.04.5 LTS
- runner image: `ubuntu-24.04` version `20260907.300.1`
- FS-UAE: `3.1.66-2build2`

All six workflows associated with the qualified revision completed successfully, including the A1000 bootstrap runtime, A1000 kickdisk static qualification, profile runtime matrix, generic FS-UAE runtime qualification, A1000 bootstrap static qualification, and M1 static qualification.

## Build and static qualification

The runner built:

- `librekick-a1000.3-bootstrap.rom`: 65,536 bytes
- `librekick-a1000.9-wcs.bin`: 262,144 bytes
- `librekick-a1000.9-kickdisk.adf`: 901,120 bytes

A1000.9 reported:

- ExecBase: `$00003400`
- version: `40.9`
- shared primitives: `GetSysBase`, `GetCurrentTask`, `SetCurrentTask`, `SwapCurrentTask`
- WCS base: `$00fc0000`
- WCS entry: `$00fc0008`
- payload SHA-256: `fc4d4a2d0945ebec6029dd1f592425bf3a6a9d416df661df15e1b40d21332853`

The A1000.9 kickdisk static checker passed. The retained A1000.3 bootstrap static checker also passed with reset SP `$0003fffc` and reset PC `$00f80008`.

The private shared `SwapCurrentTask` helper is 68000 code equivalent to:

- `MOVEA.L $00000004,A0`
- `MOVE.L $0114(A0),D1`
- `MOVE.L D0,$0114(A0)`
- `MOVE.L D1,D0`
- `RTS`

Exact helper bytes: `207900000004222801142140011420014e75`.

## Runtime qualification

The A1000.3 DF0 bootstrap loaded and entered the A1000.9 WCS payload under FS-UAE. The runtime exercised the shared internal Exec task-pointer swap path and reached the green success gate.

The test starts with a controlled current-task sentinel, swaps to a replacement pointer while checking that the previous pointer is returned, verifies the new `ThisTask` state, then swaps back and verifies restoration of the original pointer.

Captured diagnostic result:

- image: 960x540
- green ratio: `0.9010`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.9010`
- result: `FS-UAE runtime gate PASS: green diagnostic screen`

The milestone therefore qualifies the A1000 WCS execution path containing `GetSysBase`, `GetCurrentTask`, `SetCurrentTask`, and `SwapCurrentTask` in the automated emulator environment.

## Evidence artifact

The qualifying run retained all ten expected evidence/build files, including the A1000.9 WCS payload and kickdisk.

- artifact: `librekick-a1000-bootstrap-runtime-qualification`
- artifact ID: `10446412826`
- artifact size: 5,552 bytes
- artifact ZIP SHA-256: `aa595fb9f77e863b96c2894f1cb164a9a66954867482b231c92147389274ba1f`
- expires: 2026-12-15

## Scope

A1000.9 is an emulator-qualified internal shared-runtime milestone. It establishes a reversible current-task pointer swap primitive on the stock-A1000 WCS path and moves the private runtime closer to scheduler mechanics, but deliberately stops short of task context switching or public Exec scheduling APIs.

Real A1000 hardware qualification remains separate.
