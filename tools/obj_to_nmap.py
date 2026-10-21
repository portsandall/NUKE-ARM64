#!/usr/bin/env python3
"""Convert a user-exported Black Ops/Husky Wavefront OBJ into a compact NMAP mesh.

This tool never ships, fetches, or extracts proprietary Call of Duty assets.
It consumes geometry the user exports from their own installation.

NMAP v1 little-endian layout:
  4s magic ('NMAP'); uint32 version (=1); uint32 vertex_count;
  uint32 triangle_count; float32 bounds[6] (xmin,ymin,zmin,xmax,ymax,zmax);
  vertex_count * float32 xyz;
  triangle_count * uint32 index[3].
Textures, materials, collision brushes, map entities and models are NOT included.
"""
import argparse
import math
import os
import struct
import tempfile

MAGIC = b"NMAP"
VERSION = 1
MAX_VERTICES = 2_000_000
MAX_TRIANGLES = 4_000_000


def parse_obj(path):
    vertices = []
    triangles = []
    with open(path, "r", encoding="utf-8-sig", errors="replace") as stream:
        for lineno, line in enumerate(stream, 1):
            # OBJ comments may occur after a token.
            words = line.split("#", 1)[0].split()
            if not words:
                continue
            if words[0] == "v":
                if len(words) < 4:
                    raise ValueError(f"line {lineno}: malformed vertex")
                xyz = tuple(float(v) for v in words[1:4])
                if not all(math.isfinite(v) for v in xyz):
                    raise ValueError(f"line {lineno}: non-finite coordinate")
                vertices.append(xyz)
                if len(vertices) > MAX_VERTICES:
                    raise ValueError("vertex count exceeds safety limit")
            elif words[0] == "f":
                if len(words) < 4:
                    raise ValueError(f"line {lineno}: face needs >=3 vertices")
                face = []
                for word in words[1:]:
                    item = word.split("/", 1)[0]
                    if not item:
                        raise ValueError(f"line {lineno}: missing vertex index")
                    number = int(item)
                    if number == 0:
                        raise ValueError(f"line {lineno}: OBJ indices are 1-based")
                    index = number - 1 if number > 0 else len(vertices) + number
                    if not (0 <= index < len(vertices)):
                        raise ValueError(f"line {lineno}: out-of-range vertex {number}")
                    face.append(index)
                # OBJ polygon fan triangulation. Exported BSP faces are generally convex.
                for j in range(1, len(face) - 1):
                    a, b, c = face[0], face[j], face[j + 1]
                    if a != b and b != c and a != c:
                        triangles.append((a, b, c))
                        if len(triangles) > MAX_TRIANGLES:
                            raise ValueError("triangle count exceeds safety limit")
    if not vertices or not triangles:
        raise ValueError("OBJ does not contain both vertices and faces")
    return vertices, triangles


def convert(input_path, output_path, scale=1.0):
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("scale must be positive and finite")
    vertices, triangles = parse_obj(input_path)
    transformed = [(x * scale, y * scale, z * scale) for x, y, z in vertices]
    if not all(math.isfinite(q) and abs(q) <= 3.4e38 for v in transformed for q in v):
        raise ValueError("scaled vertex coordinate exceeds float32 range")
    mins = tuple(min(p[i] for p in transformed) for i in range(3))
    maxs = tuple(max(p[i] for p in transformed) for i in range(3))
    bounds = mins + maxs
    dest = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".nmap_", dir=os.path.dirname(dest))
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(struct.pack("<4sIII6f", MAGIC, VERSION, len(transformed),
                                  len(triangles), *bounds))
            for vertex in transformed:
                out.write(struct.pack("<3f", *vertex))
            for face in triangles:
                out.write(struct.pack("<3I", *face))
        os.replace(temporary, dest)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"vertices": len(transformed), "triangles": len(triangles),
            "bounds": bounds, "bytes": os.stat(dest).st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("obj", help="OBJ exported by Husky from your own BO1 game")
    parser.add_argument("nmap", help="output standalone map geometry")
    parser.add_argument("--scale", type=float, default=1.0,
                        help="uniform scale: default 1.0 (do not guess units)")
    args = parser.parse_args()
    result = convert(args.obj, args.nmap, args.scale)
    print("NMAP geometry exported:", result)
    print("Note: textures, collision brushes and original game physics not exported.")


if __name__ == "__main__":
    main()
