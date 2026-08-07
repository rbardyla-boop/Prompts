from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .kernel import KernelError, load_json


STATE_LIMIT_BYTES = 10_240
LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "PLANNING": {"EXECUTING", "BLOCKED", "ESCALATED"},
    "EXECUTING": {"VERIFYING", "REPAIRING", "BLOCKED", "ESCALATED"},
    "VERIFYING": {"REPAIRING", "BLOCKED", "ESCALATED", "TERMINAL"},
    "REPAIRING": {"EXECUTING", "VERIFYING", "BLOCKED", "ESCALATED"},
    "BLOCKED": {"PLANNING", "EXECUTING", "ESCALATED"},
    "ESCALATED": {"PLANNING", "BLOCKED"},
    "TERMINAL": set(),
}
TERMINAL_STATES = {
    "PASS",
    "PASS_WITH_DISCLOSED_LIMITS",
    "SEALED_NEGATIVE_RESULT",
    "BLOCKED_EXTERNAL",
    "PROMPTS_V2_VALIDATED",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result[:48] or "task"


def agent_dir(root: Path) -> Path:
    return root / "agent"


def load_taskpack(repo_root: Path, taskpack_id: str) -> dict[str, Any]:
    path = repo_root / "taskpacks" / f"{taskpack_id}.json"
    value = load_json(path)
    if value.get("taskpack_id") != taskpack_id:
        raise KernelError(f"task pack id mismatch in {path}")
    required = {
        "taskpack_id", "version", "task_type", "module_ids", "completion_checks",
        "allowed_actions", "forbidden_actions", "default_budgets", "terminal_states",
    }
    missing = required - value.keys()
    if missing:
        raise KernelError(f"task pack {taskpack_id} missing {sorted(missing)}")
    if not set(value["terminal_states"]).issubset(TERMINAL_STATES):
        raise KernelError(f"task pack {taskpack_id} declares unknown terminal state")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _state_path(root: Path) -> Path:
    return agent_dir(root) / "state.json"


def _contract_path(root: Path) -> Path:
    return agent_dir(root) / "contract.json"


def load_state(root: Path) -> dict[str, Any]:
    return load_json(_state_path(root))


def load_contract(root: Path) -> dict[str, Any]:
    return load_json(_contract_path(root))


def _assert_state_size(state: dict[str, Any]) -> None:
    size = len(json.dumps(state, ensure_ascii=False).encode("utf-8"))
    if size >= STATE_LIMIT_BYTES:
        raise KernelError(f"state.json is {size} bytes; limit is {STATE_LIMIT_BYTES - 1}")


def _trace_path(root: Path) -> Path:
    return agent_dir(root) / "traces" / "events.jsonl"


def _read_trace(root: Path) -> list[dict[str, Any]]:
    path = _trace_path(root)
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise KernelError(f"invalid trace JSON at line {number}") from exc
        if not isinstance(value, dict):
            raise KernelError(f"trace line {number} is not an object")
        records.append(value)
    return records


def append_trace(root: Path, event: dict[str, Any]) -> dict[str, Any]:
    records = _read_trace(root)
    previous_hash = records[-1]["event_hash"] if records else "0" * 64
    body = {
        "sequence": len(records) + 1,
        "timestamp": utc_now(),
        "previous_hash": previous_hash,
        **event,
    }
    body["event_hash"] = digest_value(body)
    path = _trace_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(body, sort_keys=True, ensure_ascii=False) + "\n")
    return body


def verify_trace(root: Path) -> dict[str, Any]:
    records = _read_trace(root)
    previous_hash = "0" * 64
    for expected_sequence, record in enumerate(records, 1):
        if record.get("sequence") != expected_sequence:
            raise KernelError(f"trace sequence mismatch at {expected_sequence}")
        if record.get("previous_hash") != previous_hash:
            raise KernelError(f"trace previous_hash mismatch at {expected_sequence}")
        claimed = record.get("event_hash")
        if not isinstance(claimed, str):
            raise KernelError(f"trace event_hash missing at {expected_sequence}")
        body = dict(record)
        del body["event_hash"]
        actual = digest_value(body)
        if actual != claimed:
            raise KernelError(f"trace hash mismatch at {expected_sequence}")
        previous_hash = claimed
    return {"event_count": len(records), "trace_root_hash": previous_hash, "result": "PASS"}


