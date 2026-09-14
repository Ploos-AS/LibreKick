# LibreKick machine profiles

LibreKick maintains explicit ROM variants for individual Amiga model families. A newer machine target must not replace or obsolete a previously supported target.

## Principles

1. **One shared codebase, multiple retained ROM products.** Common Exec/library/device code is shared. Hardware differences are selected through explicit machine profiles rather than hidden runtime assumptions.
2. **Stable profile identifiers.** Once a profile is released, its identifier remains stable so old builds can be reproduced and compared.
3. **Deterministic per-profile builds.** Every supported profile gets a dedicated build target producing a predictably named ROM image.
4. **Dedicated qualification.** A profile is not marked supported merely because the generic ROM boots elsewhere. It needs its own emulator configuration and, eventually, real-hardware qualification.
5. **Retain historical variants.** Release artifacts for earlier machines remain available when support for later machines is added.
6. **Compatibility first.** CPU-specific optimizations are optional profile properties. They must not silently raise the minimum CPU requirement of another profile.

## Initial profile registry

| Profile ID | Model family | Baseline CPU | Status |
| --- | --- | --- | --- |
| `a1000` | Amiga 1000 | 68000 | planned |
| `a500` | Amiga 500 | 68000 | emulator-qualified |
| `a500plus` | Amiga 500 Plus | 68000 | emulator-qualified |
| `a600` | Amiga 600 | 68000 | buildable; runtime qualification pending |
| `a1500` | Amiga 1500 | 68000 | planned |
| `a2000` | Amiga 2000 | 68000 | planned |
| `a2500-20` | Amiga 2500/20 | 68020-class | planned |
| `a2500-30` | Amiga 2500/30 | 68030-class | planned |
| `a3000` | Amiga 3000 | 68030 | planned |
| `a3000t` | Amiga 3000T | 68030 | planned |
| `a1200` | Amiga 1200 | 68020 | planned |
| `a4000` | Amiga 4000 | 68040-class profile | planned |
| `a4000t` | Amiga 4000T | 68040-class profile | planned |
| `cdtv` | Commodore CDTV | 68000 | planned |
| `cd32` | Amiga CD32 | 68020 | planned |

The CPU column describes the intended machine baseline, not a promise that all future optimized builds use only that exact CPU. Optional 68030/040/060 optimized derivatives may be added later while preserving the baseline profile.

## Artifact naming

Released ROMs should use a model-explicit naming scheme such as:

`librekick-<version>-<profile>.rom`

Examples:

- `librekick-0.1.0-a500.rom`
- `librekick-0.1.0-a1200.rom`
- `librekick-0.1.0-a3000.rom`
- `librekick-0.1.0-cd32.rom`

If a profile later needs multiple ROM layouts, append an explicit layout or optimization suffix rather than replacing the original artifact.

## Repository layout target

As the machine matrix becomes active, converge toward:

- `profiles/<profile>/` — machine-specific constants/configuration
- `configs/fs-uae/<profile>-*.fs-uae` — runtime qualification configs
- `build/<profile>/` — generated local images
- release artifacts named by profile
- qualification documents that state the exact machine profile tested

The current milestone-specific generators can remain while M2 task/runtime work is in progress. Profile refactoring should be incremental so the already-qualified A500 path stays reproducible.

## Qualification states

Use these states per profile:

- **planned** — profile registered, no compatibility claim.
- **buildable** — deterministic ROM is produced and passes static validation.
- **emulator-qualified** — dedicated emulator runtime qualification passes.
- **hardware-qualified** — qualification passes on representative real hardware.

A profile can move forward independently of the others. Failures on one model must not cause a previously qualified model artifact to disappear.

## Release policy

A LibreKick release should publish every model profile that is qualified for that release. Unsupported/planned profiles are documented but not presented as compatible ROMs. The release manifest should record for each artifact:

- profile ID
- ROM size
- checksum/hash
- CPU baseline
- qualification level
- emulator/hardware evidence

This gives LibreKick a preserved model matrix rather than a single moving ROM target.
