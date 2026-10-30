#!/usr/bin/env python3
"""Make upstream iassert accept the four-argument diagnostic form used by phys_local.h.

The original macro accepts only an expression, while the AVL-tree call sites also
pass source file, line and diagnostic text. The engine assertion continues to
evaluate the expression and use its stringized form; the trailing metadata is
accepted for source compatibility but remains unused, matching the existing
assertion handler's behaviour. This transforms only the disposable CI checkout.
"""
from __future__ import annotations

import sys
from pathlib import Path

OLD = "#define iassert(expression)"
NEW = "#define iassert(expression, ...)"


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <upstream-assertive.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    old_count = text.count(OLD)
    new_count = text.count(NEW)

    if old_count == 2 and new_count == 0:
        text = text.replace(OLD, NEW)
    elif old_count == 0 and new_count == 2:
        pass
    else:
        raise RuntimeError(
            f"expected both DEBUG/release iassert macros once; found old={old_count}, variadic={new_count}"
        )

    if text.count(NEW) != 2:
        raise RuntimeError("both DEBUG and release iassert macros must accept variadic diagnostic arguments")

    path.write_text(text, encoding="utf-8")
    print("Verified: DEBUG and release iassert macros accept optional file/line/description arguments.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"iassert compatibility transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
