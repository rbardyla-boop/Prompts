from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # pragma: no cover
    Draft202012Validator = None
    FormatChecker = None

from promptctl.benchmark import prepare_arm
from promptctl.harness import load_taskpack


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(Draft202012Validator is None, "jsonschema test dependency is not installed")
class BenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/benchmark-fixture.schema.json").read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(schema)
        self.validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.spec = json.loads(
            (ROOT / "benchmarks/benchmark-spec.json").read_text(encoding="utf-8")
        )

    def test_five_task_families_are_present(self) -> None:
        tasks = self.spec["task_families"]
        self.assertEqual(len(tasks), 5)
        self.assertEqual(
            {task["family"] for task in tasks},
            {"research", "coding", "long-form-writing", "game-creative", "factual-audit"},
        )

    def test_all_fixtures_validate_and_reference_existing_assets(self) -> None:
        for task in self.spec["task_families"]:
            path = ROOT / task["path"]
            self.assertTrue(path.is_file(), path)
            fixture = json.loads(path.read_text(encoding="utf-8"))
            errors = list(self.validator.iter_errors(fixture))
            self.assertEqual(errors, [], errors[0].message if errors else "")
            self.assertEqual(fixture["fixture_id"], task["fixture_id"])
            self.assertEqual(fixture["family"], task["family"])
            self.assertTrue((ROOT / fixture["legacy_arm_source"]).is_file())
            load_taskpack(ROOT, fixture["v2_task_pack"])

    def test_all_arms_share_completion_checks(self) -> None:
        self.assertEqual(set(self.spec["arms"]), {"A", "B", "C"})
        controls = set(self.spec["matched_controls"])
        self.assertIn("same evaluator rubric", controls)
        self.assertIn("same deterministic completion checks", controls)
        self.assertIn("same model and quantization", controls)

    def test_public_apparatus_cannot_be_called_final_sealed_evidence(self) -> None:
        self.assertEqual(
            self.spec["status"],
            "PUBLIC_APPARATUS_NOT_FINAL_SEALED_EVIDENCE",
        )
        self.assertIn("independently held", self.spec["final_evidence_rule"])

    def test_all_three_arms_package_with_the_same_fixture_and_evaluator(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-bench-") as temp:
            root = Path(temp)
            manifests = {}
            for arm in ("A", "B", "C"):
                manifests[arm] = prepare_arm(
                    ROOT,
                    "research-contradiction-001",
                    arm,
                    root / arm,
                    200_000,
                )
            self.assertEqual(
                {manifest["fixture_sha256"] for manifest in manifests.values()},
                {manifests["A"]["fixture_sha256"]},
            )
            self.assertEqual(
                {manifest["evaluator_package_sha256"] for manifest in manifests.values()},
                {manifests["A"]["evaluator_package_sha256"]},
            )
            self.assertEqual(manifests["A"]["selected_modules"], [])
            self.assertEqual(manifests["B"]["selected_modules"], [])
            self.assertGreater(len(manifests["C"]["selected_modules"]), 0)

    def test_arm_packaging_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-bench-") as temp:
            root = Path(temp)
            first = prepare_arm(
                ROOT,
                "coding-five-requirements-001",
                "C",
                root / "first",
                200_000,
            )
            second = prepare_arm(
                ROOT,
                "coding-five-requirements-001",
                "C",
                root / "second",
                200_000,
            )
            for key in (
                "prompt_sha256",
                "fixture_sha256",
                "evaluator_package_sha256",
                "selected_modules",
            ):
                self.assertEqual(first[key], second[key])

    def test_context_ceiling_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-bench-") as temp:
            with self.assertRaisesRegex(Exception, "exceeding ceiling"):
                prepare_arm(
                    ROOT,
                    "research-contradiction-001",
                    "B",
                    Path(temp) / "arm-b",
                    100,
                )


if __name__ == "__main__":
    unittest.main()
