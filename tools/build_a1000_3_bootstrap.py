#!/usr/bin/env python3
"""Build the LibreKick A1000.3 68000 bootstrap loader as a 64 KiB ROM."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

ROM_SIZE = 64 * 1024
SOURCE = Path("src/a1000/bootstrap_a1000_3.S")


def need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise SystemExit(
            f"missing {tool}; install GNU m68k binutils (Ubuntu: binutils-m68k-linux-gnu)"
        )
    return path


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "build/a1000/librekick-a1000.3-bootstrap.rom")
    out.parent.mkdir(parents=True, exist_ok=True)
    obj = out.with_suffix(".o")
    elf = out.with_suffix(".elf")

    assembler = need("m68k-linux-gnu-as")
    linker = need("m68k-linux-gnu-ld")
    objcopy = need("m68k-linux-gnu-objcopy")

    # The source deliberately uses traditional Motorola register spelling
    # (d0/a0/sp without '%' prefixes). GNU m68k as supports this explicitly.
    run([
        assembler,
        "-m68000",
        "--register-prefix-optional",
        "-o", str(obj),
        str(SOURCE),
    ])
    run([
        linker,
        "--build-id=none",
        "-Ttext=0x00f80000",
        "-e", "_start",
        "-o", str(elf),
        str(obj),
    ])
    run([objcopy, "-O", "binary", str(elf), str(out)])

    size = out.stat().st_size
    if size != ROM_SIZE:
        raise SystemExit(f"A1000.3 bootstrap size mismatch: expected {ROM_SIZE}, got {size}")

    print(f"A1000.3 bootstrap ROM built: {out} ({size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
