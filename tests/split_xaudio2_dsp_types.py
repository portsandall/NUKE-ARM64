#!/usr/bin/env python3
"""Split platform-neutral sound DSP layouts away from the XAudio2/XAPO header.

The generic snd_dsp.h is included through snd.h by networking/game headers.
It must not pull Windows XAPOBase.h into non-Windows translation units.
This transform edits only the disposable, pinned KisakBlack checkout.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

POD_STRUCTS = (
    "snd_dsp_master_params",
    "snd_dsp_dynamo_state",
    "snd_dsp_master_no_voice_state",
    "snd_dsp_biquad_state",
    "snd_dsp_squelch_state",
    "snd_dsp_futz_state",
    "snd_dsp_master_no_voice_params",
    "snd_dsp_biquad_coef",
    "snd_dsp_master_state",
    "snd_dsp_squelch_param",
    "snd_dsp_futz_param",
    "snd_dsp_source_params",
    "snd_dsp_source_state",
)


def extract_layouts(source: str) -> tuple[str, str]:
    lines = source.splitlines(keepends=True)
    remaining = list(lines)
    layouts: list[str] = []

    for name in POD_STRUCTS:
        declaration = re.compile(
            rf"^struct\s+(?:__declspec\(align\(128\)\)\s+)?{re.escape(name)}\b"
        )
        matches = [index for index, line in enumerate(remaining) if declaration.match(line)]
        if len(matches) != 1:
            raise RuntimeError(f"expected one declaration of {name}; found {len(matches)}")

        start = matches[0]
        end = next(
            (index for index in range(start + 1, len(remaining))
             if remaining[index].strip() == "};"),
            None,
        )
        if end is None:
            raise RuntimeError(f"could not find the closing brace for {name}")

        block = "".join(remaining[start : end + 1]).strip()
        if name == "snd_dsp_dynamo_state":
            old = "struct __declspec(align(128)) snd_dsp_dynamo_state"
            new = "struct alignas(128) snd_dsp_dynamo_state"
            if block.count(old) != 1:
                raise RuntimeError("expected one 128-byte aligned dynamo state declaration")
            block = block.replace(old, new, 1)

        layouts.append(block)
        del remaining[start : end + 1]

    return "\n\n".join(layouts) + "\n", "".join(remaining)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <kisakblack-source-root>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1])
    sound = root / "src" / "sound"
    xaudio_path = sound / "snd_driver_xaudio2_dsp.h"
    dsp_path = sound / "snd_dsp.h"
    types_path = sound / "snd_dsp_types.h"

    if types_path.exists():
        raise RuntimeError(f"refusing to overwrite existing file: {types_path}")

    xaudio_source = xaudio_path.read_text()
    dsp_source = dsp_path.read_text()

    if xaudio_source.count('#include "snd_radverb.h"') != 1:
        raise RuntimeError("expected one snd_radverb.h include in the XAudio2 DSP header")
    if dsp_source.count('#include "snd_driver_xaudio2_dsp.h"') != 1:
        raise RuntimeError("expected one XAudio2 DSP include in the generic DSP header")

    layouts, xaudio_remainder = extract_layouts(xaudio_source)
    new_types = (
        "#pragma once\n\n"
        "// Platform-neutral DSP parameter/state layouts shared by sound backends.\n"
        "// Keep these layouts independent of XAudio2 and Windows XAPO interfaces.\n\n"
        + layouts
    )

    new_xaudio = xaudio_remainder.replace(
        '#include "snd_radverb.h"',
        '#include "snd_radverb.h"\n#include "snd_dsp_types.h"',
        1,
    )
    new_dsp = dsp_source.replace(
        '#include "snd_driver_xaudio2_dsp.h"',
        '#include "snd_dsp_types.h"',
        1,
    )

    if "XAPOBase.h" in new_dsp or "snd_driver_xaudio2_dsp.h" in new_dsp:
        raise RuntimeError("generic snd_dsp.h still depends on the XAudio2/XAPO header")
    if '#include "snd_dsp_types.h"' not in new_xaudio:
        raise RuntimeError("XAudio2 DSP declarations do not include the extracted layouts")

    # Write only after all source-shape and replacement checks have passed.
    types_path.write_text(new_types)
    xaudio_path.write_text(new_xaudio)
    dsp_path.write_text(new_dsp)
    print(
        "Separated 13 platform-neutral DSP layouts into snd_dsp_types.h; "
        "generic snd_dsp.h no longer includes XAudio2/XAPO declarations."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"sound DSP header split failed: {error}", file=sys.stderr)
        raise SystemExit(1)
