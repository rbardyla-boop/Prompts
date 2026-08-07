from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from promptctl.security import (
    REDACTION,
    SecurityError,
    authorize_closed_action,
    redact_value,
    resolve_workspace_path,
)


class SecurityTests(unittest.TestCase):
    def test_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-security-") as temp:
            workspace = Path(temp)
            with self.assertRaisesRegex(SecurityError, "traversal"):
                resolve_workspace_path(workspace, "../outside.txt")

    def test_absolute_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-security-") as temp:
            workspace = Path(temp)
            with self.assertRaisesRegex(SecurityError, "absolute"):
                resolve_workspace_path(workspace, "/tmp/outside.txt")

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink support unavailable")
    def test_symlink_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-security-") as temp:
            root = Path(temp)
            workspace = root / "workspace"
            outside = root / "outside"
            workspace.mkdir()
            outside.mkdir()
            (workspace / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(SecurityError):
                resolve_workspace_path(workspace, "link/secret.txt")

    def test_safe_relative_path_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompts-v2-security-") as temp:
            workspace = Path(temp)
            (workspace / "artifacts").mkdir()
            result = resolve_workspace_path(workspace, "artifacts/result.json")
            self.assertEqual(result, workspace / "artifacts" / "result.json")

    def test_secret_redaction_is_recursive(self) -> None:
        value = {
            "authorization": "Bearer top-secret-token",
            "nested": ["top-secret-token", {"value": "prefix-top-secret-token-suffix"}],
        }
        redacted = redact_value(value, ["top-secret-token"])
        self.assertNotIn("top-secret-token", repr(redacted))
        self.assertIn(REDACTION, repr(redacted))

    def test_forbidden_action_is_rejected(self) -> None:
        with self.assertRaisesRegex(SecurityError, "forbidden action"):
            authorize_closed_action(
                "production_deploy",
                ["read_repository", "run_tests"],
                ["production_deploy"],
            )

    def test_unlisted_action_is_denied(self) -> None:
        with self.assertRaisesRegex(SecurityError, "unlisted action"):
            authorize_closed_action(
                "arbitrary_network",
                ["read_repository", "run_tests"],
                ["production_deploy"],
            )

    def test_allowed_action_passes(self) -> None:
        authorize_closed_action(
            "run_tests",
            ["read_repository", "run_tests"],
            ["production_deploy"],
        )


if __name__ == "__main__":
    unittest.main()
