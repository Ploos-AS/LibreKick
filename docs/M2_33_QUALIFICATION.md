# LibreKick M2.33 qualification

## Scope

M2.33 qualifies the immediate-ready path of Exec `Wait()` for LibreKick's single bootstrap/current task.

Qualified behavior:

- public Exec ABI surface at LVO `-318`
- `D0 = signalSet`
- return `D0 = pending & signalSet`
- clear only the returned bits from the current task's pending signal state
- preserve pending bits that were not selected by the wait mask
- integration with the already-qualified `Signal()` path

Not qualified by M2.33:

- blocking when no requested signal is pending
- task state transition to `TS_WAIT`
- scheduler/context switching
- TaskWait/TaskReady queue movement
- wakeup of a blocked task by `Signal()`
- multi-task scheduling semantics

When no requested signal is pending, the provisional M2.33 implementation returns zero. This is intentionally narrower than full Exec `Wait()` semantics and is a stepping stone toward scheduler-backed blocking.

## Runtime probe

The probe starts with no pending signals, resolves the current bootstrap task with `FindTask(NULL)`, and uses the already-qualified `Signal()` implementation to seed signal state.

The exercised transitions are:

1. `Signal(0x00000015)` -> pending `0x00000015`
2. `Wait(0x00000005)` -> returns `0x00000005`, pending `0x00000010`
3. `Signal(0x8000000A)` -> pending `0x8000001A`
4. `Wait(0x0000000A)` -> returns `0x0000000A`, pending `0x80000010`
5. `Wait(0x80000010)` -> returns `0x80000010`, pending `0x00000000`

The successful path ends on LibreKick's green runtime diagnostic screen; failures branch to blue.

## Automated qualification evidence

- repository: `Ploos-AS/LibreKick`
- qualification commit: `6d9fac2887a3aac98149f854d25172b340e1e4cf`
- workflow: `FS-UAE runtime qualification`
- workflow run: `34780582821` (#124)
- job: `103786744710`
- result: **PASS**
- ROM size: `524288` bytes
- static checker: **PASS**
- ROM checksum: `0xffffffff`
- screenshot: `960x540`
- green ratio: `0.8911`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`
- artifact: `10325530480`
- artifact size: `9120` bytes
- artifact ZIP SHA-256: `9b07d740ebec0cb2d67f521f2c13eb84eb7db9ab3257bd837dd91b33677307ef`
- artifact URL: `https://github.com/Ploos-AS/LibreKick/actions/runs/34780582821/artifacts/10325530480`

## Verdict

**M2.33 QUALIFIED.**

This verdict applies only to the immediate-ready signal-consumption semantics described above. Full blocking `Wait()` remains future work and requires task/scheduler infrastructure.
