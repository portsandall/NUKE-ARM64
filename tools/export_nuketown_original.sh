#!/usr/bin/env bash
# Extract BO1 Nuketown map into glTF/collision using the independent open-fastfile importer.
# No copyrighted Black Ops data is downloaded or included by this helper.
set -euo pipefail

usage() {
  cat >&2 <<'TEXT'
Usage: bash tools/export_nuketown_original.sh /path/to/owned/BlackOps [output_directory]

Reads original Call of Duty: Black Ops (2010) PC game files (32-bit T5).
Required: <game>/zone/Common/mp_nuked.ff plus its companion game data.
Produces: assets/world.glb, assets/collision.glb, props/textures, and metadata
          in build/bo1-nuketown-original/ unless an output directory is given.

This does not download the game, and the current NUKE-ARM64 raycaster cannot
render the resulting glTF map until a 3D asset renderer is integrated.
TEXT
}
if [[ $# -lt 1 || $# -gt 2 || "$1" == '-h' || "$1" == '--help' ]]; then
  usage
  [[ "${1:-}" == '-h' || "${1:-}" == '--help' ]] && exit 0
  exit 2
fi

GAME_DIR="$(realpath "$1")"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${2:-$REPO_ROOT/build/bo1-nuketown-original}"
mkdir -p "$(dirname "$OUT")"
OUT="$(realpath -m "$OUT")"

MAP_ZONE=''
for candidate in "$GAME_DIR/zone/Common/mp_nuked.ff" "$GAME_DIR/zone/common/mp_nuked.ff"; do
  if [[ -f "$candidate" ]]; then MAP_ZONE="$candidate"; break; fi
done
if [[ -z "$MAP_ZONE" ]]; then
  printf 'ERROR: mp_nuked.ff was not found under %s/zone/Common/\n' "$GAME_DIR" >&2
  printf 'Provide a local, legitimately obtained Black Ops PC installation. No map data was downloaded.\n' >&2
  exit 3
fi

IMPORTER_DIR="${NUKE_COD_IMPORTER_ROOT:-${HOME}/projects/open-fastfile-importer}"
if [[ ! -f "$IMPORTER_DIR/scripts/cod/__main__.py" ]]; then
  echo "Fetching source-only CoD map exporter to $IMPORTER_DIR"
  command -v git >/dev/null || { echo 'ERROR: git is required' >&2; exit 4; }
  mkdir -p "$(dirname "$IMPORTER_DIR")"
  git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/eithan1231/open-fastfile.git "$IMPORTER_DIR"
  git -C "$IMPORTER_DIR" sparse-checkout set scripts/cod docs/cod
fi

if [[ ! -f "$IMPORTER_DIR/scripts/cod/requirements.txt" ]]; then
  echo 'ERROR: importer checkout is incomplete' >&2; exit 4
fi

PYTHON="${NUKE_PYTHON:-python3}"
command -v "$PYTHON" >/dev/null || { echo "ERROR: $PYTHON not installed" >&2; exit 4; }
VENV="$IMPORTER_DIR/.venv"
if [[ ! -x "$VENV/bin/python" ]]; then "$PYTHON" -m venv "$VENV"; fi
if ! "$VENV/bin/python" -c 'import PIL' 2>/dev/null; then
  "$VENV/bin/python" -m pip install -r "$IMPORTER_DIR/scripts/cod/requirements.txt"
fi

cd "$IMPORTER_DIR"
echo "Inspecting Black Ops installation at: $GAME_DIR"
"$VENV/bin/python" -m scripts.cod doctor --game bo1 --game-dir "bo1=$GAME_DIR"
echo "Exporting original mp_nuked into: $OUT"
"$VENV/bin/python" -m scripts.cod export mp_nuked --game bo1 \
  --game-dir "bo1=$GAME_DIR" \
  --world "$(basename "$OUT")" --worlds "$(dirname "$OUT")"

for required in assets/world.glb assets/collision.glb; do
  if [[ ! -s "$OUT/$required" ]]; then
    echo "ERROR: Export completed without a nonempty $required" >&2
    exit 5
  fi
done
(
  cd "$OUT"
  find assets -type f -print0 | sort -z | xargs -0 -r sha256sum > asset-manifest.sha256
)
echo 'Verified export outputs:'
ls -lh "$OUT/assets/world.glb" "$OUT/assets/collision.glb"
echo "Manifest: $OUT/asset-manifest.sha256"
