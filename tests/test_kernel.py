from __future__ import annotations

import copy
import unittest
from pathlib import Path

from promptctl.kernel import (
    KernelError,
    compose_prompt,
    load_json,
    module_can_authorize_terminal,
    select_modules,
    validate_catalog,
    validate_graph,
    validate_repository,
)


ROOT = Path(__file__).resolve().parents[1]


class KernelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json(ROOT / "modules/legacy-extracted/MODULE_CATALOG.json")
        self.graph = load_json(ROOT / "RULE_GRAPH.json")

    def test_repository_validates(self) -> None:
        report = validate_repository(ROOT)
        self.assertEqual(report["result"], "PASS")
        self.assertEqual(report["catalog"]["module_count"], 24)
        self.assertTrue(report["graph"]["requires_acyclic"])

    def test_selection_is_deterministic(self) -> None:
        first = select_modules(self.catalog, self.graph, "research")
        second = select_modules(self.catalog, self.graph, "research")
        self.assertEqual(first, second)

    def test_profile_specific_does_not_auto_load(self) -> None:
        selection = select_modules(self.catalog, self.graph, "research")
        selected = set(selection["selected_modules"])
        for module in self.catalog["modules"]:
            if module["status"] == "PROFILE_SPECIFIC":
                self.assertNotIn(module["module_id"], selected)

    def test_profile_specific_requires_explicit_authorization(self) -> None:
        with self.assertRaises(KernelError):
            select_modules(
                self.catalog,
                self.graph,
                "time-series",
                include=["evidence.regime-change-gating"],
            )

    def test_explicit_profile_module_loads_when_authorized(self) -> None:
        selection = select_modules(
            self.catalog,
            self.graph,
            "time-series",
            include=["evidence.regime-change-gating"],
            allow_profile_specific=True,
        )
        self.assertIn("evidence.regime-change-gating", selection["selected_modules"])
        self.assertIn("evidence.metric-integrity", selection["selected_modules"])

    def test_unknown_module_is_rejected(self) -> None:
        with self.assertRaises(KernelError):
            select_modules(
                self.catalog,
                self.graph,
                "software",
                include=["unknown.module"],
            )

    def test_dependency_cycle_is_rejected(self) -> None:
        graph = copy.deepcopy(self.graph)
        graph["edges"].append(
            {
                "from": "governance.success-criteria-lock",
                "to": "workflow.gated-phase-control",
                "type": "REQUIRES",
            }
        )
        with self.assertRaisesRegex(KernelError, "dependency cycle"):
            validate_graph(graph, self.catalog)

    def test_profile_specific_default_is_rejected(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        target = next(
            item for item in catalog["modules"] if item["status"] == "PROFILE_SPECIFIC"
        )
        target["default_include"] = True
        with self.assertRaisesRegex(KernelError, "cannot default-load"):
            validate_catalog(catalog)

    def test_heuristic_default_is_rejected(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        target = next(
            item for item in catalog["modules"] if item["classification"] == "HEURISTIC"
        )
        target["default_include"] = True
        with self.assertRaisesRegex(KernelError, "HEURISTIC"):
            validate_catalog(catalog)

    def test_contaminated_tail_is_rejected(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["modules"][0]["notes"] = ["Sure, I can help you with that"]
        with self.assertRaisesRegex(KernelError, "quarantined"):
            validate_catalog(catalog)

    def test_composer_never_reads_legacy_body(self) -> None:
        selection = select_modules(self.catalog, self.graph, "research")
        result = compose_prompt("Audit the evidence.", selection, self.catalog)
        self.assertNotIn("Sure, I can help you with that", result)
        self.assertIn("PROMPTS V2 COMPOSED TASK", result)

    def test_modules_cannot_authorize_terminal_state(self) -> None:
        for module in self.catalog["modules"]:
            self.assertFalse(module_can_authorize_terminal(module))

    def test_catalog_count_mismatch_is_rejected(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["module_count"] = 999
        with self.assertRaisesRegex(KernelError, "module_count"):
            validate_catalog(catalog)

    def test_graph_unknown_node_is_rejected(self) -> None:
        graph = copy.deepcopy(self.graph)
        graph["edges"].append(
            {
                "from": "unknown.module",
                "to": graph["nodes"][0]["id"],
                "type": "REQUIRES",
            }
        )
        with self.assertRaisesRegex(KernelError, "unknown node"):
            validate_graph(graph, self.catalog)


if __name__ == "__main__":
    unittest.main()
