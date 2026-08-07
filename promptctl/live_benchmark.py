from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .benchmark import canonical_json, prepare_arm


MODELS_API = "https://models.github.ai/inference/chat/completions"


class LiveBenchmarkError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def call_model(
    token: str,
    model: str,
    prompt: str,
    *,
    max_tokens: int,
    temperature: float,
    timeout_seconds: int,
    retries: int,
    json_mode: bool = False,
) -> dict[str, Any]:
    request_body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    if json_mode:
        request_body["response_format"] = {"type": "json_object"}

    encoded = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
    last_error: str | None = None
    for attempt in range(retries + 1):
        request = urllib.request.Request(
            MODELS_API,
            data=encoded,
            method="POST",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2026-03-10",
            },
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read()
            elapsed = time.monotonic() - started
            payload = json.loads(raw.decode("utf-8"))
            choices = payload.get("choices") or []
            if not choices:
                raise LiveBenchmarkError(f"model {model} returned no choices")
            message = choices[0].get("message") or {}
            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                raise LiveBenchmarkError(f"model {model} returned empty content")
            return {
                "model_requested": model,
                "model_returned": payload.get("model"),
                "content": content,
                "usage": payload.get("usage") or {},
                "latency_seconds": round(elapsed, 6),
                "attempts": attempt + 1,
                "finish_reason": choices[0].get("finish_reason"),
                "response": payload,
            }
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_error = f"HTTP {exc.code}: {body[:1000]}"
            if exc.code not in {429, 500, 502, 503, 504} or attempt >= retries:
                raise LiveBenchmarkError(last_error) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = repr(exc)
            if attempt >= retries:
                raise LiveBenchmarkError(last_error) from exc
        if attempt < retries:
            time.sleep(2 ** attempt)
    raise LiveBenchmarkError(last_error or "unknown model-call failure")


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
        prompt_tokens = [row.get("prompt_tokens") for row in arm_rows if isinstance(row.get("prompt_tokens"), int)]
        completion_tokens = [row.get("completion_tokens") for row in arm_rows if isinstance(row.get("completion_tokens"), int)]
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
        "reason_final_validation_ineligible": "This fixture is public development apparatus and not independently held final evidence.",
    }


