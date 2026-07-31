#!/usr/bin/env python3
"""Build the deterministic code-only bundle for the Stage 2b Colab pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

BUNDLE_SCHEMA = "jspace-stage2b-pilot-code-bundle/v1"
SCRIPT_NAMES = (
    "stage2b_endpoint.py",
    "stage2b_manifest.py",
    "stage2b_preflight.py",
    "stage2b_statistics.py",
    "validate_observation.py",
)
STAGE2_DIGESTS_PATH = "tests/jspace/fixtures/stage2_manifest_digests.json"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _entry(name: str, payload: bytes) -> tuple[zipfile.ZipInfo, bytes]:
    info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    info.create_system = 3
    return info, payload


def build_bundle(*, repository_root: Path, output_path: Path) -> dict[str, object]:
    """Write a deterministic allowlisted bundle and return its content identity."""
    scripts_dir = (
        repository_root / "EvoScientist/skills/jspace-research-operations/scripts"
    )
    source_paths = {
        (f"EvoScientist/skills/jspace-research-operations/scripts/{name}"): scripts_dir
        / name
        for name in SCRIPT_NAMES
    }
    source_paths[STAGE2_DIGESTS_PATH] = repository_root / STAGE2_DIGESTS_PATH
    files: dict[str, bytes] = {}
    for archive_name, source_path in source_paths.items():
        if not source_path.is_file():
            raise FileNotFoundError(f"required pilot source is missing: {source_path}")
        files[archive_name] = source_path.read_bytes()

    manifest = {
        "schema": BUNDLE_SCHEMA,
        "files": [
            {
                "name": name,
                "size_bytes": len(files[name]),
                "sha256": _sha256(files[name]),
            }
            for name in source_paths
        ],
        "excludes": [
            "pilot prompts",
            "confirmatory prompts",
            "credentials",
            "model weights",
            "lens weights",
            "notebooks",
            "runtime artifacts",
            "scientific evidence artifacts",
        ],
    }
    manifest_payload = (
        json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            for name in source_paths:
                archive.writestr(*_entry(name, files[name]))
            archive.writestr(*_entry("bundle-manifest.json", manifest_payload))
        payload = temporary.read_bytes()
        if output_path.exists():
            if output_path.read_bytes() != payload:
                raise FileExistsError(
                    f"{output_path} exists with bytes from another source state"
                )
        else:
            temporary.replace(output_path)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "path": str(output_path),
        "size_bytes": len(payload),
        "sha256": _sha256(payload),
        "manifest": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_bundle(
        repository_root=args.repository_root,
        output_path=args.output,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
