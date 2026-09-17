# M2.48 — private two-task context switch

M2.48 extends the emulator-qualified M2.47 private CPU context frame into a controlled two-task round trip.

## Goal

Demonstrate that LibreKick can preserve one task context, activate a second prepared task context, update `ExecBase->ThisTask`, and later return to the first task with its CPU context intact.

The saved/restored context remains the M2.47 set:

- SR
- D2-D7
- A2-A6
- task stack pointer through `tc_SPReg`

## Runtime scenario

The M2.48 probe uses two synthetic task structures, Task A and Task B, with separate stack areas and distinguishable register sentinels.

1. `ThisTask` starts at Task A.
2. Task A enters the private context-switch helper.
3. Task A's current context is saved on its own task stack and `tc_SPReg` is updated.
4. `ThisTask` changes to Task B.
5. Task B's prepared context is restored and execution resumes at the Task B continuation.
6. Task B records its identity/register evidence and switches back to Task A.
7. Task A resumes after its original switch call.
8. The probe verifies both task identities, both stack transitions and the restored Task A SR/D2-D7/A2-A6 values before reaching the green PASS gate.

## Scope boundary

M2.48 is an internal deterministic qualification primitive. It does **not** claim a public Exec scheduler, ready/wait queues, priorities, quantum/preemption, interrupts driving rescheduling, or compatible public `Switch`, `Dispatch`, `Schedule` or `Reschedule` entry points.

Those interfaces remain later milestones after the private task-context mechanics are qualified independently.

## Retained profiles

The first M2.48 implementation targets the retained A500, A500 Plus and A600 ROM profiles. They remain at M2.47 `emulator-qualified` until M2.48 static and FS-UAE runtime qualification pass.
