# LibreKick M2.44 Qualification

Status: **EMULATOR QUALIFIED / PASS**

M2.44 converges the shared internal Exec task-state primitives into the retained 512 KiB ROM line. It preserves the M2.43 prepared-task activation path and shared `GetSysBase`, and adds runtime-qualified shared `GetCurrentTask` and `SetCurrentTask` consumption.

## Qualified revision

- qualification head: `6f8ba832f64d2b24def580ede59cc4527c2d34b7`
- milestone marker: `LIBREKICK-M2.44\0SHARED-EXEC-TASK-RUNTIME\0`
- identity: `exec.library\0LibreKick M2.44 shared Exec task runtime 40.44\0`
- ROM size: 512 KiB

## Runtime layout

The retained M2.43 helper/runtime layout remains intact and M2.44 adds dedicated task-state blocks:

- prepared-task activation: ROM offset `0x5e00`
- prepared-task restore: ROM offset `0x5f00`
- prepared-task target: ROM offset `0x6000`
- shared `GetSysBase`: ROM offset `0x6100`, absolute `$00f86100`
- shared `GetCurrentTask`: ROM offset `0x6200`, absolute `$00f86200`
- shared `SetCurrentTask`: ROM offset `0x6300`, absolute `$00f86300`
- M2.44 task-runtime probe: ROM offset `0x6400..0x6500`, absolute `$00f86400..$00f86500`

Exact shared primitive encodings validated by `tools/check_m2_44.py`:

- `GetSysBase`: `2039000000044e75`
- `GetCurrentTask`: `207900000004202801144e75`
- `SetCurrentTask`: `207900000004214001144e75`

`ExecBase->ThisTask` remains at offset `0x114`.

## Runtime test

The M2.44 runtime probe executes after the successful M2.43 prepared-task/GetSysBase path. It:

1. calls shared `GetCurrentTask` and verifies the real retained current task (`TASK_A`, `$0000c100`),
2. loads the controlled value `$0000c844` and calls shared `SetCurrentTask`,
3. calls shared `GetCurrentTask` and verifies the controlled value,
4. restores `TASK_A` through shared `SetCurrentTask`,
5. verifies the restored value both through `GetCurrentTask` and directly at `ExecBase->ThisTask`,
6. reaches the green diagnostic gate only after the complete reversible round trip succeeds.

The temporary task-state mutation is therefore restored before the milestone enters its final idle state.

## GitHub Actions evidence

### FS-UAE runtime qualification

- workflow: `FS-UAE runtime qualification`
- run: `35067089012` (#302)
- job: `104699712884` (`fs-uae-runtime`)
- head: `6f8ba832f64d2b24def580ede59cc4527c2d34b7`
- runner label: `ubuntu-24.04`
- conclusion: **SUCCESS**
- `Run current LibreKick ROM in FS-UAE`: **SUCCESS**
- `Upload FS-UAE runtime evidence`: **SUCCESS**

Retained runtime evidence:

- artifact: `fs-uae-runtime-qualification`
- artifact ID: `10435185113`
- artifact size: 10,534 bytes
- artifact digest: `sha256:0a91e3db0ba89a82a33426b30a849f698724870a529f923eba9c16a272058695`

### Cross-profile regression

The `LibreKick profile runtime matrix` also passed on the same head:

- run: `35067089082` (#113)
- conclusion: **SUCCESS**

The other four workflows triggered by the same M2.44 qualification head also completed successfully, giving six successful workflows and zero failed workflows for the revision.

## Scope

M2.44 qualifies **shared internal task-state primitive convergence** across the retained ordinary-ROM path. It does not claim:

- a complete Exec scheduler,
- public `exec.library` negative vectors for these helpers,
- public `FindTask` compatibility,
- full `Schedule`/`Reschedule`/`Switch`/`Dispatch` semantics,
- full Exec compatibility,
- real-hardware qualification.

Those remain later milestones. M2.44 establishes that the same private shared task-state runtime primitives already exercised by the A1000 WCS line can also be consumed safely by the ordinary 512 KiB ROM line, including a reversible current-task update and restoration.
