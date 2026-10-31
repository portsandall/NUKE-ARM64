import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ci" / "summarize_android_root_diagnostics.py"
SPEC = importlib.util.spec_from_file_location("android_root_diagnostics", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AndroidRootDiagnosticSummaryTests(unittest.TestCase):
    def test_reports_configuration_build_and_deduplicated_errors(self):
        sample = """
2026-10-31T22:41:00Z ROOT_CONFIGURE_EXIT=0
2026-10-31T22:41:01Z FAILED: [code=1] CMakeFiles/KisakBlack.dir/src/DynEntity/DynEntity_client.cpp.o
2026-10-31T22:41:02Z /work/src/snd.h:498:15: error: static assertion failed
2026-10-31T22:41:03Z /work/src/snd.h:498:15: error: static assertion failed
2026-10-31T22:41:04Z /work/src/snd.h:499:7: warning: example warning
2026-10-31T22:41:05Z ROOT_BUILD_EXIT=1
"""
        summary = MODULE.render_summary(sample)
        self.assertIn("CMake configure: **PASS (exit 0)**", summary)
        self.assertIn("Full KisakBlack target build: **FAIL (exit 1)**", summary)
        self.assertIn("Compiler errors: **1**", summary)
        self.assertIn("Compiler warnings: **1**", summary)
        self.assertIn("CMakeFiles/KisakBlack.dir/src/DynEntity/DynEntity_client.cpp.o", summary)
        self.assertIn("/work/src/snd.h:498:15", summary)

    def test_reports_successful_build_without_errors(self):
        summary = MODULE.render_summary(
            "ROOT_CONFIGURE_EXIT=0\nROOT_BUILD_EXIT=0\n"
        )
        self.assertIn("Full KisakBlack target build: **PASS (exit 0)**", summary)
        self.assertIn("Compiler errors: **0**", summary)
        self.assertIn("No compiler errors were reported.", summary)

    def test_handles_missing_exit_codes(self):
        summary = MODULE.render_summary("no compiler output")
        self.assertIn("CMake configure: **not recorded**", summary)
        self.assertIn("Full KisakBlack target build: **not recorded**", summary)


if __name__ == "__main__":
    unittest.main()
