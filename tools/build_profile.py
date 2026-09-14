#!/usr/bin/env python3
"""Build and statically validate one retained LibreKick machine profile."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: build_profile.py PROFILE_ID")

    profile_id = sys.argv[1]
    profile_path = ROOT / "profiles" / profile_id / "profile.json"
    if not profile_path.is_file():
        raise SystemExit(f"unknown LibreKick profile: {profile_id}")

    profile = json.loads(profile_path.read_text())
    if profile.get("id") != profile_id:
        raise SystemExit(f"profile id mismatch in {profile_path}")

    generator = ROOT / profile["generator"]
    checker = ROOT / profile["checker"]
    artifact = ROOT / profile["artifact"]
    artifact.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run([sys.executable, str(generator), str(artifact)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(checker), str(artifact)], cwd=ROOT, check=True)

    expected_size = int(profile["rom_size"])
    actual_size = artifact.stat().st_size
    if actual_size != expected_size:
        raise SystemExit(
            f"profile {profile_id}: ROM size mismatch: expected {expected_size}, got {actual_size}"
        )

    print(
        f"LibreKick profile PASS: {profile_id} ({profile['model']}, {profile['cpu']}) -> "
        f"{artifact.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
