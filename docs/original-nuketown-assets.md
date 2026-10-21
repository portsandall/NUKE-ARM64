# Original Black Ops Nuketown asset pipeline

**Target:** Call of Duty: Black Ops (2010), T5 multiplayer map `mp_nuked`.
**Status:** Importer identified and scripted; no original game data has been found on the connected phone or Drive. Export has not been run with actual assets.

## Why this importer

[eithan1231/open-fastfile](https://github.com/eithan1231/open-fastfile) already provides a BO1 T5 parser and declares `mp_nuked` in `scripts/cod/maps.json`. It converts a legitimately held Windows/Steam Black Ops installation into portable geometry, textured models, collision data and metadata.

The upstream project does **not** check the original extracted world assets into its public Git repository; its `worlds/` directory only contains authoring instructions. Do not mistake a map listed in `maps.json` for downloadable geometry.

## Getting original files

Locate a legitimate **PC Black Ops 1 (32-bit)** installation, commonly the Steam directory `steamapps/common/Call of Duty Black Ops/`. It should contain at least:

```text
Call of Duty Black Ops/
  zone/Common/mp_nuked.ff
  ... other zone companions and main/ archives ...
```

The importer needs the original map zone plus companion game assets. A stand-alone `mp_nuked.ff` may not contain all textures, shared models, or data. Do **not** upload your game installation to the public NUKE-ARM64 repository.

A Steam owner can access the appropriate Windows game installation or its depots via Steam. The importer documentation lists Black Ops' original map depot as `42700 / 42702`; access remains subject to Steam ownership, download size and depot availability. No passwords, Steam session files or account tokens should be placed in GitHub issues, commits or chat.

## On an environment with the original game files

```sh
git clone https://github.com/portsandall/NUKE-ARM64.git
cd NUKE-ARM64
bash tools/export_nuketown_original.sh "/path/to/Call of Duty Black Ops"
```

The script first verifies the presence of `zone/Common/mp_nuked.ff`, then fetches the source-only upstream exporter to a separate checkout if missing. It runs `doctor --game bo1`, exports the **one** requested `mp_nuked` zone, verifies required files, and writes a SHA-256 manifest.

Expected files:

```text
build/bo1-nuketown-original/
  assets/world.glb
  assets/collision.glb
  assets/props/...
  assets/...
  export_metadata.json
  asset-manifest.sha256
```

The path is gitignored, so proprietary game data is not checked into source control accidentally.

## Android integration still required

The current Android APK uses a Java 2.5D raycaster against a hardcoded grid. It **cannot** render the imported `.glb` geometry, textures or 3D collision meshes as-is.

The next technical milestone after export is a GPU-backed glTF rendering and collision path (e.g., an Android GLES 3 renderer or embedded browser/Three.js runtime), followed by creating an installable map-only package. Do not label the existing prototype as the original Nuketown port.

### External references

- [open-fastfile importer usage](https://github.com/eithan1231/open-fastfile/blob/main/docs/cod/README.md)
- [open-fastfile export stages](https://github.com/eithan1231/open-fastfile/blob/main/docs/cod/pipeline.md)
- [Black Ops 1 map registry](https://github.com/eithan1231/open-fastfile/blob/main/scripts/cod/maps.json)
