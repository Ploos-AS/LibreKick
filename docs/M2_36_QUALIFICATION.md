# LibreKick M2.36 Qualification

M2.36 qualifies the current-task stack-context handoff foundation.

## Scope

The slice follows `ExecBase->ThisTask` and reads the selected task's classic 68k `tc_SPReg` field at offset `+$36`. The value is copied to a dedicated next-SP shadow cell at `$4C18`.

Classic Task stack metadata used by the probe:

- `tc_SPReg` `+$36`
- `tc_SPLower` `+$3A`
- `tc_SPUpper` `+$3E`

The probe verifies that the handoff follows the live `tc_SPReg` value by capturing two different values from the already-selected task B. It also verifies that `FindTask(NULL)` remains consistent with `ExecBase->ThisTask`.

## Deliberate limitations

M2.36 is **not** a CPU context switch. It does not write A7, save or restore the general registers, restore SR/PC, transfer execution to another task, or implement public `Switch()`/`Dispatch()` semantics.

## Automated qualification

- FS-UAE runtime qualification run: `34795922577`
- Runtime job: `103828874314`
- Qualified HEAD: `66599221f8c1fc66476a4a53595c00bf72afbc38`
- ROM size: 524288 bytes
- ROM checksum: `0xffffffff`
- Runtime gate: PASS
- `green_ratio=0.8911`
- `blue_ratio=0.0000`
- `red_ratio=0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`
- evidence artifact: `10329304107`
- artifact size: 9120 bytes
- artifact SHA-256: `779f9807f0226db025b14ce9749593d8f1b6a1f6e0d0395d6c28aa4a244c9c5c`

The green runtime path proves the assertions encoded by the M2.36 probe and nothing beyond the scope above.
