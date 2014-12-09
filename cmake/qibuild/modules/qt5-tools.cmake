##
# This is called *before* any call to qi_use_lib() is made.
# Here we need to define the qt macros, such as qt5_wrap_cpp,
# qt5_add_resources, qt5_wrap_ui
set(CMAKE_AUTOMOC ON)
find_package(Qt5Core REQUIRED)
include("${Qt5Core_DIR}/Qt5CoreMacros.cmake")

find_package(Qt5Widgets REQUIRED)
include("${Qt5Widgets_DIR}/Qt5WidgetsMacros.cmake")

function(qi_generate_qt_conf)
  # First, find qt and generate qt.conf
  # containing paths in the toolchain
  if(DEFINED QT_PLUGINS_PATH)
    set(_plugins_path "${QT_PLUGINS_PATH}")
  else()
    list(GET QT5_CORE_LIBRARIES 0 _lib)
    if("${_lib}" STREQUAL "debug"
        OR "${_lib}" STREQUAL "optimized"
        OR "${_lib}" STREQUAL "general")
      list(GET QT5_CORE_LIBRARIES 1 _lib)
    endif()

    get_target_property(_lib_loc ${_lib} LOCATION)
    get_filename_component(_lib_path ${_lib_loc} PATH)
    if(APPLE)
      # location is: <prefix>/lib/QtCore.framework/QtCore
      get_filename_component(_lib_path ${_lib_path} PATH)
    endif()
    get_filename_component(_root_path ${_lib_path} PATH)
  endif()

  file(WRITE "${QI_SDK_DIR}/${QI_SDK_BIN}/qt.conf"
"[Paths]
Prefix = ${_root_path}
")

  # Then, generate and install a qt.conf
  # containing relative paths
  file(WRITE "${CMAKE_BINARY_DIR}/qt.conf"
"[Paths]
Prefix = ..
")
  install(FILES "${CMAKE_BINARY_DIR}/qt.conf" DESTINATION bin COMPONENT runtime)

endfunction()
