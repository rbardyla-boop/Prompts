from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # pragma: no cover - CI installs the test extra.
    Draft202012Validator = None
    FormatChecker = None

from promptctl.harness import initialize_project, submit_completion, transition


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(Draft202012Validator is None, "jsonschema test dependency is not installed")
class SchemaTests(unittest.TestCase):
    def validator(self, name: str) -> Draft202012Validator:
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator(schema, format_checker=FormatChecker())

    def assert_valid(self, validator: Draft202012Validator, value: object) -> None:
        errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
        if errors:
            self.fail(errors[0].message)

    def test_module_catalog_entries_validate(self) -> None:
        catalog = json.loads(
            (ROOT / "modules/legacy-extracted/MODULE_CATALOG.json").read_text(encoding="utf-8")
        )
        validator = self.validator("module.schema.json")
        self.assertEqual(len(catalog["modules"]), 24)
        for module in catalog["modules"]:
            self.assert_valid(validator, module)

    def test_all_task_packs_validate(self) -> None:
        validator = self.validator("taskpack.schema.json")
        paths = sorted((ROOT / "taskpacks").glob("*.json"))
        self.assertEqual(len(paths), 7)
        for path in paths:
            self.assert_valid(validator, json.loads(path.read_text(encoding="utf-8")))

    def test_generated_contract_state_trace_and_receipt_validate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-schema-") as temp:
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
                {"verdict": "FAIL", "evidence": ["Requirement 5 is absent"]},
                "PASS",
            )

            contract = json.loads(
                (workspace / "agent/contract.json").read_text(encoding="utf-8")
            )
            state = json.loads(
                (workspace / "agent/state.json").read_text(encoding="utf-8")
            )
            traces = [
                json.loads(line)
                for line in (workspace / "agent/traces/events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]

            self.assert_valid(self.validator("contract.schema.json"), contract)
            self.assert_valid(self.validator("state.schema.json"), state)
            trace_validator = self.validator("trace.schema.json")
            for event in traces:
                self.assert_valid(trace_validator, event)
            self.assert_valid(self.validator("receipt.schema.json"), receipt)


if __name__ == "__main__":
    unittest.main()
