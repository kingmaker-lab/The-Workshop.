#!/usr/bin/env python3
"""Validate the Science registry without executing research projects or network calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "science" / "catalog.json"
MATURITY = {"prototype", "experimental", "published_demo"}
REQUIRED = {
    "id", "name", "area", "maturity", "source_path",
    "documentation_path", "tests_path", "validation_command",
    "ci_workflow", "limitations", "next_gate",
}


def safe_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (not path.is_absolute() and ".." not in path.parts
            and "." not in path.parts and value == str(path))


def validate(data: object, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["catalog: expected an object"]
    if data.get("schema_version") != 1:
        errors.append("catalog: unsupported schema_version")
    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        return errors + ["projects: expected a non-empty array"]
    seen: set[str] = set()
    for idx, project in enumerate(projects):
        label = f"projects[{idx}]"
        if not isinstance(project, dict):
            errors.append(f"{label}: expected object")
            continue
        missing = REQUIRED.difference(project)
        if missing:
            errors.append(f"{label}: missing {', '.join(sorted(missing))}")
            continue
        project_id = project["id"]
        if not isinstance(project_id, str) or not project_id.startswith("SCI-"):
            errors.append(f"{label}: invalid id")
        elif project_id in seen:
            errors.append(f"{label}: duplicate id {project_id}")
        else:
            seen.add(project_id)
        if project["maturity"] not in MATURITY:
            errors.append(f"{label}: invalid maturity")
        for field in ("name", "area", "limitations", "next_gate"):
            if not isinstance(project[field], str) or not project[field].strip():
                errors.append(f"{label}: {field} must be non-empty")
        for field in ("source_path", "documentation_path", "tests_path", "ci_workflow"):
            value = project[field]
            if value is None and field in ("tests_path", "ci_workflow"):
                continue
            if not safe_relative_path(value):
                errors.append(f"{label}: unsafe or invalid {field}")
            elif not (root / value).exists():
                errors.append(f"{label}: missing {field}: {value}")
        command = project["validation_command"]
        if command is not None and (not isinstance(command, str) or not command.strip()):
            errors.append(f"{label}: invalid validation_command")
        if command is not None and project["tests_path"] is None:
            errors.append(f"{label}: validation command without tests_path")
    external = data.get("external_tracks", [])
    if not isinstance(external, list):
        errors.append("external_tracks: expected array")
    else:
        for index, track in enumerate(external):
            if not isinstance(track, dict):
                errors.append(f"external_tracks[{index}]: expected object")
                continue
            for field in ("id", "name", "repository", "tracking_branch", "assessment", "next_gate"):
                if not isinstance(track.get(field), str) or not track[field].strip():
                    errors.append(f"external_tracks[{index}]: {field} missing")
    return errors


def render_markdown(data: dict) -> str:
    lines = ["# Research inventory", "", f"Snapshot: {data['snapshot_date']}", "",
             "| ID | Research | Maturity | Validation in catalog |",
             "| --- | --- | --- | --- |"]
    for project in data["projects"]:
        check = "command documented" if project["validation_command"] else "pending"
        lines.append(f"| {project['id']} | {project['name']} | {project['maturity']} | {check} |")
    if data.get("external_tracks"):
        lines += ["", "External research (not validated by this repository):"]
        lines.extend(f"- {track['name']}: {track['repository']} ({track['tracking_branch']})"
                     for track in data["external_tracks"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    args = parser.parse_args()
    try:
        data = json.loads(args.catalog.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Science catalog unavailable or invalid: {exc}")
        return 2
    errors = validate(data)
    if args.format == "json":
        print(json.dumps({"ok": not errors, "project_count": len(data.get("projects", [])),
                          "errors": errors}, ensure_ascii=False, indent=2))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}")
    elif args.format == "markdown":
        print(render_markdown(data), end="")
    else:
        print(f"Science registry: {len(data['projects'])} tracked, "
              f"{len(data.get('external_tracks', []))} external; references OK.")
        print("Note: this validates metadata and paths, not the scientific claims or all test suites.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
