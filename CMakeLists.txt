cmake_minimum_required(VERSION 3.15)
project(ChessEngine)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(CTest)
include(cmake/CompilerOptions.cmake)
include(cmake/Core.cmake)
include(cmake/Variants.cmake)
include(cmake/EmbeddedNetwork.cmake)
include(cmake/Visualizer.cmake)

if(BUILD_TESTING)
    include(cmake/Tests.cmake)
endif()

message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "C++ Standard: ${CMAKE_CXX_STANDARD}")
