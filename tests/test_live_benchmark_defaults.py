from __future__ import annotations

import unittest

from promptctl.live_benchmark import parser


class LiveBenchmarkDefaultTests(unittest.TestCase):
    def test_copilot_defaults_do_not_assume_model_entitlement(self) -> None:
        args = parser().parse_args(
            [
                "--output",
                "/tmp/out",
                "--randomization-seed",
                "1",
            ]
        )
        self.assertEqual(args.generator_model, "auto")
        self.assertEqual(args.evaluator_model, "auto")
        self.assertGreaterEqual(args.generation_max_ai_credits, 30)
        self.assertGreaterEqual(args.evaluator_max_ai_credits, 30)


if __name__ == "__main__":
    unittest.main()
