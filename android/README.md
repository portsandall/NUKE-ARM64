# Android APK bootstrap (not playable)

This Android app packages the real KisakBlack Base64 utility as part of an Android arm64-v8a JNI shared library. It opens a diagnostic Activity. It does not render Nuketown, load game assets, provide multiplayer, or implement Black Ops gameplay.

Build from the `android/` directory with Android SDK, NDK and CMake installed:

`gradle :app:assembleDebug -PNUKE_KISAKBLACK_ROOT=/path/to/KisakBlack`

Gradle's CMake externalNativeBuild must receive the upstream source path from `NUKE_KISAKBLACK_ROOT`; the CI passes it using a generated CMake arguments value. Keep this implementation separate from the actual engine port.
