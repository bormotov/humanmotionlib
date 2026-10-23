"""Regression tests for the host interpreter and test-selection contract."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import check_host


class CheckEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_rejects_wrong_interpreter_and_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.12,<3.13"\n')
            (root / ".python-version").write_text("3.12\n")
            errors = check_host.check_environment(root, (3, 12, 9), "cpython")
        self.assertTrue(any("requires-python" in error for error in errors))
        self.assertTrue(any(".python-version" in error for error in errors))
        self.assertTrue(any("actual interpreter" in error for error in errors))

    def test_rejects_non_cpython_even_with_supported_minor(self):
        errors = check_host.check_environment(self.root, (3, 14, 1), "pypy")
        self.assertTrue(any("actual interpreter" in error for error in errors))


class HostSelectionTests(unittest.TestCase):
    def test_only_two_backend_modules_are_classified(self):
        backend = unittest.FunctionTestCase(lambda: None, description="backend")
        backend.id = lambda: "tests.test_blender_backend.SomeTest.test_build"
        fault = unittest.FunctionTestCase(lambda: None, description="fault")
        fault.id = lambda: "tests.test_pipeline_faults.SomeTest.test_fault"
        synthetic = unittest.FunctionTestCase(lambda: None, description="synthetic")
        synthetic.id = lambda: "tests.test_review_pack_supervision.SomeTest.test_synthetic"
        self.assertEqual(check_host.is_backend_excluded(backend), "tests.test_blender_backend")
        self.assertEqual(check_host.is_backend_excluded(fault), "tests.test_pipeline_faults")
        self.assertIsNone(check_host.is_backend_excluded(synthetic))
        self.assertEqual(set(check_host.BACKEND_EXCLUSIONS), {
            "tests.test_blender_backend", "tests.test_pipeline_faults"
        })

    def test_discovery_keeps_synthetic_modules_and_excludes_only_real_backend(self):
        root = Path(__file__).resolve().parents[1]
        suite, exclusions, errors = check_host.discover_host_tests(root)
        identifiers = [test.id() for test in check_host.iter_cases(suite)]
        self.assertEqual(errors, [])
        self.assertGreater(len(identifiers), 0)
        self.assertTrue(any(identifier.startswith("test_runtime.") for identifier in identifiers))
        self.assertTrue(any(identifier.startswith("test_run_blender.") for identifier in identifiers))
        self.assertTrue(any(identifier.startswith("test_review_pack_supervision.") for identifier in identifiers))
        self.assertTrue(any(identifier.startswith("test_check_host.") for identifier in identifiers))
        self.assertFalse(any(check_host.is_backend_excluded(test) for test in check_host.iter_cases(suite)))
        self.assertEqual(set(exclusions), set(check_host.BACKEND_EXCLUSIONS))
        self.assertGreater(exclusions["tests.test_blender_backend"], 0)
        self.assertGreater(exclusions["tests.test_pipeline_faults"], 0)

    def test_discovery_errors_fail_and_are_reported(self):
        output = StringIO()
        status = check_host.run_selected_tests(unittest.TestSuite(), {}, ["broken test import"], output)
        self.assertEqual(status, 1)
        self.assertIn("Discovery error: broken test import", output.getvalue())

    def test_empty_selection_fails(self):
        output = StringIO()
        status = check_host.run_selected_tests(unittest.TestSuite(), {}, [], output)
        self.assertEqual(status, 1)
        self.assertIn("empty", output.getvalue())

    def test_test_failure_produces_nonzero_status(self):
        class FailingTest(unittest.TestCase):
            def runTest(self):
                self.fail("expected regression failure")

        output = StringIO()
        status = check_host.run_selected_tests(unittest.TestSuite([FailingTest()]), {}, [], output)
        self.assertEqual(status, 1)
        self.assertIn("FAILED", output.getvalue())


if __name__ == "__main__":
    unittest.main()
