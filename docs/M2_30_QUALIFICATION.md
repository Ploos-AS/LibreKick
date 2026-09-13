# LibreKick M2.30 Qualification

## Scope

M2.30 starts the Exec tasking area with a deliberately small `FindTask()` slice.
It qualifies the public Exec LVO `-294` for the current-task query only:

- `FindTask(NULL)` returns the bootstrap current-task pointer.
- A non-NULL task name is outside this slice and returns `NULL` cleanly.
- A named lookup must not disturb the current-task state; a later `FindTask(NULL)` must still return the same bootstrap task.

This milestone does **not** claim named task lookup, task scheduling, task lists, signals, or full Exec task compatibility.

## Qualified layout

- ExecBase: `$00003400`
- `FindTask` LVO: `-294` (`$000032DA`)
- FindTask ROM routine: `$00F83200`
- bootstrap current-task pointer cell: `$00004C10`
- bootstrap task sentinel: `$0000C000`

The vector is installed with the project `vector()` helper, which writes a `JMP absolute` stub into the negative Exec vector area using separate long/word writes.

## Runtime probe

The M2.30 runtime probe checks:

1. Install the `FindTask` vector at Exec LVO `-294`.
2. Establish the bootstrap current-task pointer.
3. Call `FindTask(NULL)` and require `$0000C000`.
4. Call `FindTask(name)` and require `NULL` because named lookup is not implemented in this slice.
5. Call `FindTask(NULL)` again and require `$0000C000` to prove the unsupported named lookup did not damage current-task state.
6. Paint green only after every assertion passes; failure goes to blue.

## Automated qualification evidence

Qualified commit:

`0d2c5226fbe38973c2aa8a6941079d5ee109b9f5`

GitHub Actions FS-UAE runtime qualification:

- workflow run: `34777220808` (`#109`)
- job: `103777431156`
- ROM size: 524288 bytes
- static checker: PASS
- ROM checksum: `0xffffffff`
- runtime semantic gate: PASS
- `green_ratio=0.8911`
- `blue_ratio=0.0000`
- `red_ratio=0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`

Runtime evidence artifact:

- artifact name: `fs-uae-runtime-qualification`
- artifact ID: `10324236811`
- artifact size: 9121 bytes
- ZIP SHA-256: `2f1d761ea08f7d6e147e49face7fea255a1514d0ff5b074c2b0766930e0356fc`
- artifact URL: `https://github.com/Ploos-AS/LibreKick/actions/runs/34777220808/artifacts/10324236811`

## Verdict

**M2.30 QUALIFIED** for the explicitly tested `FindTask(NULL)` current-task foundation.

This qualification is intentionally narrower than a full implementation of Exec task management.
