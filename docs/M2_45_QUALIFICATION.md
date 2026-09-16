# LibreKick M2.45 Qualification

Status: **EMULATOR QUALIFIED / PASS**

M2.45 converges the shared private `SwapCurrentTask` runtime primitive into the retained 512 KiB LibreKick ROM path. It builds on M2.44 and keeps the existing shared `GetSysBase`, `GetCurrentTask`, and `SetCurrentTask` primitives.

## Qualified revision

- Qualified HEAD: `1fe6adaba0a2eb7e1ca352f9a7066efba66704ec`
- ROM: `build/librekick-m2_45.rom`
- ROM size: 524288 bytes
- ROM checksum: `0xffffffff`
- Runtime marker: `LIBREKICK-M2.45` / shared Exec task-swap runtime

## Shared private Exec runtime primitives

M2.45 retains the shared private runtime helpers and adds `SwapCurrentTask` to the ordinary 512 KiB ROM path:

- `GetSysBase`
- `GetCurrentTask`
- `SetCurrentTask`
- `SwapCurrentTask`

`SwapCurrentTask` replaces `ExecBase->ThisTask` with the task pointer supplied in D0 and returns the previous task pointer in D0. D1 is scratch.

The shared `ExecBase->ThisTask` offset is `0x114`.

`SwapCurrentTask` machine code is:

```
207900000004222801142140011420014e75
```

Equivalent 68000 operation sequence:

```
MOVEA.L $00000004,A0
MOVE.L  $0114(A0),D1
MOVE.L  D0,$0114(A0)
MOVE.L  D1,D0
RTS
```

## Runtime qualification

GitHub Actions FS-UAE runtime qualification:

- Workflow: `FS-UAE runtime qualification`
- Run: `35098571001` (#321)
- Job: `104801943451` (`fs-uae-runtime`)
- Qualified commit: `1fe6adaba0a2eb7e1ca352f9a7066efba66704ec`
- Runner image: Ubuntu 24.04.5 LTS / `ubuntu-24.04`
- FS-UAE: `3.1.66-2build2`
- OpenGL renderer: Mesa llvmpipe (LLVM 20.1.2, 256 bits)

The runner built and statically checked M2.45 before executing it:

```
M2.45 ROM built: build/librekick-m2_45.rom (524288 bytes)
shared_primitives=GetSysBase,GetCurrentTask,SetCurrentTask,SwapCurrentTask
M2.45 check PASS: build/librekick-m2_45.rom (524288 bytes)
Shared SwapCurrentTask reversible task-pointer convergence; checksum=0xffffffff
scope=private runtime primitive; public Exec scheduler/vectors/full task switch not claimed
```

The FS-UAE diagnostic gate then reported:

```
image=960x540
green_ratio=0.8911
blue_ratio=0.0000
red_ratio=0.0000
dominant_rgb=0,240,0
dominant_ratio=0.8901
FS-UAE runtime gate PASS: green diagnostic screen
```

This proves that the M2.45 ROM reached its successful runtime path after the reversible task-pointer swap checks.

## Retained evidence

Runtime evidence was retained by GitHub Actions as:

- Artifact: `fs-uae-runtime-qualification`
- Artifact ID: `10447133491`
- ZIP size: 10527 bytes
- ZIP SHA-256: `58d3afafb2f89f9284377e8ef73126df75e4749ca083d09b289c26bf5b7c3904`

The artifact contains the runtime result, diagnostic screenshot, FS-UAE log/version, ROM/config information, and software-OpenGL information.

The LibreKick profile runtime matrix also passed for this qualified revision (run `35098570967`, #132), providing the corresponding retained-profile regression gate.

## Qualification result

**PASS.** M2.45 is emulator-qualified for the shared private `SwapCurrentTask` convergence milestone. The ordinary retained 512 KiB ROM now executes the same shared task-pointer runtime primitive family being developed for the A1000 WCS path.

## Scope and limitations

This milestone deliberately makes only a narrow runtime claim. It does **not** claim:

- a public Exec scheduler,
- public `Switch`, `Dispatch`, `Schedule`, `Reschedule`, or `FindTask` compatibility,
- public Exec negative vectors for these private helpers,
- saved/restored task CPU context as part of `SwapCurrentTask`,
- a complete task switch,
- full `exec.library` compatibility,
- real Amiga hardware qualification.

`SwapCurrentTask` is an internal/private scheduler-building primitive. Later milestones may use it as part of progressively more complete scheduling and context-switch machinery.