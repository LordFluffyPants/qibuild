## Copyright (C) 2011 Aldebaran Robotics

#! Installing
# ===========
#
# See general documentation here :ref:`cmake-installing`
#


#! Generic install function.
# \param: SUBFOLDER      An optional subfolder in which to put the files.
# \param: IF             Condition that should be verified for the install rules
#                        to be active for example (IF WITH_ZEROMQ)
# \flag: KEEP_RELATIVE_PATHS  If true, relative paths will be preserved during installation.
function(qi_install)
  _qi_install_internal(${ARGN})
endfunction()

#! Install application headers.
# The destination will be <prefix>/include/
#
# \arg target            The library corresponding to these headers. The library
#                        must already exist. Necessary if you want to use internal libraries.
# \argn:                 A list of files : directories and globs on files are accepted.
# \param: SUBFOLDER      An optional subfolder in which to put the files.
# \param: IF             Condition that should be verified for the install rules
#                        to be active for example (IF WITH_ZEROMQ)
# \flag: KEEP_RELATIVE_PATHS  If true, relative paths will be preserved during installation.
#                        (False by default because this is NOT the standard CMake
#                         behavior)
# \group: HEADERS        Required: the list of headers to install
function(qi_install_header target)
  cmake_parse_arguments(ARG  "KEEP_RELATIVE_PATHS" "SUBFOLDER"  "HEADERS" ${ARGN})
  set(_headers ${ARG_HEADERS} ${ARG_UNPARSED_ARGUMENTS})
  if(NOT _headers)
    qi_error("No headers specified")
  endif()

  _qi_check_is_target(${target})
  # Handle ${target}_INTERNAL
  set(_should_install TRUE)
  if(${${target}_INTERNAL})
    set(_should_install FALSE)
  endif()
  if(${QI_INSTALL_INTERNAL})
    set(_should_install TRUE)
  endif()

  set(_relative_flag "")
  if(${ARG_KEEP_RELATIVE_PATHS})
    set(_relative_flag KEEP_RELATIVE_PATHS)
  endif()

  if(_should_install)
    _qi_install_internal(${_headers}
      COMPONENT header
      DESTINATION ${QI_SDK_INCLUDE}
      SUBFOLDER ${ARG_SUBFOLDER}
      ${_relative_flag}
    )
  endif()
endfunction()



#! Install application data.
# The destination will be: <prefix>/share/
#
# \argn:                 A list of files : directories and globs on files are accepted.
# \param: SUBFOLDER      An optional subfolder in which to put the files.
# \param: IF             Condition that should be verified for the install rules
#                        to be active for example (IF WITH_ZEROMQ)
# \flag: KEEP_RELATIVE_PATHS  If true, relative paths will be preserved during installation.
#                        (False by default because this is NOT the standard CMake
#                         behavior)
#
function(qi_install_data)
  _qi_install_internal(${ARGN} COMPONENT data  DESTINATION ${QI_SDK_SHARE})
endfunction()

#! Install application doc.
# The destination will be: <prefix>/share/doc/
#
# \argn:                 A list of files : directories and globs on files are accepted.
# \param: SUBFOLDER      An optional subfolder in which to put the files.
# \param: IF             Condition that should be verified for the install rules
#                        to be active for example (IF WITH_ZEROMQ)
# \flag: KEEP_RELATIVE_PATHS  If true, relative paths will be preserved during installation.
#                        (False by default because this is NOT the standard CMake
#                         behavior)
#
function(qi_install_doc)
  _qi_install_internal(${ARGN} COMPONENT doc   DESTINATION ${QI_SDK_DOC})
endfunction()


#! Install application configuration files.
#
# \argn:                 A list of files : directories and globs on files are accepted.
# \param: SUBFOLDER      An optional subfolder in which to put the files.
# \param: IF             Condition that should be verified for the install rules
#                        to be active for example (IF WITH_ZEROMQ)
# \flag: KEEP_RELATIVE_PATHS  If true, relative paths will be preserved during installation.
#                        (False by default because this is NOT the standard CMake
#                         behavior)
#
function(qi_install_conf)
  _qi_install_internal(${ARGN} COMPONENT conf  DESTINATION ${QI_SDK_CONF})
endfunction()