def initialize_project(repo_root: Path, workspace_root: Path, taskpack_id: str, goal: str, budgets: dict[str, Any] | None = None) -> dict[str, Any]:
    if not goal.strip():
        raise KernelError("goal cannot be empty")
    target = agent_dir(workspace_root)
    if target.exists() and any(target.iterdir()):
        raise KernelError(f"agent directory already initialized: {target}")

    taskpack = load_taskpack(repo_root, taskpack_id)
    task_id = f"{_slug(taskpack_id)}-{digest_value(goal)[:12]}"
    effective_budgets = dict(taskpack["default_budgets"])
    if budgets:
        effective_budgets.update(budgets)

    contract = {
        "schema_version": "1.0.0",
        "task_id": task_id,
        "taskpack_id": taskpack_id,
        "objective": goal.strip(),
        "deliverables": taskpack.get("deliverables", []),
        "constraints": taskpack.get("constraints", []),
        "module_ids": taskpack["module_ids"],
        "completion_checks": taskpack["completion_checks"],
        "allowed_actions": taskpack["allowed_actions"],
        "forbidden_actions": taskpack["forbidden_actions"],
        "terminal_states": taskpack["terminal_states"],
        "created_at": utc_now(),
    }
    contract_hash = digest_value(contract)
    state = {
        "schema_version": "1.0.0",
        "task_id": task_id,
        "status": "PLANNING",
        "current_phase": "initialize",
        "completed_components": [],
        "next_action": "compose bounded first cycle",
        "failed_check_id": None,
        "failure_fingerprint": None,
        "blocked_by": None,
        "attempts_on_current_failure": 0,
        "latest_verified_checkpoint": "checkpoint-0000",
        "remaining_budget": effective_budgets,
        "terminal_result": None,
        "contract_hash": contract_hash,
    }
    _assert_state_size(state)

    target.mkdir(parents=True, exist_ok=True)
    for directory in ("traces", "checkpoints", "evals", "receipts", "recovery", "amendments", "final-report"):
        (target / directory).mkdir(exist_ok=True)

    _write_json(_contract_path(workspace_root), contract)
    _write_json(_state_path(workspace_root), state)
    _write_json(target / "permissions.json", {
        "allowed_actions": taskpack["allowed_actions"],
        "forbidden_actions": taskpack["forbidden_actions"],
        "policy": "closed_action_api",
    })
    _write_json(target / "budgets.json", effective_budgets)
    (target / "progress.md").write_text(f"# Progress\n\n- {utc_now()}: initialized `{task_id}`\n", encoding="utf-8")
    (target / "decisions.md").write_text("# Decisions\n\n- Contract and task pack frozen at initialization.\n", encoding="utf-8")

    checkpoint = {
        "checkpoint_id": "checkpoint-0000",
        "task_id": task_id,
        "contract_hash": contract_hash,
        "state_hash": digest_value(state),
        "created_at": utc_now(),
    }
    _write_json(target / "checkpoints" / "checkpoint-0000.json", checkpoint)
    append_trace(workspace_root, {
        "event_type": "INITIALIZE",
        "state_before": None,
        "state_after": "PLANNING",
        "evidence": {"contract_hash": contract_hash, "checkpoint": "checkpoint-0000"},
    })
    return {"task_id": task_id, "contract_hash": contract_hash, "state": state, "checkpoint": checkpoint}


