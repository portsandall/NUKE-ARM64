"""Regression tests for importing geometry legitimately exported from a game installation."""
import os
import struct
import tempfile
import unittest
from tools.obj_to_nmap import convert, parse_obj


class ObjToNmapTests(unittest.TestCase):
    def test_quad_and_negative_indices(self):
        with tempfile.TemporaryDirectory() as temp:
            src = os.path.join(temp, "sample.obj")
            dst = os.path.join(temp, "sample.nmap")
            with open(src, "w", encoding="utf-8") as f:
                f.write("v 0 0 0\nv 2 0 0\nv 2 2 0\nv 0 2 0\n"
                        "f -4/-4 -3/-3 -2/-2 -1/-1\n")
            result = convert(src, dst, scale=0.5)
            self.assertEqual(result["vertices"], 4)
            self.assertEqual(result["triangles"], 2)
            self.assertEqual(result["bounds"], (0, 0, 0, 1, 1, 0))
            with open(dst, "rb") as f:
                data = f.read()
            magic, version, nv, nt, *bounds = struct.unpack_from("<4sIII6f", data)
            self.assertEqual((magic, version, nv, nt), (b"NMAP", 1, 4, 2))
            self.assertEqual(tuple(bounds), (0, 0, 0, 1, 1, 0))
            self.assertEqual(len(data), 40 + 4 * 12 + 2 * 12)
            self.assertEqual(struct.unpack_from("<3I", data, 40 + 4 * 12),
                             (0, 1, 2))

    def test_out_of_range_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            src = os.path.join(temp, "broken.obj")
            with open(src, "w", encoding="utf-8") as f:
                f.write("v 0 0 0\nf 1 2 3\n")
            with self.assertRaisesRegex(ValueError, "out-of-range"):
                parse_obj(src)

    def test_zero_scale_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            src = os.path.join(temp, "basic.obj")
            with open(src, "w", encoding="utf-8") as f:
                f.write("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            with self.assertRaisesRegex(ValueError, "scale"):
                convert(src, os.path.join(temp, "bad.nmap"), 0)


if __name__ == "__main__":
    unittest.main()
