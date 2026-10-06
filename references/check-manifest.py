#!/usr/bin/env python3
"""Check deterministic Swarm Batch Production manifest invariants.

The documented default is spec/manifest.json and uses only the standard library.
YAML is optional and requires PyYAML.
Use --require-final for the final completion gate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FINAL = {"final", "exemplar-final"}
NEEDS_REVIEWERS = {"peer_reviewing", "peer_ready", "revising", "revised", "vertically_checked", "final"}
NEEDS_COMPLETE_REVIEWS = {"peer_ready", "revising", "revised", "vertically_checked", "final"}
NEEDS_OUTPUT = {"draft_ready", *NEEDS_REVIEWERS, "exemplar-final"}
EXEMPLAR_ROLES = {"exemplar"}


def load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    elif path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError("YAML requires PyYAML; use the default spec/manifest.json for zero-dependency checks") from exc
        try:
            data = yaml.safe_load(text)
        except Exception as exc:
            raise RuntimeError(f"invalid YAML: {exc}") from exc
    else:
        raise RuntimeError(f"unsupported manifest format: {path.suffix}")
    if not isinstance(data, dict):
        raise RuntimeError("manifest root must be an object/mapping")
    return data


def manifest_path(root: Path, explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        return p if p.is_absolute() else root / p
    for rel in ("spec/manifest.json", "spec/manifest.yaml", "spec/manifest.yml"):
        p = root / rel
        if p.exists():
            return p
    raise RuntimeError("no manifest found under spec/ (json/yaml/yml)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--manifest")
    ap.add_argument("--require-final", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []

    try:
        data = load(manifest_path(root, args.manifest))
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR {exc}")
        return 1

    units = data.get("units")
    if not isinstance(units, list) or not units:
        print("ERROR manifest.units must be a non-empty list")
        return 1

    seen_ids: dict[str, int] = {}
    seen_outputs: dict[str, str] = {}
    seen_reviews: dict[str, str] = {}

    for i, u in enumerate(units):
        if not isinstance(u, dict):
            errors.append(f"units[{i}] must be an object")
            continue
        uid, output, author, status = (u.get(k) for k in ("unit_id", "output", "author_agent", "status"))
        label = uid if isinstance(uid, str) and uid else f"units[{i}]"

        for field, value in (("unit_id", uid), ("output", output), ("author_agent", author), ("status", status)):
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label}: missing/invalid {field}")

        if isinstance(uid, str):
            if uid in seen_ids:
                errors.append(f"duplicate unit_id {uid!r}")
            seen_ids[uid] = i
        if isinstance(output, str):
            if output in seen_outputs:
                errors.append(f"duplicate output path {output!r}: {seen_outputs[output]} and {label}")
            seen_outputs[output] = label
            if status in NEEDS_OUTPUT and not (root / output).is_file():
                errors.append(f"{label}: output file missing -> {output}")

        reviewers = u.get("peer_reviewers") or []
        reviews = u.get("peer_reviews") or []
        if not isinstance(reviewers, list) or not isinstance(reviews, list):
            errors.append(f"{label}: peer_reviewers and peer_reviews must be lists")
            continue

        if reviewers:
            valid_ids = all(isinstance(x, str) and x.strip() for x in reviewers)
            if not valid_ids or len(reviewers) != 2 or len(set(reviewers)) != 2:
                errors.append(f"{label}: peer_reviewers must be exactly 2 distinct agent IDs")
            if author in reviewers:
                errors.append(f"{label}: author cannot review own unit")

        for review in reviews:
            if not isinstance(review, str) or not review:
                errors.append(f"{label}: invalid peer review path")
                continue
            if review in seen_reviews:
                errors.append(f"review path reused by {seen_reviews[review]} and {label}: {review}")
            seen_reviews[review] = label
            if not (root / review).is_file():
                errors.append(f"{label}: review file missing -> {review}")

        exemplar = u.get("role") in EXEMPLAR_ROLES
        if status == "exemplar-final" and not exemplar:
            errors.append(f"{label}: status=exemplar-final requires role='exemplar'")
        if not exemplar and status in NEEDS_REVIEWERS:
            if len(reviewers) != 2:
                errors.append(f"{label}: status={status} requires 2 peer reviewers")
        if not exemplar and status in NEEDS_COMPLETE_REVIEWS:
            if len(reviews) != 2:
                errors.append(f"{label}: status={status} requires exactly 2 peer review files")
        if not exemplar and status == "peer_reviewing" and len(reviews) > 2:
            errors.append(f"{label}: status=peer_reviewing allows at most 2 peer review files")
        if args.require_final and status not in FINAL:
            errors.append(f"{label}: not final (status={status!r})")

    for e in errors:
        print(f"ERROR {e}")
    print(f"checked {len(units)} units; {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
