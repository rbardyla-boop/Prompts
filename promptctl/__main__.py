from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .kernel import KernelError, compose_prompt, load_json, select_modules, validate_repository


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="promptctl")
    result.add_argument("--root", type=Path, default=Path.cwd())
    commands = result.add_subparsers(dest="command", required=True)

    commands.add_parser("validate", help="validate catalog, graph and invariants")

    compose = commands.add_parser("compose", help="select modules and compose a prompt")
    compose.add_argument("--task-type", required=True)
    compose.add_argument("--goal", required=True)
    compose.add_argument("--include", action="append", default=[])
    compose.add_argument("--allow-profile-specific", action="store_true")
    compose.add_argument("--output", type=Path)

    explain = commands.add_parser("explain", help="show deterministic module selection")
    explain.add_argument("--task-type", required=True)
    explain.add_argument("--include", action="append", default=[])
    explain.add_argument("--allow-profile-specific", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "validate":
            print(json.dumps(validate_repository(root), indent=2))
            return 0

        catalog = load_json(root / "modules/legacy-extracted/MODULE_CATALOG.json")
        graph = load_json(root / "RULE_GRAPH.json")
        selection = select_modules(
            catalog,
            graph,
            args.task_type,
            args.include,
            args.allow_profile_specific,
        )

        if args.command == "explain":
            print(json.dumps(selection, indent=2))
            return 0

        text = compose_prompt(args.goal, selection, catalog)
        if args.output:
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text)
        return 0
    except KernelError as exc:
        print(f"promptctl: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
