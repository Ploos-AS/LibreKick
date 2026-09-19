# M2.49 design — private ready-list dispatch

## Goal

M2.49 is the next deliberately narrow Exec-runtime step after the qualified M2.48 deterministic A → B → A context switch.

M2.48 proved that LibreKick can save a task context, restore a prepared second task, execute it, and return to the first task. M2.49 adds **internal task selection from a minimal ready list** so the caller no longer supplies the next task pointer directly.

This remains a private LibreKick mechanism. It is not yet a claim of public Exec `Schedule`, `Switch`, `Dispatch`, `Reschedule`, `AddTask`, or full task-state compatibility.

## Retained baseline

M2.49 extends M2.48 and must preserve:

- 512 KiB deterministic ROM image.
- 68000 baseline.
- ExecBase at `$00003400`.
- `ThisTask` at ExecBase offset `$0114`.
- `tc_SPReg` at task offset `$0036`.
- saved/restored SR, D2-D7 and A2-A6.
- A500, A500+ and A600 retained model-specific builds.
- M2.48 qualification as a reproducible historical milestone.

The stock A1000 WCS line remains separate. M2.49 is first implemented and qualified on the retained 512 KiB profiles; an A1000 convergence milestone follows only after M2.49 is stable.

## New private runtime state

Introduce a deliberately small internal ready-list representation with two prepared task records for the qualification probe.

The first implementation should avoid claiming the public Exec List/Node ABI. A private ready-list head/tail or equivalent deterministic selector is sufficient.

Required semantics:

1. Task A is `ThisTask`.
2. Task B is placed on the private ready list with a prepared context frame.
3. A calls the private dispatch helper without passing B as the next-task argument.
4. The helper selects B from the ready list.
5. A's context and `tc_SPReg` are saved.
6. B becomes `ThisTask` and its context is restored.
7. B records execution evidence and places/selects A for return.
8. The same private dispatch path selects A.
9. A resumes after its original dispatch call.
10. A verifies task identity, evidence, restored registers/SR and expected ready-list state before reaching the green terminal gate.

## Qualification requirements

Static qualification must verify the retained M2.48 structure plus the M2.49 marker, private dispatch code, ready-list state and probe metadata.

Runtime qualification must prove the selection is list-driven rather than a disguised M2.48 direct handoff. The probe therefore must not pass the next task pointer to the dispatch helper.

A successful runtime must verify:

- A → selector → B → selector → A.
- `ThisTask` transitions A → B → A.
- B execution evidence.
- A resume evidence.
- SR preservation/restoration.
- D2-D7 preservation/restoration.
- A2-A6 preservation/restoration.
- task-stack transition through `tc_SPReg`.
- ready-list state consumed/updated as designed.
- terminal green diagnostic gate.

Qualification is required on A500, A500+ and A600 through the retained profile runtime matrix.

## Explicit non-goals

M2.49 does not claim:

- public Exec List/Node ABI compatibility;
- public task state values or flags;
- priority ordering;
- round-robin policy;
- wait lists;
- signals;
- preemption;
- interrupt-driven scheduling;
- quantum/time slicing;
- task creation/deletion;
- public `AddTask`, `RemTask`, `FindTask`, `Schedule`, `Switch`, `Dispatch`, or `Reschedule`;
- full `exec.library` compatibility.

Those surfaces should be introduced only with explicit ABI definitions and dedicated qualification.

## Exit criterion

M2.49 is complete when all three retained 68000 profiles build deterministically, pass static checks, and independently reach the green FS-UAE runtime gate using the private ready-list-driven dispatch path.
