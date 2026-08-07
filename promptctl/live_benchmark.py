from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import statistics
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from .benchmark import canonical_json, prepare_arm


class LiveBenchmarkError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    value = json.loads(stripped)
    if not isinstance(value, dict):
        raise LiveBenchmarkError("evaluator response was not a JSON object")
    return value


def _event_type(event: dict[str, Any]) -> str:
    value = event.get("type") or event.get("event") or event.get("eventType")
    return value if isinstance(value, str) else ""


def _event_data(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("data")
    return value if isinstance(value, dict) else event


def _first_int(mapping: dict[str, Any], names: tuple[str, ...]) -> int | None:
    for name in names:
        value = mapping.get(name)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
    return None


def parse_copilot_jsonl(stdout: str) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    for number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LiveBenchmarkError(f"Copilot JSONL line {number} was invalid JSON") from exc
        if not isinstance(event, dict):
            raise LiveBenchmarkError(f"Copilot JSONL line {number} was not an object")
        events.append(event)

    if not events:
        raise LiveBenchmarkError("Copilot emitted no JSONL events")

    final_messages: list[str] = []
    deltas: list[str] = []
    usage_events: list[dict[str, Any]] = []
    tool_events: list[str] = []
    sanitized_events: list[dict[str, Any]] = []

    for event in events:
        kind = _event_type(event)
        data = _event_data(event)
        if kind.startswith("assistant.reasoning"):
            continue
        sanitized_events.append(event)
        if kind == "assistant.message":
            content = data.get("content") or data.get("message")
            if isinstance(content, str) and content.strip():
                final_messages.append(content)
        elif kind == "assistant.message_delta":
            delta = data.get("deltaContent") or data.get("delta_content")
            if isinstance(delta, str):
                deltas.append(delta)
        elif kind == "assistant.usage":
            usage_events.append(data)
        elif kind.startswith("tool."):
            tool_events.append(kind)

    content = final_messages[-1] if final_messages else "".join(deltas)
    if not content.strip():
        raise LiveBenchmarkError("Copilot emitted no final assistant content")

    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0
    usage_seen = False
    for usage in usage_events:
        input_value = _first_int(
            usage,
            ("inputTokens", "input_tokens", "promptTokens", "prompt_tokens"),
        )
        output_value = _first_int(
            usage,
            ("outputTokens", "output_tokens", "completionTokens", "completion_tokens"),
        )
        cache_value = _first_int(
            usage,
            ("cacheReadTokens", "cache_read_tokens", "cachedInputTokens", "cached_input_tokens"),
        )
        if input_value is not None:
            input_tokens += input_value
            usage_seen = True
        if output_value is not None:
            output_tokens += output_value
            usage_seen = True
        if cache_value is not None:
            cache_read_tokens += cache_value

    if not usage_seen:
        for event in events:
            data = _event_data(event)
            input_value = _first_int(data, ("inputTokens", "input_tokens"))
            output_value = _first_int(data, ("outputTokens", "output_tokens"))
            if input_value is not None or output_value is not None:
                input_tokens += input_value or 0
                output_tokens += output_value or 0
                usage_seen = True

    return {
        "content": content,
        "input_tokens": input_tokens if usage_seen else None,
        "output_tokens": output_tokens if usage_seen else None,
        "cache_read_tokens": cache_read_tokens if usage_seen else None,
        "tool_event_count": len(tool_events),
        "tool_events": tool_events,
        "events": sanitized_events,
    }


def call_copilot(
    copilot_binary: str,
    model: str,
    prompt: str,
    *,
    max_ai_credits: int,
    timeout_seconds: int,
    retries: int,
    call_id: str,
) -> dict[str, Any]:
    excluded_tools = ",".join(
        [
            "bash",
            "powershell",
            "list_bash",
            "list_powershell",
            "read_bash",
            "read_powershell",
            "stop_bash",
            "stop_powershell",
            "write_bash",
            "write_powershell",
            "apply_patch",
            "create",
            "edit",
            "view",
            "list_agents",
            "read_agent",
            "task",
            "write_agent",
            "ask_user",
            "glob",
            "grep",
            "rg",
            "skill",
            "web_fetch",
        ]
    )
    command = [
        copilot_binary,
        "--prompt",
        prompt,
        "--model",
        model,
        "--context",
        "default",
        "--reasoning-effort",
        "low",
        "--max-ai-credits",
        str(max_ai_credits),
        "--output-format",
        "json",
        "--excluded-tools",
        excluded_tools,
        "--disable-builtin-mcps",
        "--no-ask-user",
        "--no-custom-instructions",
        "--no-auto-update",
        "--no-remote",
        "--no-remote-export",
        "--no-experimental",
        "--no-color",
    ]

    failures: list[dict[str, Any]] = []
    for attempt in range(1, retries + 2):
        with tempfile.TemporaryDirectory(prefix=f"prompts-v2-copilot-{call_id}-") as temp:
            temp_path = Path(temp)
            workdir = temp_path / "workspace"
            home = temp_path / "home"
            workdir.mkdir()
            home.mkdir()
            env = os.environ.copy()
            env["COPILOT_HOME"] = str(home)
            env["COPILOT_AUTO_UPDATE"] = "false"
            started = time.monotonic()
            try:
                process = subprocess.run(
                    command,
                    cwd=workdir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                failures.append(
                    {
                        "attempt": attempt,
                        "kind": "timeout",
                        "timeout_seconds": timeout_seconds,
                        "stderr": (exc.stderr or "")[-2000:] if isinstance(exc.stderr, str) else "",
                    }
                )
                if attempt <= retries:
                    continue
                raise LiveBenchmarkError(f"Copilot timed out after {attempt} attempt(s)") from exc

            elapsed = time.monotonic() - started
            if process.returncode != 0:
                failures.append(
                    {
                        "attempt": attempt,
                        "kind": "nonzero_exit",
                        "returncode": process.returncode,
                        "stderr": process.stderr[-4000:],
                        "stdout_tail": process.stdout[-4000:],
                    }
                )
                if attempt <= retries:
                    continue
                raise LiveBenchmarkError(
                    f"Copilot exited {process.returncode}: {process.stderr[-1000:]}"
                )

            parsed = parse_copilot_jsonl(process.stdout)
            parsed.update(
                {
                    "model_requested": model,
                    "latency_seconds": round(elapsed, 6),
                    "attempts": attempt,
                    "prior_failures": failures,
                    "stderr": process.stderr,
                }
            )
            if parsed["tool_event_count"]:
                raise LiveBenchmarkError(
                    f"Copilot used {parsed['tool_event_count']} tool event(s) in tool-free benchmark call"
                )
            if parsed["input_tokens"] is None or parsed["output_tokens"] is None:
                raise LiveBenchmarkError("Copilot response did not expose token usage")
            return parsed

    raise LiveBenchmarkError("Copilot call exhausted retries")


def evaluator_prompt(evaluator_package: dict[str, Any], candidate_output: str) -> str:
    return (
        "You are an independent benchmark evaluator. Evaluate only the candidate output against the "
        "provided frozen rubric. The candidate identity and benchmark arm are intentionally hidden. "
        "Do not infer or reward a framework. Return exactly one JSON object with keys verdict, "
        "first_unmet_requirement, unsupported_claims, unrelated_changes, evidence. verdict must be "
        "PASS or FAIL. unsupported_claims, unrelated_changes and evidence must be arrays.\n\n"
        "FROZEN EVALUATOR PACKAGE:\n"
        + json.dumps(evaluator_package, indent=2, ensure_ascii=False)
        + "\n\nCANDIDATE OUTPUT:\n"
        + candidate_output
    )


def bootstrap_mean_ci(values: list[float], seed: int, draws: int = 10_000) -> list[float] | None:
    if not values:
        return None
    rng = random.Random(seed)
    means = []
    for _ in range(draws):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(statistics.mean(sample))
    means.sort()
    lower = means[int(draws * 0.025)]
    upper = means[min(draws - 1, int(draws * 0.975))]
    return [round(lower, 6), round(upper, 6)]


def summarize_results(rows: list[dict[str, Any]], seed: int) -> dict[str, Any]:
    by_arm: dict[str, list[dict[str, Any]]] = {arm: [] for arm in "ABC"}
    for row in rows:
        by_arm[row["arm"]].append(row)

    arms: dict[str, Any] = {}
    for arm, arm_rows in by_arm.items():
        passes = sum(row["verdict"] == "PASS" for row in arm_rows)
        prompt_tokens = [row["prompt_tokens"] for row in arm_rows]
        completion_tokens = [row["completion_tokens"] for row in arm_rows]
        latencies = [row["generation_latency_seconds"] for row in arm_rows]
        arms[arm] = {
            "runs": len(arm_rows),
            "passes": passes,
            "pass_rate": passes / len(arm_rows) if arm_rows else None,
            "mean_prompt_tokens": round(statistics.mean(prompt_tokens), 3) if prompt_tokens else None,
            "mean_completion_tokens": round(statistics.mean(completion_tokens), 3) if completion_tokens else None,
            "mean_generation_latency_seconds": round(statistics.mean(latencies), 6) if latencies else None,
            "unsupported_claim_count": sum(len(row["unsupported_claims"]) for row in arm_rows),
        }

    paired: dict[str, Any] = {}
    indexed = {(row["repetition"], row["arm"]): row for row in rows}
    for other in ("B", "A"):
        diffs: list[float] = []
        for repetition in sorted({row["repetition"] for row in rows}):
            c = indexed[(repetition, "C")]["verdict"] == "PASS"
            baseline = indexed[(repetition, other)]["verdict"] == "PASS"
            diffs.append(float(c) - float(baseline))
        paired[f"C_minus_{other}"] = {
            "paired_pass_differences": diffs,
            "mean_difference": round(statistics.mean(diffs), 6),
            "bootstrap_95_ci": bootstrap_mean_ci(diffs, seed + ord(other)),
        }

    c_vs_b = paired["C_minus_B"]
    development_verdict = "NO_DEVELOPMENT_WIN"
    ci = c_vs_b["bootstrap_95_ci"]
    if ci and ci[0] > 0:
        development_verdict = "DEVELOPMENT_WIN_C_OVER_B"

    return {
        "arms": arms,
        "paired_comparisons": paired,
        "development_verdict": development_verdict,
        "final_validation_eligible": False,
        "reason_final_validation_ineligible": (
            "This fixture is public development apparatus and not independently held final evidence."
        ),
    }


def run_fixture(
    root: Path,
    fixture_id: str,
    output: Path,
    *,
    copilot_binary: str,
    generator_model: str,
    evaluator_model: str,
    repetitions: int,
    randomization_seed: int,
    max_context_chars: int,
    generation_max_ai_credits: int,
    evaluator_max_ai_credits: int,
    timeout_seconds: int,
    retries: int,
) -> dict[str, Any]:
    if repetitions < 1:
        raise LiveBenchmarkError("repetitions must be positive")
    if shutil.which(copilot_binary) is None:
        raise LiveBenchmarkError(f"Copilot CLI not found: {copilot_binary}")
    output.mkdir(parents=True, exist_ok=False)

    manifests: dict[str, dict[str, Any]] = {}
    packages = output / "packages"
    for arm in "ABC":
        manifests[arm] = prepare_arm(root, fixture_id, arm, packages / arm, max_context_chars)

    if len({manifests[arm]["fixture_sha256"] for arm in "ABC"}) != 1:
        raise LiveBenchmarkError("fixture hash mismatch across arms")
    if len({manifests[arm]["evaluator_package_sha256"] for arm in "ABC"}) != 1:
        raise LiveBenchmarkError("evaluator hash mismatch across arms")

    evaluator_package = json.loads(
        (packages / "A" / "evaluator-package.json").read_text(encoding="utf-8")
    )
    rng = random.Random(randomization_seed)
    orders: list[list[str]] = []
    candidate_map: dict[str, dict[str, Any]] = {}
    for repetition in range(1, repetitions + 1):
        order = list("ABC")
        rng.shuffle(order)
        orders.append(order)
        for arm in order:
            candidate_id = hashlib.sha256(
                f"{fixture_id}:{randomization_seed}:{repetition}:{arm}".encode("utf-8")
            ).hexdigest()[:16]
            candidate_map[candidate_id] = {"repetition": repetition, "arm": arm}

    commitment_payload = {
        "fixture_id": fixture_id,
        "repetitions": repetitions,
        "seed": randomization_seed,
        "orders": orders,
        "candidate_ids": sorted(candidate_map),
    }
    commitment_hash = sha256_bytes(canonical_json(commitment_payload))
    write_json(
        output / "randomization-commitment.json",
        {**commitment_payload, "sha256": commitment_hash},
    )

    generation_records: dict[str, dict[str, Any]] = {}
    for repetition, order in enumerate(orders, start=1):
        for arm in order:
            candidate_id = next(
                key
                for key, value in candidate_map.items()
                if value == {"repetition": repetition, "arm": arm}
            )
            prompt = (packages / arm / "prompt.md").read_text(encoding="utf-8")
            response = call_copilot(
                copilot_binary,
                generator_model,
                prompt,
                max_ai_credits=generation_max_ai_credits,
                timeout_seconds=timeout_seconds,
                retries=retries,
                call_id=f"gen-{candidate_id}",
            )
            generation_records[candidate_id] = response
            write_json(output / "raw-generations" / f"{candidate_id}.json", response)
            candidate_path = output / "candidate-outputs" / f"{candidate_id}.md"
            candidate_path.parent.mkdir(parents=True, exist_ok=True)
            candidate_path.write_text(response["content"], encoding="utf-8")

    evaluation_records: dict[str, dict[str, Any]] = {}
    for candidate_id in sorted(candidate_map):
        candidate_output = generation_records[candidate_id]["content"]
        response = call_copilot(
            copilot_binary,
            evaluator_model,
            evaluator_prompt(evaluator_package, candidate_output),
            max_ai_credits=evaluator_max_ai_credits,
            timeout_seconds=timeout_seconds,
            retries=retries,
            call_id=f"eval-{candidate_id}",
        )
        parse_error = None
        try:
            parsed = parse_json_object(response["content"])
        except Exception as exc:
            parse_error = repr(exc)
            parsed = {
                "verdict": "FAIL",
                "first_unmet_requirement": "evaluator-json-parse",
                "unsupported_claims": [],
                "unrelated_changes": [],
                "evidence": [],
            }
        verdict = parsed.get("verdict")
        if verdict not in {"PASS", "FAIL"}:
            verdict = "FAIL"
            parsed["first_unmet_requirement"] = (
                parsed.get("first_unmet_requirement") or "invalid-evaluator-verdict"
            )
        normalized = {
            "candidate_id": candidate_id,
            "verdict": verdict,
            "first_unmet_requirement": parsed.get("first_unmet_requirement"),
            "unsupported_claims": (
                parsed.get("unsupported_claims")
                if isinstance(parsed.get("unsupported_claims"), list)
                else []
            ),
            "unrelated_changes": (
                parsed.get("unrelated_changes")
                if isinstance(parsed.get("unrelated_changes"), list)
                else []
            ),
            "evidence": parsed.get("evidence") if isinstance(parsed.get("evidence"), list) else [],
            "parse_error": parse_error,
            "model_requested": evaluator_model,
            "input_tokens": response["input_tokens"],
            "output_tokens": response["output_tokens"],
            "latency_seconds": response["latency_seconds"],
            "attempts": response["attempts"],
            "events": response["events"],
        }
        evaluation_records[candidate_id] = normalized
        write_json(output / "blinded-evaluations" / f"{candidate_id}.json", normalized)

    write_json(output / "unblinding-map.json", candidate_map)
    rows: list[dict[str, Any]] = []
    for candidate_id, mapping in sorted(
        candidate_map.items(), key=lambda item: (item[1]["repetition"], item[1]["arm"])
    ):
        generation = generation_records[candidate_id]
        evaluation = evaluation_records[candidate_id]
        rows.append(
            {
                "candidate_id": candidate_id,
                "repetition": mapping["repetition"],
                "arm": mapping["arm"],
                "verdict": evaluation["verdict"],
                "first_unmet_requirement": evaluation["first_unmet_requirement"],
                "unsupported_claims": evaluation["unsupported_claims"],
                "unrelated_changes": evaluation["unrelated_changes"],
                "prompt_tokens": generation["input_tokens"],
                "completion_tokens": generation["output_tokens"],
                "generation_latency_seconds": generation["latency_seconds"],
                "generation_attempts": generation["attempts"],
                "evaluator_input_tokens": evaluation["input_tokens"],
                "evaluator_output_tokens": evaluation["output_tokens"],
                "evaluator_attempts": evaluation["attempts"],
            }
        )

    summary = summarize_results(rows, randomization_seed)
    report = {
        "schema_version": "1.0.0",
        "fixture_id": fixture_id,
        "public_development_evidence_only": True,
        "execution_adapter": "github-copilot-cli",
        "generator_model": generator_model,
        "evaluator_model": evaluator_model,
        "repetitions_per_arm": repetitions,
        "context_tier": "default",
        "reasoning_effort": "low",
        "tool_access": "excluded; zero tool events required",
        "output_token_ceiling": "provider default, identical model and CLI settings across arms",
        "generation_max_ai_credits_per_call": generation_max_ai_credits,
        "evaluator_max_ai_credits_per_call": evaluator_max_ai_credits,
        "timeout_seconds": timeout_seconds,
        "retry_limit": retries,
        "randomization_commitment_sha256": commitment_hash,
        "package_manifests": manifests,
        "rows": rows,
        "summary": summary,
    }
    write_json(output / "comparison-report.json", report)
    return report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="promptbench-live")
    result.add_argument("--root", type=Path, default=Path.cwd())
    result.add_argument("--fixture", default="research-contradiction-001")
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--copilot-binary", default="copilot")
    result.add_argument("--generator-model", default="gpt-5.4")
    result.add_argument("--evaluator-model", default="claude-haiku-4.5")
    result.add_argument("--repetitions", type=int, default=5)
    result.add_argument("--randomization-seed", type=int, required=True)
    result.add_argument("--max-context-chars", type=int, default=200_000)
    result.add_argument("--generation-max-ai-credits", type=int, default=10)
    result.add_argument("--evaluator-max-ai-credits", type=int, default=5)
    result.add_argument("--timeout-seconds", type=int, default=180)
    result.add_argument("--retries", type=int, default=1)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not (os.environ.get("COPILOT_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")):
        print("promptbench-live: COPILOT_GITHUB_TOKEN or GITHUB_TOKEN is required")
        return 2
    try:
        report = run_fixture(
            args.root.resolve(),
            args.fixture,
            args.output.resolve(),
            copilot_binary=args.copilot_binary,
            generator_model=args.generator_model,
            evaluator_model=args.evaluator_model,
            repetitions=args.repetitions,
            randomization_seed=args.randomization_seed,
            max_context_chars=args.max_context_chars,
            generation_max_ai_credits=args.generation_max_ai_credits,
            evaluator_max_ai_credits=args.evaluator_max_ai_credits,
            timeout_seconds=args.timeout_seconds,
            retries=args.retries,
        )
    except (LiveBenchmarkError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"promptbench-live: {exc}")
        return 2
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
