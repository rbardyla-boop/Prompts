from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .harness import (
    agent_dir,
    archive_manifest,
    initialize_project,
    load_state,
    load_taskpack,
    recovery_report,
    run_recovery_test,
    self_test,
    verify_trace,
)
from .kernel import (
    KernelError,
    TASK_TAGS,
    catalog_modules,
    compose_prompt,
    load_json,
    select_modules,
    validate_repository,
)


def add_selection_arguments(command: argparse.ArgumentParser) -> None:
    group = command.add_mutually_exclusive_group(required=True)
    group.add_argument("--task-type")
    group.add_argument("--task-pack")
    command.add_argument("--include", action="append", default=[])
    command.add_argument("--allow-profile-specific", action="store_true")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="promptctl")
    result.add_argument("--root", type=Path, default=Path.cwd())
    commands = result.add_subparsers(dest="command", required=True)

    commands.add_parser("inventory", help="list typed modules")
    commands.add_parser("validate", help="validate catalog, graph and invariants")

    compose = commands.add_parser("compose", help="select modules and compose a prompt")
    add_selection_arguments(compose)
    compose.add_argument("--goal", required=True)
    compose.add_argument("--output", type=Path)

    explain = commands.add_parser("explain", help="show deterministic module selection")
    add_selection_arguments(explain)

    init = commands.add_parser("init", help="initialize an external-state harness")
    init.add_argument("--workspace", type=Path, required=True)
    init.add_argument("--task-pack", required=True)
    init.add_argument("--goal", required=True)

    status = commands.add_parser("status", help="show canonical harness state")
    status.add_argument("--workspace", type=Path, required=True)

    run = commands.add_parser("run", help="emit the next bounded worker cycle")
    run.add_argument("--workspace", type=Path, required=True)

    verify = commands.add_parser("verify", help="validate repository and optional harness")
    verify.add_argument("--workspace", type=Path)

    traces = commands.add_parser("verify-traces", help="verify trace hash chain")
    traces.add_argument("--workspace", type=Path, required=True)

    recovery = commands.add_parser("recovery-test", help="resume from external state in a fresh process")
    recovery.add_argument("--workspace", type=Path, required=True)

    archive = commands.add_parser("archive", help="create a hashed agent-state manifest")
    archive.add_argument("--workspace", type=Path, required=True)

    commands.add_parser("self-test", help="run the false-completion terminal harness test")

    child = commands.add_parser("_recover-child")
    child.add_argument("--workspace", type=Path, required=True)
    return result


def resolve_selection(args: argparse.Namespace, root: Path) -> tuple[dict, dict, dict]:
    catalog = load_json(root / "modules/legacy-extracted/MODULE_CATALOG.json")
    graph = load_json(root / "RULE_GRAPH.json")
    explicit = list(args.include)
    allow_profile = args.allow_profile_specific
    if args.task_pack:
        pack = load_taskpack(root, args.task_pack)
        task_type = pack["task_type"]
        explicit = list(dict.fromkeys([*pack["module_ids"], *explicit]))
        allow_profile = allow_profile or bool(pack.get("allow_profile_specific", False))
        extra_tags = pack.get("extra_task_tags", [])
    else:
        task_type = args.task_type
        extra_tags = []

    original_tags = TASK_TAGS[task_type]
    TASK_TAGS[task_type] = set(original_tags) | set(extra_tags)
    try:
        selection = select_modules(catalog, graph, task_type, explicit, allow_profile)
    finally:
        TASK_TAGS[task_type] = original_tags
    if args.task_pack:
        selection["taskpack_id"] = args.task_pack
    return catalog, graph, selection


def bounded_cycle_prompt(workspace: Path) -> str:
    contract = load_json(agent_dir(workspace) / "contract.json")
    state = load_state(workspace)
    return "\n".join(
        [
            "# BOUNDED WORK CYCLE",
            "",
            f"Task: {state['task_id']}",
            f"Objective: {contract['objective']}",
            f"State: {state['status']}",
            f"Phase: {state['current_phase']}",
            f"Next action: {state['next_action']}",
            "",
            "Execute exactly one independently verifiable state transition.",
            "Use only allowed actions from agent/permissions.json.",
            "Save evidence and update canonical state before stopping.",
            "Do not claim completion; submit evidence to the harness.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "inventory":
            catalog = load_json(root / "modules/legacy-extracted/MODULE_CATALOG.json")
            rows = [
                {
                    "module_id": module["module_id"],
                    "classification": module["classification"],
                    "status": module["status"],
                    "default_include": module["default_include"],
                }
                for module in catalog_modules(catalog)
            ]
            print(json.dumps({"module_count": len(rows), "modules": rows}, indent=2))
            return 0

        if args.command == "validate":
            print(json.dumps(validate_repository(root), indent=2))
            return 0

        if args.command in {"compose", "explain"}:
            catalog, _, selection = resolve_selection(args, root)
            if args.command == "explain":
                print(json.dumps(selection, indent=2))
                return 0
            text = compose_prompt(args.goal, selection, catalog)
            if args.output:
                args.output.write_text(text, encoding="utf-8")
            else:
                print(text)
            return 0

        if args.command == "init":
            report = initialize_project(root, args.workspace.resolve(), args.task_pack, args.goal)
            print(json.dumps(report, indent=2))
            return 0

        if args.command == "status":
            print(json.dumps(load_state(args.workspace.resolve()), indent=2))
            return 0

        if args.command == "run":
            print(bounded_cycle_prompt(args.workspace.resolve()))
            return 0

        if args.command == "verify":
            report = {"repository": validate_repository(root)}
            if args.workspace:
                report["trace"] = verify_trace(args.workspace.resolve())
                report["state"] = load_state(args.workspace.resolve())
            print(json.dumps(report, indent=2))
            return 0

        if args.command == "verify-traces":
            print(json.dumps(verify_trace(args.workspace.resolve()), indent=2))
            return 0

        if args.command == "recovery-test":
            print(json.dumps(run_recovery_test(root, args.workspace.resolve()), indent=2))
            return 0

        if args.command == "archive":
            print(json.dumps(archive_manifest(args.workspace.resolve()), indent=2))
            return 0

        if args.command == "self-test":
            print(json.dumps(self_test(root), indent=2))
            return 0

        if args.command == "_recover-child":
            print(json.dumps(recovery_report(args.workspace.resolve())))
            return 0

        raise KernelError(f"unknown command: {args.command}")
    except KernelError as exc:
        print(f"promptctl: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
