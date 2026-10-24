if(NOT DEFINED PROBE OR NOT EXISTS "${PROBE}")
  message(FATAL_ERROR "PROBE must name the built nuke-platform-probe executable")
endif()

execute_process(
  COMMAND "${PROBE}" mp_cracked
  RESULT_VARIABLE result
  OUTPUT_VARIABLE stdout
  ERROR_VARIABLE stderr
)

# Reject crashes and launch failures; this test expects a normal non-zero exit.
if(NOT "${result}" MATCHES "^[0-9]+$")
  message(FATAL_ERROR "probe did not exit normally: ${result}")
endif()
if("${result}" STREQUAL "0")
  message(FATAL_ERROR "probe unexpectedly accepted mp_cracked")
endif()

string(STRIP "${stderr}" stderr_stripped)
if(NOT stdout STREQUAL "")
  message(FATAL_ERROR "unexpected stdout from rejected map: ${stdout}")
endif()
if(NOT stderr_stripped STREQUAL "Only mp_nuked is within project scope.")
  message(FATAL_ERROR "unexpected rejection diagnostic: ${stderr}")
endif()

message(STATUS "mp_cracked rejected with the expected diagnostic")
