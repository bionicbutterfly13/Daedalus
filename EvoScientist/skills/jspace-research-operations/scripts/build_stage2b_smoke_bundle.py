#!/usr/bin/env python3
"""Build the deterministic code-only bundle for the Stage 2b Colab smoke."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

BUNDLE_SCHEMA = "jspace-stage2b-integration-smoke-bundle/v1"
BUNDLE_FILES = (
    "stage2b_endpoint.py",
    "stage2b_preflight.py",
    "stage2b_integration_smoke.py",
)
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _entry(name: str, payload: bytes) -> tuple[zipfile.ZipInfo, bytes]:
    info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    info.create_system = 3
    return info, payload


def build_bundle(*, scripts_dir: Path, output_path: Path) -> dict[str, object]:
    """Write a deterministic bundle and return its content identity."""
    files: dict[str, bytes] = {}
    for name in BUNDLE_FILES:
        path = scripts_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"required smoke source is missing: {path}")
        files[name] = path.read_bytes()

    manifest = {
        "schema": BUNDLE_SCHEMA,
        "files": [
            {
                "name": name,
                "size_bytes": len(files[name]),
                "sha256": _sha256(files[name]),
            }
            for name in BUNDLE_FILES
        ],
        "excludes": [
            "pilot prompts",
            "confirmatory prompts",
            "credentials",
            "model weights",
            "lens weights",
            "runtime artifacts",
        ],
    }
    manifest_payload = (
        json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w") as archive:
        for name in BUNDLE_FILES:
            archive.writestr(*_entry(name, files[name]))
        archive.writestr(*_entry("bundle-manifest.json", manifest_payload))
    payload = temporary.read_bytes()
    if output_path.exists():
        if output_path.read_bytes() != payload:
            temporary.unlink()
            raise FileExistsError(
                f"{output_path} exists with bytes from another source state"
            )
        temporary.unlink()
    else:
        temporary.replace(output_path)
    return {
        "path": str(output_path),
        "size_bytes": len(payload),
        "sha256": _sha256(payload),
        "manifest": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scripts-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_bundle(scripts_dir=args.scripts_dir, output_path=args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
