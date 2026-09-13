# LibreKick M2.31 qualification

M2.31 qualifies the first current-task signal-state primitive: Exec `SetSignal()` at LVO `-306`.

## Scope

The slice keeps a 32-bit signal-state value in the bootstrap task signal cell at `$00004C14` and qualifies the public `SetSignal(newSignals, signalSet)` ABI for that current task. The implementation returns the previous signal state and replaces only bits selected by `signalSet`.

The runtime probe covers:

- selective replacement of low signal bits;
- selective clearing;
- selective setting;
- a zero mask behaving as a read-only operation;
- preservation of unselected signal bits.

This milestone does **not** claim a complete Exec `Task` structure, scheduler, task switching, `Wait()`, inter-task `Signal()`, signal allocation, or full AmigaOS Exec tasking compatibility.

## Qualification evidence

Qualification commit: `e9e4db74b025879d65870d5e7da0a98e903a54c0`

GitHub Actions FS-UAE runtime qualification:

- workflow run: `34779802054` (`#114`)
- job: `103784601487`
- ROM size: 524288 bytes
- static checker: PASS
- ROM checksum: `0xffffffff`
- runtime color gate: PASS
- green ratio: `0.8911`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`
- artifact: `10324590802`
- artifact size: 9121 bytes
- artifact ZIP SHA-256: `6db4971f6565078a6b2894e2af286a6d02619b3a3c17239847371807b378e0de`
- artifact URL: `https://github.com/Ploos-AS/LibreKick/actions/runs/34779802054/artifacts/10324590802`

The green diagnostic screen is the runtime semantic PASS only for the assertions explicitly gated by the M2.31 probe.