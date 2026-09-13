# LibreKick M2.32 qualification

## Scope

M2.32 qualifies a minimal Exec-compatible `Signal()` ABI surface for delivery to LibreKick's single bootstrap/current task.

Qualified public ABI:

- `Signal()` at Exec LVO `-324`
- input `A1 = task`
- input `D0 = signalSet`
- delivery ORs the requested signal bits into the current task's bootstrap signal-state cell

This milestone intentionally has only one task. The `A1` task argument is ABI-visible, but general task selection, scheduler interaction, blocked-task wakeup, and inter-task signalling are **not** claimed or qualified by M2.32.

## Runtime probe

The probe resolves the current bootstrap task using the already-qualified `FindTask(NULL)` surface and then calls `Signal()` with several masks. It verifies cumulative signal-state delivery for:

- `0x00000005`
- `0x0000000A`
- `0x80000000`
- `0x00000000`

Expected state transitions are checked before the diagnostic screen can become green.

## GitHub Actions evidence

- qualification commit: `333e00017844aa12153db2baf18d04576b463881`
- workflow: `FS-UAE runtime qualification`
- run: `34780144490` (#119)
- job: `103785545186`
- result: **PASS**
- ROM size: `524288` bytes
- ROM checksum: `0xffffffff`
- image: `960x540`
- green ratio: `0.8911`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`
- artifact: `fs-uae-runtime-qualification`
- artifact ID: `10324451767`
- artifact size: `9121` bytes
- artifact ZIP SHA-256: `94d4b16b2707726fbb12fbacb1fb3f4021e4fc74f24d06998b3dd5504beeb8e1`
- artifact URL: `https://github.com/Ploos-AS/LibreKick/actions/runs/34780144490/artifacts/10324451767`

The FS-UAE color gate reached the green diagnostic state, so all assertions on the M2.32 green path passed at runtime.

## Verdict

**M2.32 QUALIFIED AND DOCUMENTED** for the single-current-task `Signal()` delivery surface described above.
