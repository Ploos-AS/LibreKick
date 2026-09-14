# LibreKick A1000 boot strategy

## Why A1000 is not just another 512 KiB ROM profile

The stock Amiga 1000 is architecturally different from later ROM-based Amigas. It starts from a small bootstrap ROM and loads Kickstart from disk into a 256 KiB writable control store (WCS), which is then write-protected and executed. A normal 512 KiB Kickstart image is therefore not a faithful stock-A1000 boot product.

The first LibreKick A1000 profile experiment deliberately tried the shared 512 KiB M2.43 ROM under FS-UAE's `A1000` model. Static generation and the M2.43 checker passed, but the dedicated runtime job did not create an FS-UAE window and timed out. Evidence: profile runtime matrix run `34831299390`, job `103935019498`, artifact `10342561675`, artifact SHA-256 `17db7acdece0d7ecb4cbd799ecaf60b38c4f159aa20f9e3432211d64a2bbeab6`.

That failed experiment is retained as evidence that the stock A1000 target needs its own boot architecture. It must not be made green by forcing A500-like ROM mapping.

## Target products

The retained `a1000` profile will target an unmodified stock-style A1000 boot path and eventually produce separate artifacts:

1. `librekick-<version>-a1000-bootstrap.rom`
   - clean-room A1000 bootstrap ROM
   - intended size: 64 KiB container/image unless later hardware qualification proves another exact layout is required
   - responsible only for machine bring-up, disk loading, WCS population/lock, diagnostics, and transfer to the WCS payload

2. `librekick-<version>-a1000-kickdisk.adf`
   - bootable Kickstart disk image
   - contains the A1000 WCS payload
   - WCS payload budget: 256 KiB

3. Optional later extension media/modules
   - functionality that cannot fit in the 256 KiB WCS core may be loaded after the core is running
   - this is the likely route to a broader V40-compatible environment while preserving stock A1000 hardware constraints

## Compatibility contract

The `a1000` profile means **stock A1000 WCS boot architecture**, not a ROM-adapter machine.

A future 512 KiB ROM-adapter target, if useful, must use a separate profile identifier such as `a1000-romadapter`. It must never replace the stock `a1000` profile.

The first A1000 milestones are intentionally narrower than the shared M2.43 ROM:

- A1000.0: deterministic clean-room bootstrap ROM skeleton and checker
- A1000.1: bootstrap executes under FS-UAE A1000 and shows a diagnostic marker
- A1000.2: deterministic Kickstart disk image with a minimal WCS payload
- A1000.3: bootstrap loads the payload into WCS and transfers control
- A1000.4: WCS payload reaches LibreKick diagnostic PASS
- A1000.5: begin converging the 256 KiB core with shared Exec/runtime code without exceeding the WCS budget
- Later: disk-loaded extension modules for functionality that cannot reside in WCS

## Qualification policy

`a1000` remains `planned` until the dedicated bootstrap + WCS path exists. The shared 512 KiB ROM checker passing is not sufficient evidence for this profile.

Qualification levels for A1000 require:

- **buildable**: bootstrap ROM and Kickstart disk are generated deterministically and pass A1000-specific static validation
- **emulator-qualified**: FS-UAE A1000 boots the LibreKick bootstrap, loads the LibreKick WCS payload, and reaches the runtime PASS gate
- **hardware-qualified**: the same artifacts pass on representative unmodified A1000 hardware

The generic A500/A500+/A600 profile matrix remains regression coverage for the shared 512 KiB ROM line while A1000 develops on its separate boot path.
