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
            "ROOT_CONFIGURE_EXIT=0\\nROOT_BUILD_EXIT=0\\n"
        )
        self.assertIn("Full KisakBlack target build: **PASS (exit 0)**", summary)
        self.assertIn("Compiler errors: **0**", summary)
        self.assertIn("No compiler errors were reported.", summary)

    def test_handles_missing_exit_codes(self):
        summary = MODULE.render_summary("no compiler output")
        self.assertIn("CMake configure: **not recorded**", summary)
        self.assertIn("Full KisakBlack target build: **not recorded**", summary)

    def test_deduplicates_repeated_timestamped_diagnostics_from_ci_log(self):
        sample = """\\
2026-11-11T00:11:28Z ROOT_CONFIGURE_EXIT=0
2026-11-11T00:11:28Z FAILED: [code=1] CMakeFiles/KisakBlack.dir/src/DynEntity/DynEntity_client.cpp.o
2026-11-11T00:11:29Z /work/src/DynEntity/DynEntity_client.cpp:1306:14: error: cast from pointer to smaller type 'int' loses information
2026-11-11T00:11:29Z /work/src/physics/phys_gjk.h:613:19: warning: example warning
2026-11-11T00:11:30Z ROOT_BUILD_EXIT=1
2026-11-11T00:11:31Z /work/src/DynEntity/DynEntity_client.cpp:1306:14: error: cast from pointer to smaller type 'int' loses information
2026-11-11T00:11:31Z /work/src/physics/phys_gjk.h:613:19: warning: example warning
2026-11-11T00:11:32Z ROOT_BUILD_EXIT=1
"""
        summary = MODULE.render_summary(sample)
        self.assertIn("CMake configure: **PASS (exit 0)**", summary)
        self.assertIn("Full KisakBlack target build: **FAIL (exit 1)**", summary)
        self.assertIn("Compiler errors: **1**", summary)
        self.assertIn("Compiler warnings: **1**", summary)
        self.assertEqual(summary.count("CMakeFiles/KisakBlack.dir/src/DynEntity/DynEntity_client.cpp.o"), 1)


if __name__ == "__main__":
    unittest.main()
