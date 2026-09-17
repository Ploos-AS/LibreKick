# LibreKick A1000.12 design

Status: **DESIGN / qualification pending**

A1000.12 is the stock-Amiga-1000/WCS counterpart to shared M2.48. It extends the emulator-qualified A1000.11 private CPU-context frame into a deterministic two-task round trip while preserving the A1000 boot architecture: 64 KiB bootstrap ROM, Kickstart disk container, and a 256 KiB payload loaded into WCS at `$00fc0000`.

## Scope

A1000.12 adds a private context-switch primitive and a qualification probe with two synthetic tasks, A and B.

The saved/restored context remains:

- SR
- D2-D7
- A2-A6
- task stack pointer through `tc_SPReg`

Expected round trip:

1. Task A is installed as `ThisTask` with known register sentinels.
2. Task B receives a prepared context frame and private stack.
3. A calls the private switch helper targeting B.
4. The helper saves A's context and `tc_SPReg`, changes `ThisTask` to B, restores B's prepared context, and returns into B's entry point.
5. B verifies its identity/register context, records evidence, and switches back to A.
6. A resumes at its original call site and verifies `ThisTask`, its restored registers/SR, B evidence, and the expected task-stack transitions.
7. PASS is the existing green runtime gate; any mismatch enters the red gate.

## WCS constraints

- WCS payload: exactly 256 KiB.
- Load base: `$00fc0000`.
- Entry: `$00fc0008`.
- ExecBase remains `$00003400` and SysBase remains at address 4.
- Revision becomes `40.12`.
- Existing A1000.11 private helpers remain retained unless an address collision requires an explicitly documented relocation.
- A1000.12 artifacts must be retained as `librekick-a1000.12-wcs.bin` and `librekick-a1000.12-kickdisk.adf`.

## Qualification requirements

Static qualification must verify container metadata/digest, exact WCS size and vectors, A1000.12 marker/ident, helper placement, both prepared task contexts, register/SR evidence checks, `ThisTask` transitions, `tc_SPReg` transitions, and deterministic artifact generation.

Runtime qualification must use the dedicated stock-A1000 FS-UAE bootstrap path, not the generic 512 KiB ROM workflow. The runtime evidence must demonstrate the A1000 bootstrap loading the A1000.12 WCS payload and the payload reaching the green gate.

## Explicit non-goals

A1000.12 does not claim a complete Exec scheduler. It does not add ready/wait queues, priorities, preemption, interrupt-driven rescheduling, or public `Switch`, `Dispatch`, `Schedule`, or `Reschedule` compatibility.
