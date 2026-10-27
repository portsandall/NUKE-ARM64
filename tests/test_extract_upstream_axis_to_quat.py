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

    def test_rejects_parenthesized_out_of_range_row(self):
        function = "void AxisToQuat() { float x = mat[(3)][0]; }"
        with self.assertRaisesRegex(SystemExit, r"mat\[\(3\)\]\[0\]"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_parenthesized_out_of_range_column(self):
        function = "void AxisToQuat() { float x = mat[0][(3)]; }"
        with self.assertRaisesRegex(SystemExit, r"mat\[0\]\[\(3\)\]"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_computed_matrix_index(self):
        function = "void AxisToQuat() { float x = mat[1 + 2][0]; }"
        with self.assertRaisesRegex(SystemExit, "non-literal matrix index"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_nested_computed_row_index(self):
        function = "void AxisToQuat() { float x = mat[indices[3]][0]; }"
        with self.assertRaisesRegex(SystemExit, "non-literal matrix index"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_nested_computed_column_index(self):
        function = "void AxisToQuat() { float x = mat[0][indices[3]]; }"
        with self.assertRaisesRegex(SystemExit, "non-literal matrix index"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_single_dimension_matrix_access(self):
        function = "void AxisToQuat() { float x = mat[0]; }"
        with self.assertRaisesRegex(SystemExit, "non-2D matrix access"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_c_style_cast_flattened_matrix_index(self):
        function = "void AxisToQuat() { float x = ((const float *)mat)[9]; }"
        with self.assertRaisesRegex(SystemExit, "flattened matrix indexing"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_reinterpret_cast_flattened_matrix_index(self):
        function = "void AxisToQuat() { float x = reinterpret_cast<const float *>(mat)[9]; }"
        with self.assertRaisesRegex(SystemExit, "flattened matrix indexing"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_c_style_cast_flattened_matrix_index_trailing_const(self):
        function = "void AxisToQuat() { float x = ((float const *)mat)[9]; }"
        with self.assertRaisesRegex(SystemExit, "flattened matrix indexing"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_reinterpret_cast_flattened_matrix_index_trailing_const(self):
        function = "void AxisToQuat() { float x = reinterpret_cast<float const *>(mat)[9]; }"
        with self.assertRaisesRegex(SystemExit, "flattened matrix indexing"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_c_style_cast_alias_flattened_matrix_index(self):
        function = "void AxisToQuat() { float *flat = (float *)mat; float x = flat[9]; }"
        with self.assertRaisesRegex(SystemExit, "flattened matrix indexing through alias flat"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_reinterpret_cast_alias_flattened_matrix_index(self):
        function = "void AxisToQuat() { auto flat = reinterpret_cast<float *>(mat); float x = flat[9]; }"
        with self.assertRaisesRegex(SystemExit, "flattened matrix indexing through alias flat"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_address_of_matrix_element_alias_flattened_matrix_index(self):
        function = "void AxisToQuat() { float *flat = &mat[0][0]; float x = flat[9]; }"
        with self.assertRaisesRegex(SystemExit, "flattened matrix indexing through alias flat"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_auto_address_of_matrix_element_alias_flattened_matrix_index(self):
        function = "void AxisToQuat() { auto flat = &mat[0][0]; float x = flat[9]; }"
        with self.assertRaisesRegex(SystemExit, "flattened matrix indexing through alias flat"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_accepts_address_of_matrix_element_alias_without_flat_indexing(self):
        function = "void AxisToQuat() { float *flat = &mat[0][0]; consume(flat); }"
        EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_rejects_deferred_address_of_matrix_element_alias_flattened_index(self):
        function = "void AxisToQuat() { float *flat; flat = &mat[0][0]; float x = flat[9]; }"
        with self.assertRaisesRegex(SystemExit, "flattened matrix indexing through alias flat"):
            EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_accepts_deferred_matrix_pointer_without_flat_indexing(self):
        function = "void AxisToQuat() { float *flat; flat = &mat[0][0]; consume(flat); }"
        EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_accepts_flat_pointer_cast_alias_without_flat_indexing(self):
        function = "void AxisToQuat() { float *flat = (float *)mat; consume(flat); }"
        EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_accepts_parenthesized_valid_matrix_coordinates(self):
        function = "void AxisToQuat() { float x = mat[((2))][(1)]; }"
        EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")

    def test_accepts_valid_matrix_coordinates(self):
        function = "void AxisToQuat() { float x = mat[2][2]; }"
        EXTRACTOR.validate_matrix_indexing(function, "AxisToQuat")


if __name__ == "__main__":
    unittest.main()