def run_fixture(
    root: Path,
    fixture_id: str,
    output: Path,
    *,
    token: str,
    generator_model: str,
    evaluator_model: str,
    repetitions: int,
    randomization_seed: int,
    max_context_chars: int,
    generation_max_tokens: int,
    evaluator_max_tokens: int,
    temperature: float,
    timeout_seconds: int,
    retries: int,
) -> dict[str, Any]:
    if repetitions < 1:
        raise LiveBenchmarkError("repetitions must be positive")
    output.mkdir(parents=True, exist_ok=False)

    manifests: dict[str, dict[str, Any]] = {}
    packages = output / "packages"
    for arm in "ABC":
        manifests[arm] = prepare_arm(root, fixture_id, arm, packages / arm, max_context_chars)

    if len({manifests[arm]["fixture_sha256"] for arm in "ABC"}) != 1:
        raise LiveBenchmarkError("fixture hash mismatch across arms")
    if len({manifests[arm]["evaluator_package_sha256"] for arm in "ABC"}) != 1:
        raise LiveBenchmarkError("evaluator hash mismatch across arms")

    evaluator_package = json.loads((packages / "A" / "evaluator-package.json").read_text(encoding="utf-8"))
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
    write_json(output / "randomization-commitment.json", {**commitment_payload, "sha256": commitment_hash})

    generation_records: dict[str, dict[str, Any]] = {}
    for repetition, order in enumerate(orders, start=1):
        for arm in order:
            candidate_id = next(
                key for key, value in candidate_map.items()
                if value == {"repetition": repetition, "arm": arm}
            )
            prompt = (packages / arm / "prompt.md").read_text(encoding="utf-8")
            response = call_model(
                token,
                generator_model,
                prompt,
                max_tokens=generation_max_tokens,
                temperature=temperature,
                timeout_seconds=timeout_seconds,
                retries=retries,
            )
            generation_records[candidate_id] = response
            write_json(output / "raw-generations" / f"{candidate_id}.json", response)
            (output / "candidate-outputs" / f"{candidate_id}.md").parent.mkdir(parents=True, exist_ok=True)
            (output / "candidate-outputs" / f"{candidate_id}.md").write_text(response["content"], encoding="utf-8")

    evaluation_records: dict[str, dict[str, Any]] = {}
    for candidate_id in sorted(candidate_map):
        candidate_output = generation_records[candidate_id]["content"]
        response = call_model(
            token,
            evaluator_model,
            evaluator_prompt(evaluator_package, candidate_output),
            max_tokens=evaluator_max_tokens,
            temperature=0.0,
            timeout_seconds=timeout_seconds,
            retries=retries,
            json_mode=True,
        )
        parse_error = None
        try:
            parsed = parse_json_object(response["content"])
        except Exception as exc:  # evaluator parse failure is evidence, not a hidden retry
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
            parsed["first_unmet_requirement"] = parsed.get("first_unmet_requirement") or "invalid-evaluator-verdict"
        normalized = {
            "candidate_id": candidate_id,
            "verdict": verdict,
            "first_unmet_requirement": parsed.get("first_unmet_requirement"),
            "unsupported_claims": parsed.get("unsupported_claims") if isinstance(parsed.get("unsupported_claims"), list) else [],
            "unrelated_changes": parsed.get("unrelated_changes") if isinstance(parsed.get("unrelated_changes"), list) else [],
            "evidence": parsed.get("evidence") if isinstance(parsed.get("evidence"), list) else [],
            "parse_error": parse_error,
            "raw_model_response": response,
        }
        evaluation_records[candidate_id] = normalized
        write_json(output / "blinded-evaluations" / f"{candidate_id}.json", normalized)

    write_json(output / "unblinding-map.json", candidate_map)
    rows: list[dict[str, Any]] = []
    for candidate_id, mapping in sorted(candidate_map.items(), key=lambda item: (item[1]["repetition"], item[1]["arm"])):
        generation = generation_records[candidate_id]
        evaluation = evaluation_records[candidate_id]
        usage = generation.get("usage") or {}
        rows.append({
            "candidate_id": candidate_id,
            "repetition": mapping["repetition"],
            "arm": mapping["arm"],
            "verdict": evaluation["verdict"],
            "first_unmet_requirement": evaluation["first_unmet_requirement"],
            "unsupported_claims": evaluation["unsupported_claims"],
            "unrelated_changes": evaluation["unrelated_changes"],
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "generation_latency_seconds": generation["latency_seconds"],
            "generation_attempts": generation["attempts"],
            "evaluator_attempts": evaluation["raw_model_response"]["attempts"],
        })

    summary = summarize_results(rows, randomization_seed)
    report = {
        "schema_version": "1.0.0",
        "fixture_id": fixture_id,
        "public_development_evidence_only": True,
        "generator_model": generator_model,
        "evaluator_model": evaluator_model,
        "repetitions_per_arm": repetitions,
        "generation_max_tokens": generation_max_tokens,
        "evaluator_max_tokens": evaluator_max_tokens,
        "temperature": temperature,
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
    result.add_argument("--generator-model", default="openai/gpt-4.1")
    result.add_argument("--evaluator-model", default="openai/gpt-4o")
    result.add_argument("--repetitions", type=int, default=5)
    result.add_argument("--randomization-seed", type=int, required=True)
    result.add_argument("--max-context-chars", type=int, default=200_000)
    result.add_argument("--generation-max-tokens", type=int, default=1600)
    result.add_argument("--evaluator-max-tokens", type=int, default=700)
    result.add_argument("--temperature", type=float, default=0.3)
    result.add_argument("--timeout-seconds", type=int, default=120)
    result.add_argument("--retries", type=int, default=2)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("promptbench-live: GITHUB_TOKEN is required")
        return 2
    try:
        report = run_fixture(
            args.root.resolve(),
            args.fixture,
            args.output.resolve(),
            token=token,
            generator_model=args.generator_model,
            evaluator_model=args.evaluator_model,
            repetitions=args.repetitions,
            randomization_seed=args.randomization_seed,
            max_context_chars=args.max_context_chars,
            generation_max_tokens=args.generation_max_tokens,
            evaluator_max_tokens=args.evaluator_max_tokens,
            temperature=args.temperature,
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
