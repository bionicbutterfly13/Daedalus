#!/usr/bin/env python3
"""Create a hash-bound disposable launch copy after explicit GPU authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

CANONICAL_NOTEBOOK_SHA256 = (
    "e3e0cdcfa73732138dcfaf374f9946a7993f1647cb424f8acbed91cf3ae9b5fc"
)
AUTHORIZATION_FALSE = "INTEGRATION_SMOKE_AUTHORIZED = False"
AUTHORIZATION_TRUE = "INTEGRATION_SMOKE_AUTHORIZED = True"
TRANSFER_FALSE = "ARTIFACT_TRANSFER_AUTHORIZED = False"
TRANSFER_TRUE = "ARTIFACT_TRANSFER_AUTHORIZED = True"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_notebook_bytes(notebook: dict[str, Any]) -> bytes:
    return (
        json.dumps(notebook, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def create_authorized_copy(
    *,
    canonical_path: Path,
    output_path: Path,
    authorization_record_sha256: str,
) -> dict[str, Any]:
    """Create one disposable copy while preserving every other code-cell byte."""
    if re.fullmatch(r"[0-9a-f]{64}", authorization_record_sha256) is None:
        raise ValueError("authorization record SHA-256 must be 64 lowercase hex")
    canonical_payload = canonical_path.read_bytes()
    canonical_sha256 = _sha256(canonical_payload)
    if canonical_sha256 != CANONICAL_NOTEBOOK_SHA256:
        raise ValueError(
            f"canonical notebook SHA-256 is {canonical_sha256}, "
            f"expected {CANONICAL_NOTEBOOK_SHA256}"
        )
    notebook = json.loads(canonical_payload)
    code_cells = [
        cell for cell in notebook.get("cells", []) if cell.get("cell_type") == "code"
    ]
    source = "\n".join("".join(cell.get("source", [])) for cell in code_cells)
    if source.count(AUTHORIZATION_FALSE) != 1:
        raise ValueError(
            "canonical notebook must contain one false smoke authorization"
        )
    if AUTHORIZATION_TRUE in source:
        raise ValueError("canonical notebook already contains true smoke authorization")
    if source.count(TRANSFER_FALSE) != 1 or TRANSFER_TRUE in source:
        raise ValueError(
            "canonical notebook must contain one false transfer authorization"
        )
    if any(
        cell.get("execution_count") is not None or cell.get("outputs")
        for cell in code_cells
    ):
        raise ValueError("canonical notebook must be unexecuted")

    replaced = False
    for cell in code_cells:
        cell_source = "".join(cell.get("source", []))
        if AUTHORIZATION_FALSE not in cell_source:
            continue
        updated = cell_source.replace(AUTHORIZATION_FALSE, AUTHORIZATION_TRUE, 1)
        cell["source"] = updated.splitlines(keepends=True)
        replaced = True
    if not replaced:
        raise AssertionError("authorization replacement did not occur")

    notebook.setdefault("metadata", {})["stage2b_integration_smoke_launch"] = {
        "canonical_notebook_sha256": CANONICAL_NOTEBOOK_SHA256,
        "authorization_record_sha256": authorization_record_sha256,
        "artifact_transfer_authorized": False,
        "disposable_copy": True,
    }
    output_payload = _canonical_notebook_bytes(notebook)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open("xb") as handle:
            handle.write(output_payload)
    except FileExistsError:
        if output_path.read_bytes() != output_payload:
            raise FileExistsError(
                f"{output_path} exists with bytes from another authorization"
            ) from None
    if canonical_path.read_bytes() != canonical_payload:
        raise RuntimeError("canonical notebook changed while creating launch copy")
    return {
        "path": str(output_path),
        "size_bytes": len(output_payload),
        "sha256": _sha256(output_payload),
        "canonical_notebook_sha256": CANONICAL_NOTEBOOK_SHA256,
        "authorization_record_sha256": authorization_record_sha256,
        "artifact_transfer_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--authorization-record-sha256", required=True)
    args = parser.parse_args()
    result = create_authorized_copy(
        canonical_path=args.canonical,
        output_path=args.output,
        authorization_record_sha256=args.authorization_record_sha256,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
