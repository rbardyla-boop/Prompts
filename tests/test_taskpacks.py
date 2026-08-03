from __future__ import annotations

import copy
import unittest
from pathlib import Path

from promptctl.harness import load_taskpack
from promptctl.kernel import TASK_TAGS, load_json, select_modules


ROOT = Path(__file__).resolve().parents[1]
PACK_IDS = [
    "deep-research",
    "software-build",
    "book-production",
    "browser-game",
    "factual-audit",
    "adversarial-artifact-audit",
    "harness-terminal-test",
]


class TaskPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json(ROOT / "modules/legacy-extracted/MODULE_CATALOG.json")
        self.graph = load_json(ROOT / "RULE_GRAPH.json")

    def select_pack(self, pack_id: str) -> dict:
        pack = load_taskpack(ROOT, pack_id)
        task_type = pack["task_type"]
        original = copy.copy(TASK_TAGS[task_type])
        TASK_TAGS[task_type] = set(original) | set(pack.get("extra_task_tags", []))
        try:
            return select_modules(
                self.catalog,
                self.graph,
                task_type,
                include=pack["module_ids"],
                allow_profile_specific=bool(pack.get("allow_profile_specific", False)),
            )
        finally:
            TASK_TAGS[task_type] = original

    def test_all_expected_task_packs_load(self) -> None:
        loaded = [load_taskpack(ROOT, pack_id)["taskpack_id"] for pack_id in PACK_IDS]
        self.assertEqual(loaded, PACK_IDS)

    def test_deep_research_selection_is_explainable(self) -> None:
        selection = self.select_pack("deep-research")
        selected = selection["selected_modules"]
        reasons = selection["selection_reasons"]
        self.assertIn("research.competing-view-search", selected)
        self.assertIn("research.curiosity-lens", selected)
        self.assertIn("evidence.proxy-triangulation", selected)
        self.assertEqual(set(selected), set(reasons))
        self.assertNotIn("evidence.regime-change-gating", selected)

    def test_browser_game_combines_software_and_creative_modules(self) -> None:
        selection = self.select_pack("browser-game")
        selected = set(selection["selected_modules"])
        self.assertIn("development.secure-defaults", selected)
        self.assertIn("creative.forced-remix", selected)
        self.assertIn("creative.influence-map", selected)
        self.assertIn("workflow.minimum-viable-experiment", selected)


if __name__ == "__main__":
    unittest.main()
