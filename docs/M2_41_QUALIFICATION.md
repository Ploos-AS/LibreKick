# LibreKick M2.41 qualification

M2.41 qualifies a **private task-stack PC resume handoff primitive**. It is deliberately narrower than an Exec scheduler or public `Switch()` / `Dispatch()` implementation.

## Qualified behavior

The M2.41 helper is entered by `JSR` on the caller stack. It records the caller A7 and JSR return PC, loads the current task from `ExecBase->ThisTask`, switches A7 to `ThisTask->tc_SPReg`, pushes a private LibreKick resume-stub address on that task stack, and executes `RTS`.

That `RTS` therefore obtains its next PC from the task stack. The private resume stub records arrival, restores the original caller A7, and returns through the original caller return PC. The runtime probe repeats this with two independent task-stack pointers (`$D7F0` and `$D6C0`).

This qualifies a real controlled PC transfer through task-owned stack storage. It does **not** yet qualify a complete Amiga Exec task context switch: there is no scheduler decision, no task-to-task register/SR context transfer, and no public `Switch`, `Dispatch`, `Schedule`, or `Reschedule` vector claim.

## Runtime qualification

- Repository: `Ploos-AS/LibreKick`
- Qualified HEAD: `9dbc1e59b3ac862f47478250ded142b8cb0c1d03`
- FS-UAE runtime workflow: **#166**
- Run ID: `34801627191`
- Result: **PASS / success**
- Static qualification: **#292**, run `34801627181`, **PASS / success**
- Runtime artifact: `fs-uae-runtime-qualification`
- Artifact ID: `10331028521`
- Artifact size: `9120` bytes
- Artifact ZIP SHA-256: `1b270202c02c896281656eb614f7ad96525dc4faa2ebfb89bab0c7fdc200830c`

The runtime workflow completed the FS-UAE execution and evidence-upload steps successfully.

## Scope boundary

M2.41 proves only the private PC-resume primitive described above. The resume PC is a LibreKick-internal ROM stub, not a general saved task PC, and the milestone must not be cited as proof of full Exec task switching or multitasking compatibility.
