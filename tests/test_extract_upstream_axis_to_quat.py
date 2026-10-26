"""Regression tests for the upstream quaternion extractor's matrix bounds guard."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).with_name("extract_upstream_axis_to_quat.py")
SPEC = importlib.util.spec_from_file_location("axis_to_quat_extractor", SCRIPT)
EXTRACTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXTRACTOR)


class MatrixIndexValidationTests(unittest.TestCase):
    def test_rejects_flattened_matrix_index_three(self):
        function = "void AxisToQuat() { float x = (*mat)[3]; }"
        with self.assertRaisesRegex(SystemExit, "flattened matrix indexing"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_flattened_index_above_old_guard_range(self):
        function = "void AxisToQuat() { float x = (*mat)[12]; }"
        with self.assertRaisesRegex(SystemExit, "flattened matrix indexing"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_out_of_range_row(self):
        function = "void AxisToQuat() { float x = mat[3][0]; }"
        with self.assertRaisesRegex(SystemExit, r"mat\[3\]\[0\]"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_out_of_range_column(self):
        function = "void AxisToQuat() { float x = mat[0][3]; }"
        with self.assertRaisesRegex(SystemExit, r"mat\[0\]\[3\]"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_hex_flattened_matrix_index(self):
        function = "void AxisToQuat() { float x = (*mat)[0xC]; }"
        with self.assertRaisesRegex(SystemExit, "flattened matrix indexing"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_hex_out_of_range_row_with_suffix(self):
        function = "void AxisToQuat() { float x = mat[0x3u][0]; }"
        with self.assertRaisesRegex(SystemExit, r"mat\[0x3u\]\[0\]"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_negative_column_index(self):
        function = "void AxisToQuat() { float x = mat[0][-1]; }"
        with self.assertRaisesRegex(SystemExit, r"mat\[0\]\[-1\]"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_accepts_valid_matrix_coordinates(self):
        function = "void AxisToQuat() { float x = mat[2][2]; }"
        EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")


if __name__ == "__main__":
    unittest.main()
