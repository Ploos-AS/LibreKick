# M2.49 emulator qualification

Status: **PASS — emulator-qualified**

M2.49 extends the qualified M2.48 private two-task context switch with a private ready-state-driven dispatcher. The caller no longer supplies the next task pointer directly: the dispatcher selects it from internal ready state, saves the current context, publishes the current task for the return dispatch, restores the selected task, and completes the deterministic A → B → A round trip.

This remains an internal LibreKick runtime slice. It does not claim the public Exec scheduler ABI.

## Qualified source and runtime

- Workflow: `M2.49 runtime qualification`
- Run: `35464983571`
- Static job: `105955557328` — **PASS**
- FS-UAE job: `105955557487` — **PASS**
- ROM size: 524288 bytes
- Static checker: `M2.49 check PASS`

Runtime diagnostic:

- Green ratio: `0.8911`
- Blue ratio: `0.0000`
- Red ratio: `0.0000`
- Dominant RGB: `0,240,0`
- Runtime gate: **PASS — green diagnostic screen**

Retained evidence:

- Artifact: `m2-49-fs-uae-qualification`
- Artifact ID: `10590792845`

## Qualified semantics

The runtime probe establishes:

1. Task A is installed as `ThisTask`.
2. Task B is prepared with a private saved context and published in the internal ready state.
3. A invokes the private dispatcher without passing B as a next-task argument.
4. The dispatcher selects B from ready state, saves A through `tc_SPReg`, installs B as `ThisTask`, and restores B.
5. B records execution evidence and invokes the same dispatcher.
6. The ready state selects A.
7. A resumes and verifies task identity and B/A execution evidence before reaching the green gate.

The context mechanism retains the M2.48 preservation contract: SR, D2-D7, A2-A6 and task-stack state through `tc_SPReg`.

## Qualification boundary

M2.49 does **not** claim public Exec List/Node compatibility, task-state flags, priorities, round-robin policy, wait lists, signals, preemption, interrupt-driven scheduling, time slicing, task creation/removal, or public `AddTask`, `RemTask`, `FindTask`, `Schedule`, `Switch`, `Dispatch` or `Reschedule` compatibility.

This qualification is emulator evidence. Physical Amiga hardware qualification remains separate.