def transition(root: Path, new_status: str, *, phase: str | None = None, next_action: str | None = None, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    state = load_state(root)
    current = state["status"]
    if new_status not in LEGAL_TRANSITIONS:
        raise KernelError(f"unknown state: {new_status}")
    if new_status not in LEGAL_TRANSITIONS[current]:
        raise KernelError(f"illegal state transition: {current} -> {new_status}")

    before_hash = digest_value(state)
    state["status"] = new_status
    if phase is not None:
        state["current_phase"] = phase
    if next_action is not None:
        state["next_action"] = next_action
    _assert_state_size(state)
    _write_json(_state_path(root), state)
    append_trace(root, {
        "event_type": "STATE_TRANSITION",
        "state_before": current,
        "state_after": new_status,
        "state_before_hash": before_hash,
        "state_after_hash": digest_value(state),
        "evidence": evidence or {},
    })
    return state


def permission_allowed(root: Path, action: str) -> bool:
    policy = load_json(agent_dir(root) / "permissions.json")
    if action in policy["forbidden_actions"]:
        return False
    return action in policy["allowed_actions"]


def recovery_report(root: Path) -> dict[str, Any]:
    contract = load_contract(root)
    state = load_state(root)
    return {
        "task_id": state["task_id"],
        "objective": contract["objective"],
        "current_phase": state["current_phase"],
        "status": state["status"],
        "completed_components": state["completed_components"],
        "failed_check_id": state["failed_check_id"],
        "latest_verified_checkpoint": state["latest_verified_checkpoint"],
        "next_action": state["next_action"],
        "blocked_by": state["blocked_by"],
        "remaining_budget": state["remaining_budget"],
        "contract_hash": state["contract_hash"],
    }


def grade_recovery(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    expected = recovery_report(root)
    mismatches = {key: {"expected": expected[key], "actual": report.get(key)} for key in expected if report.get(key) != expected[key]}
    return {"result": "PASS" if not mismatches else "FAIL", "mismatches": mismatches, "report_hash": digest_value(report)}


def run_recovery_test(repo_root: Path, workspace_root: Path) -> dict[str, Any]:
    command = [sys.executable, "-m", "promptctl", "--root", str(repo_root), "_recover-child", "--workspace", str(workspace_root)]
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(repo_root), "LANG": os.environ.get("LANG", "C.UTF-8")}
    result = subprocess.run(command, cwd=repo_root, env=env, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise KernelError(f"recovery subprocess failed ({result.returncode}): {result.stderr.strip()}")
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise KernelError("recovery subprocess emitted invalid JSON") from exc
    grade = grade_recovery(workspace_root, report)
    receipt = {"command": command, "subprocess_returncode": result.returncode, "fresh_process": True, "report": report, "grade": grade}
    _write_json(agent_dir(workspace_root) / "recovery" / "latest.json", receipt)
    current = load_state(workspace_root)["status"]
    append_trace(workspace_root, {"event_type": "RECOVERY_TEST", "state_before": current, "state_after": current, "evidence": {"result": grade["result"], "report_hash": grade["report_hash"]}})
    return receipt


def submit_completion(root: Path, check_results: dict[str, bool], evaluator: dict[str, Any], recovery_result: str) -> dict[str, Any]:
    contract = load_contract(root)
    state = load_state(root)
    required_ids = [item["id"] for item in contract["completion_checks"]]
    missing = [check_id for check_id in required_ids if check_id not in check_results]
    failed = [check_id for check_id in required_ids if check_id in check_results and check_results[check_id] is not True]
    trace_result: dict[str, Any] | None = None
    trace_error: str | None = None
    try:
        trace_result = verify_trace(root)
    except KernelError as exc:
        trace_error = str(exc)

    gates = {
        "all_required_results_present": not missing,
        "all_required_checks_pass": not failed and not missing,
        "evaluator_pass": evaluator.get("verdict") == "PASS",
        "recovery_pass": recovery_result == "PASS",
        "trace_integrity_pass": trace_error is None,
        "contract_unchanged": state["contract_hash"] == digest_value(contract),
    }
    accepted = all(gates.values())
    receipt = {
        "task_id": state["task_id"],
        "submitted_at": utc_now(),
        "worker_claim": "DONE",
        "required_check_ids": required_ids,
        "check_results": check_results,
        "missing_checks": missing,
        "failed_checks": failed,
        "evaluator": evaluator,
        "recovery_result": recovery_result,
        "trace_result": trace_result,
        "trace_error": trace_error,
        "gates": gates,
        "accepted": accepted,
    }
    receipt["receipt_hash"] = digest_value(receipt)

    if accepted:
        if state["status"] != "VERIFYING":
            raise KernelError("completion may only be accepted from VERIFYING")
        state = transition(root, "TERMINAL", phase="complete", next_action="none", evidence={"receipt_hash": receipt["receipt_hash"]})
        before_hash = digest_value(state)
        state["terminal_result"] = contract["terminal_states"][0]
        _assert_state_size(state)
        _write_json(_state_path(root), state)
        append_trace(root, {
            "event_type": "TERMINAL_RESULT_SET",
            "state_before": "TERMINAL",
            "state_after": "TERMINAL",
            "state_before_hash": before_hash,
            "state_after_hash": digest_value(state),
            "evidence": {"terminal_result": state["terminal_result"], "receipt_hash": receipt["receipt_hash"]},
        })
    else:
        failed_id = (failed or missing or ["completion-gate"])[0]
        fingerprint = hashlib.sha256(f"{failed_id}:{receipt['receipt_hash']}".encode("utf-8")).hexdigest()
        state["failed_check_id"] = failed_id
        state["failure_fingerprint"] = fingerprint
        state["attempts_on_current_failure"] += 1
        state["next_action"] = f"repair:{failed_id}"
        _assert_state_size(state)
        _write_json(_state_path(root), state)
        if state["status"] == "VERIFYING":
            transition(root, "REPAIRING", phase="repair", next_action=f"repair:{failed_id}", evidence={"failed_check_id": failed_id, "failure_fingerprint": fingerprint, "receipt_hash": receipt["receipt_hash"]})

    _write_json(agent_dir(root) / "receipts" / f"completion-{receipt['receipt_hash'][:12]}.json", receipt)
    return receipt


def classify_amendment(changes: dict[str, Any]) -> str:
    material = {"objective", "deliverables", "constraints", "completion_checks", "allowed_actions", "forbidden_actions", "terminal_states", "budgets"}
    if material & changes.keys():
        return "C"
    if changes:
        return "B"
    return "A"


def propose_amendment(root: Path, changes: dict[str, Any], *, human_approval: bool = False) -> dict[str, Any]:
    if load_state(root)["status"] == "TERMINAL":
        raise KernelError("terminal tasks are immutable; amendment rejected")
    amendment_class = classify_amendment(changes)
    status = "APPROVED" if amendment_class != "C" or human_approval else "AWAITING_HUMAN"
    record = {
        "amendment_id": f"AMD-{digest_value(changes)[:10]}",
        "class": amendment_class,
        "changes": changes,
        "human_approval": human_approval,
        "status": status,
        "created_at": utc_now(),
    }
    _write_json(agent_dir(root) / "amendments" / f"{record['amendment_id']}.json", record)
    current = load_state(root)["status"]
    append_trace(root, {"event_type": "AMENDMENT_PROPOSED", "state_before": current, "state_after": current, "evidence": {"amendment_id": record["amendment_id"], "class": amendment_class, "status": status}})
    return record


def archive_manifest(root: Path) -> dict[str, Any]:
    base = agent_dir(root)
    if not base.exists():
        raise KernelError("agent directory is not initialized")
    files = []
    for path in sorted(p for p in base.rglob("*") if p.is_file()):
        files.append({"path": str(path.relative_to(root)), "sha256": digest_file(path), "size_bytes": path.stat().st_size})
    manifest = {"schema_version": "1.0.0", "created_at": utc_now(), "task_id": load_state(root)["task_id"], "files": files}
    manifest["root_hash"] = digest_value(files)
    _write_json(base / "archive-manifest.json", manifest)
    return manifest


def self_test(repo_root: Path, taskpack_id: str = "harness-terminal-test") -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="prompts-v2-harness-") as temp:
        workspace = Path(temp)
        initialized = initialize_project(repo_root, workspace, taskpack_id, "Implement five deterministic requirements.")
        transition(workspace, "EXECUTING", phase="build", next_action="implement requirements")
        transition(workspace, "VERIFYING", phase="verify", next_action="run completion checks")

        first_results = {"req-1": True, "req-2": True, "req-3": True, "req-4": True, "req-5": False}
        rejected = submit_completion(workspace, first_results, {"verdict": "PASS", "evidence": ["worker documentation"]}, "PASS")
        if rejected["accepted"]:
            raise KernelError("false completion was accepted")
        repaired_state = load_state(workspace)
        if repaired_state["status"] != "REPAIRING":
            raise KernelError("failed completion did not enter REPAIRING")
        if repaired_state["failed_check_id"] != "req-5":
            raise KernelError("failed requirement was not persisted")

        recovery = run_recovery_test(repo_root, workspace)
        if recovery["grade"]["result"] != "PASS":
            raise KernelError("recovery test failed")

        amendment = propose_amendment(workspace, {"completion_checks": []}, human_approval=False)
        if amendment["status"] != "AWAITING_HUMAN":
            raise KernelError("material amendment was auto-approved")

        transition(workspace, "EXECUTING", phase="repair", next_action="implement req-5")
        transition(workspace, "VERIFYING", phase="verify", next_action="run repaired suite")
        final_results = {f"req-{index}": True for index in range(1, 6)}
        accepted = submit_completion(workspace, final_results, {"verdict": "PASS", "evidence": ["independent evaluator"]}, "PASS")
        if not accepted["accepted"]:
            raise KernelError("repaired completion was rejected")
        if load_state(workspace)["status"] != "TERMINAL":
            raise KernelError("accepted completion did not enter TERMINAL")

        trace = verify_trace(workspace)
        return {
            "result": "PASS",
            "task_id": initialized["task_id"],
            "false_completion_rejected": True,
            "failed_requirement_persisted": True,
            "recovery_passed": True,
            "repaired_completion_accepted": True,
            "trace_integrity": trace,
            "material_amendment_auto_approval_rejected": True,
        }
