# LibreKick M2.35 Qualification

## Scope

M2.35 qualifies the first internal scheduler transition from `ExecBase->TaskReady` to the current/running task state.

The slice deliberately does **not** perform a CPU context switch. It does not restore registers, change A7, change PC, or expose the internal helper as `Schedule()`, `Reschedule()`, or `Switch()`.

## Qualified behavior

The runtime probe starts from the M2.34 ready list, where task B (priority 7) precedes task A (priority 2). The M2.35 dispatcher:

- removes the head with the already-qualified `RemHead()` path,
- stores the selected task in classic `ExecBase->ThisTask` at offset `$114`,
- synchronizes the LibreKick current-task compatibility cell used by `FindTask(NULL)`,
- marks the selected task `TS_RUN`,
- leaves the remaining ready-list topology correct,
- verifies that `FindTask(NULL)` resolves the selected task.

## Runtime qualification

- Repository: `Ploos-AS/LibreKick`
- Qualified HEAD: `2d5d22854a3947bd22f894e7fc3732acbba49966`
- FS-UAE workflow run: `34793194608` (#136)
- Job: `103821189192`
- Result: PASS
- Static qualification run: `34793194582` (#262), PASS
- Diagnostic gate: green
- Runtime artifact: `10328743837`
- Artifact size: 9121 bytes
- Artifact SHA-256: `462caae8e8d998d8a01254cfc9742a8526c39af3b95ec7df6e74150215a02418`

## Compatibility boundary

M2.35 proves scheduler **selection/state plumbing only**. It is not evidence of full Exec task switching, preemption, register preservation, stack switching, blocking `Wait()`, interrupt-driven scheduling, or compatibility with the public scheduler entry points.

Those require subsequent context-management milestones.
