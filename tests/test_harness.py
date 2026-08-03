from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from promptctl.harness import (
    KernelError,
    initialize_project,
    load_state,
    permission_allowed,
    propose_amendment,
    run_recovery_test,
    self_test,
    submit_completion,
    transition,
    verify_trace,
)


ROOT = Path(__file__).resolve().parents[1]


class HarnessTests(unittest.TestCase):
    def test_terminal_self_test_passes(self) -> None:
        report = self_test(ROOT)
        self.assertEqual(report["result"], "PASS")
        self.assertTrue(report["false_completion_rejected"])
        self.assertTrue(report["failed_requirement_persisted"])
        self.assertTrue(report["recovery_passed"])
        self.assertTrue(report["repaired_completion_accepted"])
        self.assertTrue(report["material_amendment_auto_approval_rejected"])

    def test_false_done_enters_repairing_and_persists_failure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-test-") as temp:
            workspace = Path(temp)
            initialize_project(
                ROOT,
                workspace,
                "harness-terminal-test",
                "Implement five deterministic requirements.",
            )
            transition(workspace, "EXECUTING", phase="build")
            transition(workspace, "VERIFYING", phase="verify")

            receipt = submit_completion(
                workspace,
                {
                    "req-1": True,
                    "req-2": True,
                    "req-3": True,
                    "req-4": True,
                    "req-5": False,
                },
                {"verdict": "PASS", "evidence": ["worker documentation"]},
                "PASS",
            )

            state = load_state(workspace)
            self.assertFalse(receipt["accepted"])
            self.assertEqual(state["status"], "REPAIRING")
            self.assertEqual(state["failed_check_id"], "req-5")
            self.assertEqual(state["next_action"], "repair:req-5")
            self.assertIsNone(state["terminal_result"])

    def test_worker_done_cannot_authorize_terminal_state(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-test-") as temp:
            workspace = Path(temp)
            initialize_project(
                ROOT,
                workspace,
                "harness-terminal-test",
                "Implement five deterministic requirements.",
            )
            transition(workspace, "EXECUTING", phase="build")
            transition(workspace, "VERIFYING", phase="verify")

            receipt = submit_completion(
                workspace,
                {f"req-{index}": True for index in range(1, 6)},
                {"verdict": "FAIL", "evidence": ["independent defect"]},
                "PASS",
            )

            self.assertFalse(receipt["accepted"])
            self.assertFalse(receipt["gates"]["evaluator_pass"])
            self.assertEqual(load_state(workspace)["status"], "REPAIRING")

    def test_fresh_subprocess_recovery_matches_canonical_state(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-test-") as temp:
            workspace = Path(temp)
            initialize_project(
                ROOT,
                workspace,
                "software-build",
                "Build a deterministic fixture.",
            )
            transition(
                workspace,
                "EXECUTING",
                phase="implementation",
                next_action="implement first requirement",
            )

            receipt = run_recovery_test(ROOT, workspace)
            self.assertTrue(receipt["fresh_process"])
            self.assertEqual(receipt["grade"]["result"], "PASS")
            self.assertEqual(receipt["report"]["status"], "EXECUTING")
            self.assertEqual(
                receipt["report"]["next_action"],
                "implement first requirement",
            )

    def test_trace_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-test-") as temp:
            workspace = Path(temp)
            initialize_project(
                ROOT,
                workspace,
                "software-build",
                "Build a deterministic fixture.",
            )
            transition(workspace, "EXECUTING", phase="implementation")
            trace_path = workspace / "agent" / "traces" / "events.jsonl"
            records = trace_path.read_text(encoding="utf-8").splitlines()
            event = json.loads(records[0])
            event["event_type"] = "TAMPERED"
            records[0] = json.dumps(event, sort_keys=True)
            trace_path.write_text("\n".join(records) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(KernelError, "trace hash mismatch"):
                verify_trace(workspace)

    def test_material_amendment_requires_human_approval(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-test-") as temp:
            workspace = Path(temp)
            initialize_project(
                ROOT,
                workspace,
                "software-build",
                "Build a deterministic fixture.",
            )
            record = propose_amendment(
                workspace,
                {"completion_checks": []},
                human_approval=False,
            )
            self.assertEqual(record["class"], "C")
            self.assertEqual(record["status"], "AWAITING_HUMAN")

    def test_forbidden_action_is_denied(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-test-") as temp:
            workspace = Path(temp)
            initialize_project(
                ROOT,
                workspace,
                "software-build",
                "Build a deterministic fixture.",
            )
            self.assertTrue(permission_allowed(workspace, "run_tests"))
            self.assertFalse(permission_allowed(workspace, "production_deploy"))
            self.assertFalse(permission_allowed(workspace, "access_secrets"))
            self.assertFalse(permission_allowed(workspace, "unlisted_action"))

    def test_state_remains_under_ten_kibibytes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-test-") as temp:
            workspace = Path(temp)
            initialize_project(
                ROOT,
                workspace,
                "deep-research",
                "Audit a bounded factual question.",
            )
            state_path = workspace / "agent" / "state.json"
            self.assertLess(state_path.stat().st_size, 10_240)


if __name__ == "__main__":
    unittest.main()
