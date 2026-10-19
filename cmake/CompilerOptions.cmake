# Single-config generators default to no build type, which silently skips
# NDEBUG and leaves asserts in the hot path. Default to Release.
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

option(ENGINE_NATIVE "Tune codegen for the build machine (-march=native)" ON)

# Perft-only optimization: a precomputed enemy king-danger map speeds up perft
# (~+3%) because it amortizes over every king move, but it regresses real
# search (king moves are rare there), so it is off by default. Enable only for
# perft benchmarking: -DOPT_KING_DANGER=ON.
option(OPT_KING_DANGER "Precompute enemy king-danger map (perft-only win)" OFF)
if(OPT_KING_DANGER)
    add_compile_definitions(ENGINE_KING_DANGER)
endif()
# Profile-guided optimization. Configure with -DENGINE_PGO=generate, build,
# run `bench 12`, then reconfigure with -DENGINE_PGO=use and rebuild.
set(ENGINE_PGO "off" CACHE STRING "PGO mode: off | generate | use")

# LTO/IPO is on by default but can be disabled (e.g. for sanitizer builds).
option(ENGINE_LTO "Enable link-time / interprocedural optimization" ON)
if(ENGINE_LTO)
    set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
endif()

if(MSVC)
    add_compile_options(/O2 /W4 /Ot /Ob2 /arch:AVX2)
    # Deep search recursion (up to MAX_PLY plies, plus singular same-ply
    # re-searches, each frame carrying large move buffers) overflows MSVC's
    # 1 MB default stack. Give it 32 MB; on Windows this PE value also seeds
    # std::thread worker stacks, so it protects real deep searches too.
    add_link_options(/STACK:33554432)
    if(ENGINE_LTO)
        add_link_options(/LTCG)
    endif()
else()
    add_compile_options(-O3 -Wall -Wextra)
    if(EMSCRIPTEN)
        # The browser build links with shared memory (pthreads), and wasm-ld
        # refuses to mix objects built with the atomics feature and objects
        # built without it -- so every translation unit needs these, not just
        # the final link. -msimd128 lets the compiler vectorise the portable
        # scalar NNUE kernels. Set here rather than via CXXFLAGS/-DCMAKE_CXX_FLAGS
        # because emcmake re-invokes cmake and drops those.
        add_compile_options(-pthread -msimd128)
    elseif(ENGINE_NATIVE)
        add_compile_options(-march=native)
    endif()
    if(ENGINE_PGO STREQUAL "generate")
        add_compile_options(-fprofile-generate)
        add_link_options(-fprofile-generate)
    elseif(ENGINE_PGO STREQUAL "use")
        add_compile_options(-fprofile-use -fprofile-correction -Wno-missing-profile)
        add_link_options(-fprofile-use)
    endif()
    if(WIN32)
        # MinGW: avoid depending on the toolchain's runtime DLLs at run time
        add_link_options(-static)
        # Same deep-recursion stack headroom as the MSVC build (the PE default
        # stack also seeds std::thread workers on Windows).
        add_link_options(-Wl,--stack,33554432)
    endif()
endif()
