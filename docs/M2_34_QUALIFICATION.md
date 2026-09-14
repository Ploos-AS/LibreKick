# LibreKick M2.34 Qualification

M2.34 qualifies a narrow `AddTask()` ready-list registration slice for the classic 68k Exec ABI.

## Scope

Qualified behavior:

- `AddTask()` is installed at Exec LVO `-282`.
- ABI-visible inputs are `A1=task`, `A2=initialPC`, `A3=finalPC`.
- A prepared task node is inserted into `ExecBase->TaskReady` through the already-qualified priority-sorted `Enqueue()` path.
- `tc_State` is set to `TS_READY` (`3`).
- The task pointer is returned in `D0`.
- The probe adds priority-2 and priority-7 tasks and verifies that the priority-7 task becomes the ready-list head.

Classic 68k ExecBase layout used by the corrected qualification:

- `ThisTask = ExecBase + $114`
- `TaskReady = ExecBase + $196`
- `TaskWait = ExecBase + $1A4`
- with LibreKick `ExecBase=$3400`, `TaskReady=$3596`.

Not qualified in M2.34:

- initial CPU context construction,
- execution of `initialPC` or `finalPC`,
- task launch,
- context switching,
- rescheduling/preemption,
- removal/termination,
- full scheduler semantics.

## Corrected runtime qualification

The first M2.34 implementation used an incorrect provisional TaskReady offset. The generator and checker were corrected to the classic 68k `ExecBase+$196` layout and the corrected ROM was re-qualified.

GitHub Actions evidence:

- HEAD: `edcac1376e611713378f26382c8331c794008764`
- FS-UAE workflow: `FS-UAE runtime qualification` #131
- run: `34782927475`
- job: `103793095582`
- result: **PASS**
- static checker: `M2.34 check PASS`
- ROM size: `524288` bytes
- ROM checksum: `0xffffffff`
- runtime image: `960x540`
- green ratio: `0.8911`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`
- runtime gate: `PASS: green diagnostic screen`
- artifact ID: `10325424244`
- artifact size: `9121` bytes
- artifact ZIP SHA-256: `d80eef12866bb72e99cd9f7243f432529b717dc7a2dc8d3ef616d83eac6d57a6`

Static qualification for the corrected HEAD also completed successfully:

- workflow: `M1 static qualification` #257
- run: `34782927455`
- job: `103793095583`
- result: **PASS**

## Verdict

**M2.34 QUALIFIED AND DOCUMENTED** for the ready-list registration behavior above. This is deliberately not a claim of full Amiga Exec `AddTask()` or scheduler compatibility.
