# Original Black Ops (2010) Nuketown — standalone map import

The default NUKE-ARM64 arena is an independently written **Nuketown-inspired blockout**.
It is not the original Call of Duty multiplayer level.

## Required user-owned source

The original Black Ops 1 map identifier is `mp_nuked`, and the Steam PC game
installation contains `zone/Common/mp_nuked.ff` (and localization assets).
This project does **not** ship that map or offer third-party downloads of it.

### Exporting geometry from your own game

[Scobalula's Husky](https://github.com/Scobalula/Husky) explicitly supports
**Black Ops 1** map geometry export to Wavefront OBJ. It normally requires a
running, legitimate PC installation of the game:

1. Launch your copy of Black Ops multiplayer on a Windows PC.
2. Load Nuketown (`mp_nuked`) and use Husky's export function.
3. Copy the exported `mp_nuked.obj` onto your Android phone.
4. In Termux, from the NUKE-ARM64 repository, convert the mesh:

   ```sh
   python3 tools/obj_to_nmap.py /sdcard/Download/mp_nuked.obj /sdcard/Download/mp_nuked.nmap
   ```

5. In the NUKE-ARM64 app select **IMPORT EXPORTED NUKETOWN .NMAP**, choose that
   file, then explore the geometry using the Android OpenGL ES 2 renderer.

The converter retains vertices and faces and rejects malformed indices. It
accepts positive and negative Wavefront OBJ indices. It does not include
textures, materials, scripts, the separately placed xmodels or collision
brushes. It does not attempt to parse `.ff` directly.

## Present Android capability

- First-person free-fly *geometry preview* with look and move touch controls.
- A GLES2 mesh renderer (untextured) and local NMAP file selection.
- A separate offline playable blockout using simplified collision/bots/hitscan.
- No original BO1 weapons, materials, exact physics, player spawns, world
  collision, or multiplayer server.
- The viewer caps imported NMAP files at 80 MiB and renders at most about
  180,000 sampled triangles per frame to control phone memory/GPU load.
  It will **not** display an entire complex map faithfully if that limit
  is exceeded. OBJ coordinates/scales are preserved by default.

### Why we cannot include the exact original map yet

The original game files or a user-owned geometry export have **not** been
provided to this project. The original game's world geometry cannot be
reconstructed from the name `mp_nuked` alone.

OpenAssetTools can inspect many Black Ops fastfile assets, but at the time
of this writing its T5 `GfxWorld` and `clipMap_t` dumping are not supported
in its official supported-asset matrix. This is why the first import path uses
Husky's BSP geometry export. The normal Windows game/extractor dependency
also means that a phone-only workflow cannot currently perform that export.

Next implementation milestones after importing a real OBJ are streaming
meshes, materials/texture mapping, static model placement, spatial collision
acceleration, grounded movement, weapons, and game-mode/multiplayer logic.

No copyrighted Black Ops game assets should be committed to the public
repository or incorporated into a distributed APK without appropriate rights.
