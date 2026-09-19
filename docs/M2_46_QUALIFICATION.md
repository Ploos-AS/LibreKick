# M2.46 Qualification

Status: **EMULATOR QUALIFIED / PASS**

M2.46 converges the shared private `HandoffTaskStack` runtime primitive into the retained 512 KiB LibreKick ROM, following the A1000.10 WCS qualification. This is a private cooperative task-stack handoff primitive and is not a public Exec scheduler or a complete task context switch.

## Qualified revision

- Qualified HEAD: `2e5f7bc52271b8be5b91831061d3b8d06a2fd3bf`
- Retained ROM: `build/librekick-m2_46.rom`
- Runtime profile: A500 / FS-UAE

## Shared primitive

`HandoffTaskStack` uses the shared Exec runtime state:

- `SysBase` at absolute address `$00000004`
- `ThisTask` at ExecBase offset `$0114`
- `tc_SPReg` at task offset `$0036`

68000 helper bytes:

```
20790000000422680114234f003622092240214001142e69003620014e75
```

Semantics of the private helper:

1. Load `SysBase`.
2. Load the current task from `ThisTask`.
3. Save the current A7 into that task's `tc_SPReg`.
4. Preserve the old task pointer as the return value.
5. Install the task supplied in D0 as `ThisTask`.
6. Load A7 from the replacement task's `tc_SPReg`.
7. Return the previous task pointer in D0.
8. `RTS` through the prepared replacement stack.

The M2.46 runtime probe performs a cooperative handoff and a return handoff, validating that task identity and stack state are restored before reaching the green diagnostic gate.

## GitHub Actions qualification

The M2.46 qualification set completed successfully on the qualified source. The exact profile-matrix run ID was not retained in the original qualification notes, so this document does not invent one.

Key runtime evidence:

- Workflow: `FS-UAE runtime qualification`
- Run: `35133689640`
- Run number: `345`
- Job: `104920630064`
- Result: `success`
- Profile runtime matrix: run number `156`, `success` (exact run ID was not retained in the qualification notes)
- Runtime artifact: `10463075585`
- Artifact size: `10529` bytes
- Artifact digest: `sha256:30426bbd4640423d73815193dd8f2797e44cfe7722ca4353a79d8fe69291563b`

The runtime qualification uses the established GitHub-hosted Ubuntu/FS-UAE software-rendered test path and requires the ROM to reach the green diagnostic gate.

## Scope

M2.46 qualifies cross-profile use of the shared private task-stack handoff primitive. It does **not** claim:

- public Exec `Switch`, `Dispatch`, `Schedule`, or `Reschedule` compatibility;
- public Exec negative-vector compatibility for this primitive;
- scheduler-driven task selection;
- preservation/restoration of the complete task CPU register set or SR as part of `HandoffTaskStack`;
- a complete Exec task switch;
- full `exec.library` compatibility;
- real Amiga hardware qualification.

The next scheduler-oriented work can build a defined saved CPU-context frame on top of the now-qualified task-pointer and task-stack primitives.
