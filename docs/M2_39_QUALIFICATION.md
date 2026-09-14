# LibreKick M2.39 qualification

M2.39 qualifies an expanded preserved-register context frame on the selected task stack.

## Scope

The private context helper follows `ExecBase->ThisTask`, loads the classic `Task.tc_SPReg` field at `+$36`, temporarily hands A7 to that task stack, saves `D2-D7` and `A2-A6`, deliberately clobbers the same register set, restores it in reverse order, restores the caller A7, and returns normally.

The frame contains 11 longwords (44 bytes). The runtime probe verifies every restored value and verifies both ends of the physical frame on the task stack.

This milestone is intentionally **not** a full Exec task switch. It does not preserve `D0-D1`, `A0-A1`, SR, or PC, does not transfer execution to another task, and does not expose `Switch()`, `Dispatch()`, `Schedule()`, or `Reschedule()` ABI compatibility.

## Qualification evidence

- Qualified HEAD: `ee5bf77cf907faf648dd89f6bff4962c89ffd0b9`
- FS-UAE runtime qualification: run `34798488532`, job `103836167475`, PASS
- Static qualification: run `34798488550`, PASS
- ROM size: 524288 bytes
- ROM checksum: `0xffffffff`
- Runtime diagnostic: `green_ratio=0.8911`, `blue_ratio=0.0000`, `red_ratio=0.0000`
- Dominant RGB: `0,240,0`, ratio `0.8901`
- Runtime artifact: `10330577662`, 9121 bytes
- Artifact ZIP SHA-256: `bdc2abc9471b10551d8d2fa6068f8f4f5c024f6193063b53843a0b0839e214e3`

## Verdict

**PASS** for the bounded M2.39 preserved-register frame semantics described above.
