cmake_minimum_required(VERSION 3.20)
project(NUKE_ARM64 VERSION 0.1.0 LANGUAGES C CXX)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_executable(nuke-platform-probe src/main.c)
if(CMAKE_C_COMPILER_ID MATCHES "Clang|GNU")
  target_compile_options(nuke-platform-probe PRIVATE -Wall -Wextra -Wconversion -Werror)
endif()
# Standalone portability shim test. Does not yet compile the upstream game engine.
include(CTest)

# Optional integration target for one real, pinned KisakBlack translation unit.
# CI supplies the upstream checkout after applying the portability patches.
option(NUKE_BUILD_UPSTREAM_BASE64_TEST
  "Build the pinned KisakBlack Base64 implementation and its regression test" OFF)
set(NUKE_UPSTREAM_SOURCE_DIR "" CACHE PATH
  "Path to a checked-out KisakBlack source tree")

if(NUKE_BUILD_UPSTREAM_BASE64_TEST)
  if(NOT IS_DIRECTORY "${NUKE_UPSTREAM_SOURCE_DIR}")
    message(FATAL_ERROR
      "NUKE_BUILD_UPSTREAM_BASE64_TEST requires NUKE_UPSTREAM_SOURCE_DIR to point to KisakBlack")
  endif()

  set(NUKE_UPSTREAM_BASE64_SOURCE
    "${NUKE_UPSTREAM_SOURCE_DIR}/src/universal/base64.cpp")
  if(NOT EXISTS "${NUKE_UPSTREAM_BASE64_SOURCE}")
    message(FATAL_ERROR
      "KisakBlack Base64 source not found: ${NUKE_UPSTREAM_BASE64_SOURCE}")
  endif()

  add_executable(nuke-upstream-base64-test
    "${NUKE_UPSTREAM_BASE64_SOURCE}"
    tests/upstream_base64.cpp)
  target_include_directories(nuke-upstream-base64-test PRIVATE
    "${NUKE_UPSTREAM_SOURCE_DIR}/src/universal")

  if(BUILD_TESTING AND NOT CMAKE_CROSSCOMPILING)
    add_test(NAME upstream-base64-roundtrip
      COMMAND nuke-upstream-base64-test)
  endif()
endif()


# Compile-only gate for a second real engine translation unit. This intentionally
# stops before linking because the full engine dependency graph is not ported yet.
option(NUKE_BUILD_UPSTREAM_ANGLE_VECTORS
  "Compile the pinned KisakBlack angle/vector translation unit" OFF)

if(NUKE_BUILD_UPSTREAM_ANGLE_VECTORS)
  if(NOT IS_DIRECTORY "${NUKE_UPSTREAM_SOURCE_DIR}")
    message(FATAL_ERROR
      "NUKE_BUILD_UPSTREAM_ANGLE_VECTORS requires NUKE_UPSTREAM_SOURCE_DIR to point to KisakBlack")
  endif()

  set(NUKE_UPSTREAM_ANGLE_VECTORS_SOURCE
    "${NUKE_UPSTREAM_SOURCE_DIR}/src/universal/com_math_anglevectors.cpp")
  if(NOT EXISTS "${NUKE_UPSTREAM_ANGLE_VECTORS_SOURCE}")
    message(FATAL_ERROR
      "KisakBlack angle/vector source not found: ${NUKE_UPSTREAM_ANGLE_VECTORS_SOURCE}")
  endif()

  if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    message(FATAL_ERROR
      "The upstream angle/vector translation unit currently requires Clang Microsoft-compatibility extensions")
  endif()

  add_library(nuke-upstream-angle-vectors OBJECT
    "${NUKE_UPSTREAM_ANGLE_VECTORS_SOURCE}")
  target_include_directories(nuke-upstream-angle-vectors PRIVATE
    "${NUKE_UPSTREAM_SOURCE_DIR}/src"
    "${NUKE_UPSTREAM_SOURCE_DIR}/src/universal")
  target_compile_options(nuke-upstream-angle-vectors PRIVATE -fms-extensions)

  # Extract only the patched quaternion converter and its tiny vector helper.
  # The full com_math.cpp translation unit depends on engine-wide services.
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  set(NUKE_UPSTREAM_AXIS_TO_QUAT_SOURCE
    "${CMAKE_CURRENT_BINARY_DIR}/upstream_axis_to_quat_extracted.cpp")
  add_custom_command(
    OUTPUT "${NUKE_UPSTREAM_AXIS_TO_QUAT_SOURCE}"
    COMMAND "${Python3_EXECUTABLE}"
      "${CMAKE_CURRENT_SOURCE_DIR}/tests/extract_upstream_axis_to_quat.py"
      "${NUKE_UPSTREAM_SOURCE_DIR}/src/universal/com_math.cpp"
      "${NUKE_UPSTREAM_AXIS_TO_QUAT_SOURCE}"
    DEPENDS
      tests/extract_upstream_axis_to_quat.py
      "${NUKE_UPSTREAM_SOURCE_DIR}/src/universal/com_math.cpp"
      "${NUKE_UPSTREAM_SOURCE_DIR}/src/ik/ik_math.cpp"
    VERBATIM)
  add_library(nuke-upstream-axis-to-quat OBJECT
    "${NUKE_UPSTREAM_AXIS_TO_QUAT_SOURCE}")
  target_compile_options(nuke-upstream-axis-to-quat PRIVATE -fms-extensions)

  # Link the real upstream angle/vector and quaternion subset on both host and Android.
  # Host tests use sanitizers; Android CI links the same sources to catch unresolved
  # platform dependencies before the full engine target exists.
  add_executable(nuke-upstream-angle-vectors-test
    "${NUKE_UPSTREAM_ANGLE_VECTORS_SOURCE}"
    "${NUKE_UPSTREAM_AXIS_TO_QUAT_SOURCE}"
    tests/upstream_angle_vectors.cpp)
  target_include_directories(nuke-upstream-angle-vectors-test PRIVATE
    "${NUKE_UPSTREAM_SOURCE_DIR}/src"
    "${NUKE_UPSTREAM_SOURCE_DIR}/src/universal")
  target_compile_options(nuke-upstream-angle-vectors-test PRIVATE -fms-extensions)
  if(BUILD_TESTING AND NOT CMAKE_CROSSCOMPILING)
    target_compile_options(nuke-upstream-angle-vectors-test PRIVATE
      -fsanitize=address,undefined -fno-sanitize-recover=all
      -fno-omit-frame-pointer)
    target_link_options(nuke-upstream-angle-vectors-test PRIVATE
      -fsanitize=address,undefined -fno-sanitize-recover=all)
    add_test(NAME upstream-angle-vectors-roundtrip
      COMMAND nuke-upstream-angle-vectors-test)
  endif()
endif()

if(BUILD_TESTING)
  find_package(Threads REQUIRED)
  add_executable(nuke-atomic-test tests/atomic_compat.cpp)
  target_include_directories(nuke-atomic-test PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include")
  target_link_libraries(nuke-atomic-test PRIVATE Threads::Threads)
  if(NOT CMAKE_CROSSCOMPILING)
    add_test(NAME physics-atomic-compat COMMAND nuke-atomic-test)
    add_test(NAME probe-accepts-mp-nuked-scope COMMAND nuke-platform-probe mp_nuked)
    add_test(NAME reject-other-map
      COMMAND ${CMAKE_COMMAND}
        "-DPROBE=$<TARGET_FILE:nuke-platform-probe>"
        -P "${CMAKE_CURRENT_SOURCE_DIR}/tests/reject_other_map.cmake")
  endif()
endif()
