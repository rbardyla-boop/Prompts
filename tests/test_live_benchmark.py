from __future__ import annotations

import json
import unittest

from promptctl.live_benchmark import parse_json_object, summarize_results


class LiveBenchmarkTests(unittest.TestCase):
    def test_parse_json_object_accepts_plain_and_fenced_json(self) -> None:
        plain = parse_json_object('{"verdict":"PASS"}')
        fenced = parse_json_object('```json\n{"verdict":"FAIL"}\n```')
        self.assertEqual(plain["verdict"], "PASS")
        self.assertEqual(fenced["verdict"], "FAIL")

    def test_summary_uses_paired_repetitions(self) -> None:
        rows = []
        verdicts = {
            1: {"A": "FAIL", "B": "FAIL", "C": "PASS"},
            2: {"A": "PASS", "B": "FAIL", "C": "PASS"},
            3: {"A": "PASS", "B": "PASS", "C": "PASS"},
            4: {"A": "FAIL", "B": "FAIL", "C": "PASS"},
            5: {"A": "PASS", "B": "FAIL", "C": "PASS"},
        }
        for repetition, arm_verdicts in verdicts.items():
            for arm, verdict in arm_verdicts.items():
                rows.append(
                    {
                        "candidate_id": f"{repetition}-{arm}",
                        "repetition": repetition,
                        "arm": arm,
                        "verdict": verdict,
                        "first_unmet_requirement": None,
                        "unsupported_claims": [],
                        "unrelated_changes": [],
                        "prompt_tokens": 100,
                        "completion_tokens": 20,
                        "generation_latency_seconds": 1.0,
                        "generation_attempts": 1,
                        "evaluator_attempts": 1,
                    }
                )
        summary = summarize_results(rows, seed=17)
        self.assertEqual(summary["arms"]["C"]["passes"], 5)
        self.assertEqual(summary["arms"]["B"]["passes"], 1)
        self.assertEqual(summary["paired_comparisons"]["C_minus_B"]["mean_difference"], 0.8)
        self.assertEqual(summary["development_verdict"], "DEVELOPMENT_WIN_C_OVER_B")
        self.assertFalse(summary["final_validation_eligible"])

    def test_summary_does_not_promote_tie(self) -> None:
        rows = []
        for repetition in range(1, 6):
            for arm in "ABC":
                rows.append(
                    {
                        "candidate_id": f"{repetition}-{arm}",
                        "repetition": repetition,
                        "arm": arm,
                        "verdict": "PASS",
                        "first_unmet_requirement": None,
                        "unsupported_claims": [],
                        "unrelated_changes": [],
                        "prompt_tokens": 100,
                        "completion_tokens": 20,
                        "generation_latency_seconds": 1.0,
                        "generation_attempts": 1,
                        "evaluator_attempts": 1,
                    }
                )
        summary = summarize_results(rows, seed=17)
        self.assertEqual(summary["development_verdict"], "NO_DEVELOPMENT_WIN")
        self.assertEqual(summary["paired_comparisons"]["C_minus_B"]["bootstrap_95_ci"], [0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
