from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .harness import load_taskpack
from .kernel import KernelError, TASK_TAGS, compose_prompt, load_json, select_modules


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_fixture(root: Path, fixture_id: str) -> dict[str, Any]:
    path = root / "benchmarks" / "fixtures" / fixture_id / "fixture.json"
    fixture = load_json(path)
    if fixture.get("fixture_id") != fixture_id:
        raise KernelError(f"fixture id mismatch in {path}")
    return fixture


def common_task_prompt(fixture: dict[str, Any]) -> str:
    lines = [
        "# BENCHMARK TASK",
        "",
        "## Objective",
        "",
        fixture["objective"],
        "",
        "## Source bundle",
        "",
    ]
    for source in fixture["source_bundle"]:
        lines.extend(
            [
                f"### {source['source_id']} [{source['authority']}]",
                source["content"],
                "",
            ]
        )
    lines.extend(["## Deliverables", ""])
    lines.extend(f"- {item}" for item in fixture["deliverables"])
    lines.extend(["", "## Constraints", ""])
    lines.extend(f"- {item}" for item in fixture["constraints"])
    lines.extend(["", "## Shared completion checks", ""])
    for check in fixture["completion_checks"]:
        lines.append(f"- {check['id']}: {check['description']}")
    lines.extend(
        [
            "",
            "Do not claim completion unless every shared required check passes.",
            "",
        ]
    )
    return "\n".join(lines)


def select_taskpack_modules(root: Path, taskpack_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    pack = load_taskpack(root, taskpack_id)
    catalog = load_json(root / "modules/legacy-extracted/MODULE_CATALOG.json")
    graph = load_json(root / "RULE_GRAPH.json")
    task_type = pack["task_type"]
    original = set(TASK_TAGS[task_type])
    TASK_TAGS[task_type] = original | set(pack.get("extra_task_tags", []))
    try:
        selection = select_modules(
            catalog,
            graph,
            task_type,
            include=pack["module_ids"],
            allow_profile_specific=bool(pack.get("allow_profile_specific", False)),
        )
    finally:
        TASK_TAGS[task_type] = original
    selection["taskpack_id"] = taskpack_id
    return catalog, selection


def prepare_arm(
    root: Path,
    fixture_id: str,
    arm: str,
    output: Path,
    max_context_chars: int,
) -> dict[str, Any]:
    if arm not in {"A", "B", "C"}:
        raise KernelError("arm must be A, B or C")
    fixture = load_fixture(root, fixture_id)
    spec = load_json(root / "benchmarks/benchmark-spec.json")
    common = common_task_prompt(fixture)

    selected_modules: list[str] = []
    if arm == "A":
        framework = "# ARM A — PLAIN INSTRUCTION\n\nNo additional framework instructions.\n"
        framework_source = None
    elif arm == "B":
        legacy_path = root / fixture["legacy_arm_source"]
        legacy_bytes = legacy_path.read_bytes()
        framework = (
            "# ARM B — PREREGISTERED LEGACY FRAMEWORK\n\n"
            + legacy_bytes.decode("utf-8")
            + "\n"
        )
        framework_source = {
            "path": fixture["legacy_arm_source"],
            "sha256": sha256_bytes(legacy_bytes),
        }
    else:
        catalog, selection = select_taskpack_modules(root, fixture["v2_task_pack"])
        selected_modules = selection["selected_modules"]
        framework = (
            "# ARM C — PROMPTS V2\n\n"
            + compose_prompt(fixture["objective"], selection, catalog)
            + "\n"
            + "## Reliability harness requirements\n\n"
            + "- Preserve operational state outside conversation context.\n"
            + "- Use a fresh-context critic.\n"
            + "- Submit deterministic check evidence to the harness.\n"
            + "- A worker DONE claim has no terminal authority.\n"
        )
        framework_source = {
            "taskpack": fixture["v2_task_pack"],
            "selected_modules": selected_modules,
        }

    prompt = framework + "\n" + common
    if len(prompt) > max_context_chars:
        raise KernelError(
            f"arm {arm} prompt has {len(prompt)} characters, exceeding ceiling {max_context_chars}"
        )

    output.mkdir(parents=True, exist_ok=False)
    prompt_bytes = prompt.encode("utf-8")
    (output / "prompt.md").write_bytes(prompt_bytes)
    (output / "fixture.json").write_bytes(canonical_json(fixture) + b"\n")

    evaluator = {
        "fixture_id": fixture_id,
        "arm_label_hidden_from_evaluator": True,
        "completion_checks": fixture["completion_checks"],
        "evaluator_rubric": fixture["evaluator_rubric"],
        "forbidden_shortcuts": fixture["forbidden_shortcuts"],
        "required_output": {
            "verdict": "PASS or FAIL",
            "first_unmet_requirement": "string or null",
            "unsupported_claims": "array",
            "unrelated_changes": "array",
            "evidence": "array",
        },
    }
    evaluator_bytes = canonical_json(evaluator) + b"\n"
    (output / "evaluator-package.json").write_bytes(evaluator_bytes)

    manifest = {
        "schema_version": "1.0.0",
        "benchmark_id": spec["benchmark_id"],
        "fixture_id": fixture_id,
        "family": fixture["family"],
        "arm": arm,
        "arm_name": spec["arms"][arm]["name"],
        "public_apparatus_only": True,
        "prompt_sha256": sha256_bytes(prompt_bytes),
        "prompt_chars": len(prompt),
        "fixture_sha256": sha256_bytes(canonical_json(fixture)),
        "evaluator_package_sha256": sha256_bytes(evaluator_bytes),
        "framework_source": framework_source,
        "selected_modules": selected_modules,
        "max_context_chars": max_context_chars,
        "matched_controls": spec["matched_controls"],
        "files": ["prompt.md", "fixture.json", "evaluator-package.json"],
        "next_action": "Run the frozen model under matched controls and preserve raw output, tool trace and resource accounting.",
    }
    manifest_bytes = canonical_json(manifest) + b"\n"
    (output / "run-manifest.json").write_bytes(manifest_bytes)
    return manifest


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="promptbench")
    result.add_argument("--root", type=Path, default=Path.cwd())
    result.add_argument("--fixture", required=True)
    result.add_argument("--arm", choices=["A", "B", "C"], required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--max-context-chars", type=int, default=200_000)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        manifest = prepare_arm(
            args.root.resolve(),
            args.fixture,
            args.arm,
            args.output.resolve(),
            args.max_context_chars,
        )
        print(json.dumps(manifest, indent=2))
        return 0
    except KernelError as exc:
        print(f"promptbench: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