#! Install CMake module files.
# The destination will be: <prefix>/share/cmake/
#
# \argn:                 A list of files : directories and globs on files are accepted.
# \param: SUBFOLDER      An optional subfolder in which to put the files.
# \param: IF             Condition that should be verified for the install rules
#                        to be active for example (IF WITH_ZEROMQ)
# \flag: KEEP_RELATIVE_PATHS  If true, relative paths will be preserved during installation.
#                        (False by default because this is NOT the standard CMake
#                         behavior)
#
function(qi_install_cmake)
  _qi_install_internal(${ARGN} COMPONENT cmake DESTINATION ${QI_SDK_CMAKE})
endfunction()


#! install a target, that could be a program or a library.
#
# \argn:                 A list of targets to install
# \param: SUBFOLDER      An optional subfolder in which to put the files.
# \param: IF             Condition that should be verified for the install rules
#                        to be active for example (IF WITH_ZEROMQ)
function(qi_install_target)
  cmake_parse_arguments(ARG "" "IF;SUBFOLDER" "" ${ARGN})

  if (NOT "${ARG_IF}" STREQUAL "")
    set(_doit TRUE)
  else()
    #I must say... lol cmake, but NOT NOT TRUE is not valid!!
    if (${ARG_IF})
    else()
      set(_doit TRUE)
    endif()
  endif()
  if (NOT _doit)
    return()
  endif()

  if(ARG_SUBFOLDER)
    set(_dll_output ${QI_SDK_LIB}/${ARG_SUBFOLDER})
  else()
    set(_dll_output ${QI_SDK_BIN})
  endif()

  if(WIN32)
    set(_runtime_output ${_dll_output})
  else()
    set(_runtime_output ${QI_SDK_BIN}/${ARG_SUBFOLDER})
  endif()

  foreach (name ${ARG_UNPARSED_ARGUMENTS})
    install(TARGETS "${name}"
            RUNTIME COMPONENT binary     DESTINATION ${_runtime_output}
            LIBRARY COMPONENT lib        DESTINATION ${QI_SDK_LIB}/${ARG_SUBFOLDER}
      PUBLIC_HEADER COMPONENT header     DESTINATION ${QI_SDK_INCLUDE}/${ARG_SUBFOLDER}
           RESOURCE COMPONENT data       DESTINATION ${QI_SDK_SHARE}/${name}/${ARG_SUBFOLDER}
            ARCHIVE COMPONENT static-lib DESTINATION ${QI_SDK_LIB}/${ARG_SUBFOLDER})
  endforeach()
endfunction()

#! install program (mostly script or user provided program). Do not use this function
# to install a library or a program built by your project, prefer using qi_install_target.
#
# \argn:                 A list of programs to install
# \param: SUBFOLDER      An optional subfolder in which to put the files.
# \param: IF             Condition that should be verified for the install rules
#                        to be active for example (IF WITH_ZEROMQ)
function(qi_install_program)
  cmake_parse_arguments(ARG "" "IF;SUBFOLDER" "" ${ARGN})

  if (NOT "${ARG_IF}" STREQUAL "")
    set(_doit TRUE)
  else()
    #I must say... lol cmake, but NOT NOT TRUE is not valid!!
    if (${ARG_IF})
    else()
      set(_doit TRUE)
    endif()
  endif()
  if (NOT _doit)
    return()
  endif()

  foreach(name ${ARG_UNPARSED_ARGUMENTS})
    #TODO: what should be the real source here?
    install(PROGRAMS    "${QI_SDK_DIR}/${QI_SDK_BIN}/${ARG_SUBFOLDER}/${name}"
            COMPONENT   binary
            DESTINATION "${QI_SDK_BIN}/${ARG_SUBFOLDER}")
  endforeach()
endfunction()


#! install external library. Do not use this function
# to install a library or a program built by your project,
# prefer using qi_install_target.
#
# \argn:                 A list of libraries to install
# \param: SUBFOLDER      An optional subfolder in which to put the files.
# \param: IF             Condition that should be verified for the install rules
#                        to be active for example (IF WITH_ZEROMQ)
function(qi_install_library)
  _qi_install_internal(${ARGN} COMPONENT lib DESTINATION ${QI_SDK_LIB})
endfunction()
