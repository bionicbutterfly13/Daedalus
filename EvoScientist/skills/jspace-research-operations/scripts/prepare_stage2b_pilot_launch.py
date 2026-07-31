#!/usr/bin/env python3
"""Prepare an exclusive, byte-verified Stage 2b pilot upload package.

This tool does not authorize a pilot. It consumes an already approved,
content-addressed authorization record and proves that the exact notebook and
code-bundle bytes named by that record are the only executable upload sources.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import stage2b_preflight as preflight

SCHEMA = "stage2b-pilot-launch-package/v1"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _verify_canonical_notebook(payload: bytes) -> dict[str, Any]:
    try:
        notebook = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"canonical notebook is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(notebook, dict) or not isinstance(notebook.get("cells"), list):
        raise ValueError("canonical notebook has no cell list")
    sources: list[str] = []
    for index, cell in enumerate(notebook["cells"]):
        if not isinstance(cell, dict):
            raise ValueError(f"canonical notebook cell {index} is not an object")
        if cell.get("cell_type") != "code":
            continue
        if cell.get("execution_count") is not None or cell.get("outputs") not in (
            None,
            [],
        ):
            raise ValueError("canonical notebook must be unexecuted and output-free")
        source = cell.get("source")
        if not isinstance(source, list) or not all(
            isinstance(line, str) for line in source
        ):
            raise ValueError(f"canonical notebook code cell {index} has invalid source")
        sources.append("".join(source))
    joined = "\n".join(sources)
    for required in (
        "PILOT_AUTHORIZED = False",
        "PILOT_PROTOCOL_RATIFIED = False",
        "THRESHOLDS_RATIFIED = False",
        "ARTIFACT_TRANSFER_AUTHORIZED = False",
    ):
        if required not in joined:
            raise ValueError(
                f"canonical notebook is missing refusal source: {required}"
            )
    for forbidden in (
        "PILOT_AUTHORIZED = True",
        "PILOT_PROTOCOL_RATIFIED = True",
        "THRESHOLDS_RATIFIED = True",
        "ARTIFACT_TRANSFER_AUTHORIZED = True",
    ):
        if forbidden in joined:
            raise ValueError(
                f"canonical notebook enables forbidden source: {forbidden}"
            )
    return notebook


def prepare_launch(
    *,
    notebook_path: Path,
    code_bundle_path: Path,
    pilot_view_path: Path,
    authorization_path: Path,
    approved_authorization_sha256: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Verify exact sources and copy only the authorized upload members."""
    if output_dir.exists():
        raise FileExistsError(
            f"exclusive launch directory already exists: {output_dir}"
        )
    notebook_payload = notebook_path.read_bytes()
    bundle_payload = code_bundle_path.read_bytes()
    pilot_view_payload = pilot_view_path.read_bytes()
    _verify_canonical_notebook(notebook_payload)
    notebook_sha256 = _sha256(notebook_payload)
    bundle_sha256 = _sha256(bundle_payload)
    pilot_view_sha256 = _sha256(pilot_view_payload)

    authorization = preflight.load_pilot_authorization_record(
        authorization_path,
        approved_record_sha256=approved_authorization_sha256,
        expected_pilot_view_sha256=pilot_view_sha256,
        observed_code_bundle_sha256=bundle_sha256,
    )
    source = authorization["source"]
    if source["notebook_sha256"] != notebook_sha256:
        raise ValueError(
            "authorization record notebook identity does not match exact canonical bytes"
        )
    if source["code_bundle_sha256"] != bundle_sha256:
        raise ValueError(
            "authorization record code-bundle identity does not match exact bundle bytes"
        )

    members = [
        (notebook_path.name, notebook_payload),
        (code_bundle_path.name, bundle_payload),
        (pilot_view_path.name, pilot_view_payload),
        (authorization_path.name, authorization_path.read_bytes()),
    ]
    if len({name for name, _ in members}) != len(members):
        raise ValueError("pilot launch members require unique filenames")
    manifest = {
        "schema": SCHEMA,
        "authorization_record_sha256": approved_authorization_sha256,
        "source": {
            "notebook_sha256": notebook_sha256,
            "code_bundle_sha256": bundle_sha256,
            "pilot_view_sha256": pilot_view_sha256,
        },
        "boundaries": {
            "run_mode": "pilot",
            "confirmation_access_authorized": False,
            "artifact_transfer_authorized": False,
        },
        "members": [
            {"name": name, "size_bytes": len(payload), "sha256": _sha256(payload)}
            for name, payload in members
        ],
    }
    manifest_payload = _canonical_json(manifest)

    output_dir.mkdir(parents=True, exist_ok=False)
    for name, payload in members:
        target = output_dir / name
        target.write_bytes(payload)
        if target.read_bytes() != payload:
            raise RuntimeError(f"launch member readback mismatch: {name}")
    manifest_path = output_dir / "stage2b-pilot-launch-manifest.json"
    manifest_path.write_bytes(manifest_payload)
    if manifest_path.read_bytes() != manifest_payload:
        raise RuntimeError("launch manifest readback mismatch")

    return {
        "path": str(output_dir),
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha256(manifest_payload),
        "source": manifest["source"],
        "authorization_record_sha256": approved_authorization_sha256,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--notebook", type=Path, required=True)
    parser.add_argument("--code-bundle", type=Path, required=True)
    parser.add_argument("--pilot-view", type=Path, required=True)
    parser.add_argument("--authorization-record", type=Path, required=True)
    parser.add_argument("--approved-authorization-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = prepare_launch(
        notebook_path=args.notebook,
        code_bundle_path=args.code_bundle,
        pilot_view_path=args.pilot_view,
        authorization_path=args.authorization_record,
        approved_authorization_sha256=args.approved_authorization_sha256,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
