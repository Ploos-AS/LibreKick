# A1000.10 Qualification

Status: **EMULATOR QUALIFIED / PASS**

A1000.10 extends the stock-A1000 WCS runtime with the shared private `HandoffTaskStack` primitive. It retains `GetSysBase`, `GetCurrentTask`, `SetCurrentTask`, and `SwapCurrentTask`, then performs a controlled cooperative handoff to a replacement task's prepared stack and a round trip back to the original task stack.

This is deliberately an internal scheduler/context-switch building block. It does **not** claim a complete CPU context switch, public Exec scheduler semantics, public negative vectors, full `exec.library` compatibility, or real-hardware qualification.

## Qualified revision

- commit: `a54561a752609a98ab4373b01027942fcc3e67ac`
- GitHub Actions workflow: `A1000 bootstrap runtime qualification`
- run: `35113409616` (#117)
- job: `104852631290` (`a1000-bootstrap-runtime`)
- runner label: `ubuntu-24.04`
- runtime step: `Run A1000.3 DF0 loader with A1000.10 task stack handoff WCS runtime in FS-UAE`
- result: success

The runtime job started at `2026-09-16T15:09:38Z` and completed at `2026-09-16T15:10:31Z`. The A1000.10 runtime step and evidence upload both completed successfully.

## Build and static contract

The retained A1000 architecture remains:

- A1000.3 bootstrap ROM: 65,536 bytes
- A1000.10 WCS payload: 262,144 bytes
- A1000.10 kickdisk: 901,120 bytes
- WCS base: `$00fc0000`
- WCS entry: `$00fc0008`
- ExecBase: `$00003400`
- Exec version/revision: `40.10`
- `ExecBase->ThisTask` offset: `0x114`
- private task `tc_SPReg` offset: `0x36`

The shared private primitive set is:

- `GetSysBase`
- `GetCurrentTask`
- `SetCurrentTask`
- `SwapCurrentTask`
- `HandoffTaskStack`

`HandoffTaskStack` machine code is:

```text
20790000000422680114234f003622092240214001142e69003620014e75
```

Equivalent 68000 operation sequence:

```text
MOVEA.L $00000004,A0
MOVEA.L $0114(A0),A1
MOVE.L  A7,$0036(A1)
MOVE.L  A1,D1
MOVEA.L D0,A1
MOVE.L  D0,$0114(A0)
MOVEA.L $0036(A1),A7
MOVE.L  D1,D0
RTS
```

The helper saves the post-JSR A7 in the old task's `tc_SPReg`, installs D0 as `ThisTask`, loads A7 from the replacement task's `tc_SPReg`, returns the old task pointer in D0, and transfers through the return PC prepared on the replacement stack.

## Controlled round-trip test

The A1000.10 WCS test uses:

- original task sentinel: `$0000c700`
- replacement task: `$0000c900`
- prepared replacement stack pointer: `$0000d7f0`
- WCS resume trampoline: `$00fc04c0`

The first handoff enters the replacement task's prepared stack and returns to the WCS resume trampoline. The trampoline invokes `HandoffTaskStack` again so execution returns to the original task stack. The runtime then verifies that `ThisTask` and the task-stack state are restored before reaching the green success gate.

## Runtime qualification

The retained evidence reports:

```text
image=960x540
green_ratio=0.9010
blue_ratio=0.0000
red_ratio=0.0000
dominant_rgb=0,240,0
dominant_ratio=0.9010
result=PASS
```

The evidence records FS-UAE version `3.1.66`.

The retained A1000.10 payload hashes are:

- WCS SHA-256: `df97a07652ddeae0ac751a0b450c7a87f1222a3b61929c87988fbc1f7ca64648`
- kickdisk SHA-256: `dba01dfdf0f6d2af8ab7bd762a379643781461b75241e0800466a3a68d848246`

## Evidence artifact

GitHub Actions retained the qualifying evidence as:

- artifact: `librekick-a1000-bootstrap-runtime-qualification`
- artifact ID: `10452509394`
- artifact size: 5,657 bytes
- artifact digest: `sha256:b3402288538400bae6760130c62892b8402ef4b041de8b8015647c7726002e5c`
- expires: `2026-12-15T15:09:24Z`

The artifact contains ten files: the A1000.3 bootstrap ROM, A1000.10 WCS payload, A1000.10 kickdisk, runtime result, diagnostic screenshot, FS-UAE log/version, ROM/config records, and wait-time record.

## Qualification result

**PASS.** A1000.10 is emulator-qualified for the private cooperative task-stack handoff milestone. The stock-A1000 WCS path now demonstrates a real A7 handoff to a prepared task stack and a controlled return to the original task stack, rather than only changing the current-task pointer.

## Scope and limitations

A1000.10 does **not** yet provide:

- complete D0-D7/A0-A6/SR task-context save and restore,
- interrupt-driven or scheduler-driven switching,
- public `Switch`, `Dispatch`, `Schedule`, `Reschedule`, or `FindTask` compatibility,
- public Exec negative-vector ABI for these private helpers,
- full task lifecycle semantics,
- full `exec.library` compatibility,
- real A1000 hardware qualification.

The next convergence step is to bring the shared `HandoffTaskStack` primitive into the ordinary retained 512 KiB ROM path before expanding toward fuller task-context switching.