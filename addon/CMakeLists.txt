cmake_minimum_required(VERSION 3.16)
project(gw2chatlogger_addon CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

add_library(gw2chatlogger SHARED src/main.cpp)
target_include_directories(gw2chatlogger PRIVATE include)

# Produce "arcdps_gw2chatlogger.dll" (arcdps only loads addons named arcdps_*.dll).
set_target_properties(gw2chatlogger PROPERTIES
    PREFIX ""
    OUTPUT_NAME "arcdps_gw2chatlogger")

target_compile_options(gw2chatlogger PRIVATE -O2 -Wall -Wextra)

# Statically link the runtime so the DLL has no mingw runtime dependencies and can
# be dropped next to arcdps as-is (on Windows or inside a Proton prefix).
target_link_options(gw2chatlogger PRIVATE
    -static
    -static-libgcc
    -static-libstdc++)
