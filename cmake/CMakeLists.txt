# Using this min version for now
cmake_minimum_required(VERSION 3.1)

project(challenge_sets C CXX)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Needed for newer challenges
set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 11)

if(WIN32)
    # Need to use MASM on windows
    enable_language(ASM_MASM)

    set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS TRUE)
    set(BUILD_SHARED_LIBS TRUE)

    add_compile_options(
        /w
        /W0
        /Z7
        /GS-
        /GR-
        /guard:cf-
    )
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} /MACHINE:X86 /NXCOMPAT:NO /SAFESEH:NO /DYNAMICBASE:NO")
    set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} /MACHINE:X86")

    # Read in challenges to exclude from build
    if(CLANGCL)
        file(STRINGS "exclude/win_clangcl.txt" cb_exclude)
        add_definitions(-DCLANGCL)
    else()
        file(STRINGS "exclude/win_msvc.txt" cb_exclude)
        add_definitions(-DWIN)
    endif()
else(WIN32)
    # Generic ASM can be enabled on other OSs
    enable_language(ASM)

    if(UNIX AND NOT APPLE)
        set(LINUX TRUE)
        add_definitions(-DLINUX)

    endif()
    if(APPLE)
        add_definitions(-DAPPLE)

        # Read in challenges to exclude from build
        file(STRINGS "exclude/osx.txt" cb_exclude)
    endif()

    # Default flags for everything
    add_compile_options(
        -fno-builtin
        -fcommon
        -w
        -g3
    )

    if(DEFINED ENV{SAVETEMPS})
        add_compile_options(-save-temps=obj)
    endif()

    if(DEFINED ENV{M32})
        # Link everything 32-bit

        set(CMAKE_C_FLAGS_INIT -m32)
        set(CMAKE_CXX_FLAGS_INIT -m32)
        set(CMAKE_ASM_FLAGS_INIT -m32)

        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -m32")
        set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -m32")
        set(CMAKE_MODULE_LINKER_FLAGS_INIT -m32)
        add_compile_definitions(X32_COMPILE)
        add_compile_options(-m32)
    endif()

    # Linker options
    # Dynamic by default
    option(BUILD_SHARED_LIBS "" ON)
    if(BUILD_STATIC_LIBS AND LINUX)
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -static -Wl,--allow-multiple-definition")
        set(CMAKE_SHARED_LIBRARY_LINK_C_FLAGS "")
        set(CMAKE_SHARED_LIBRARY_LINK_CXX_FLAGS "")
    endif()
endif(WIN32)


if(DEFINED ENV{COVERAGE})
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fprofile-arcs -ftest-coverage")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-arcs -ftest-coverage")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fprofile-arcs -ftest-coverage")
endif()

# set environment C flags
set(CMAKE_C_FLAGS $ENV{CMAKE_C_FLAGS})

# Include all libraries
include_directories($ENV{CGC_INCLUDE_DIR})

find_library(LIB_CGC NAMES cgc PATHS $ENV{CGC_LIB_DIR})
find_library(LIB_POV NAMES pov PATHS $ENV{CGC_LIB_DIR})
find_library(LIB_AES NAMES tiny-AES128-C PATHS $ENV{CGC_LIB_DIR})

function(build path target)
    message(STATUS "Building ${target}")

    # Gather all sources
    aux_source_directory(${path}/src cb_src)
    aux_source_directory(${path}/lib cb_lib)
    aux_source_directory(${path}/include cb_inc)
    set(cb_all_src ${cb_lib} ${cb_src} ${cb_inc})

    add_executable(${target} ${cb_all_src})

    if(DEFINED ENV{PATCH})
        add_executable(${target}_patched ${cb_all_src})
    endif()

    target_include_directories(${target} PUBLIC ${path}/lib ${path}/src ${path}/include)

    if(DEFINED ENV{PATCH})
    	target_include_directories(${target}_patched PUBLIC ${path}/lib ${path}/src ${path}/include)
    endif()

    set_target_properties(${target} PROPERTIES
                          RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_CURRENT_BINARY_DIR}
                          RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_CURRENT_BINARY_DIR})
    if(DEFINED ENV{PATCH})
        set_target_properties(${target}_patched PROPERTIES
                              RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_CURRENT_BINARY_DIR}
                              RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_CURRENT_BINARY_DIR})
    endif()

    if(DEFINED ENV{PATCH})
    # Add patched defines
    	target_compile_definitions(${target}_patched PUBLIC ${patch_defs})
    endif()

    target_link_libraries(${target} LINK_PUBLIC ${LIB_CGC} ${LIB_AES})
    if(DEFINED ENV{PATCH})
        target_link_libraries(${target}_patched LINK_PUBLIC ${LIB_CGC} ${LIB_AES})
    endif()


    IF(WIN32)
        # Copy required DLLs post-build
        add_custom_command(
            TARGET ${target} POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:cgc> ${CMAKE_CURRENT_BINARY_DIR}
            COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:tiny-AES128-C> ${CMAKE_CURRENT_BINARY_DIR}
            COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:pov> ${CMAKE_CURRENT_BINARY_DIR}
        )
    ENDIF()
endfunction(build)

function(buildPOV path cb pov)
    # Unique target name, i.e. "Palindrome2_pov_1",
    # executable name kept as "pov_#.pov"
    set(target "${cb}_${pov}")

    # Gather sources
    aux_source_directory("${path}/${pov}" pov_src)
    add_executable(${target} ${pov_src})

    # POVs are allowed to include challenge headers,
    # but must have their own definitions
    target_include_directories(
        ${target} PUBLIC
        "${path}/${pov}"
        "${path}/include"
        "${path}/lib"
        "${path}/src"
        "$ENV{CGC_INCLUDE_DIR}/libpov"
    )
    set_target_properties(${target} PROPERTIES
        OUTPUT_NAME "${pov}.pov"
        RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_CURRENT_BINARY_DIR}
        RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_CURRENT_BINARY_DIR}
    )

    target_link_libraries(${target} LINK_PUBLIC ${LIB_CGC} ${LIB_POV} ${LIB_AES})
endfunction(buildPOV)

function(buildCB)
    if(DEFINED ENV{PATCH})
        # Generate all the patched #defines for this challenge
        set(patch_defs -DPATCHED)
        if(VULN_COUNT)
            foreach(i RANGE 1 ${VULN_COUNT})
                set(patch_defs ${patch_defs} -DPATCHED_${i})
            endforeach()
        endif()
    endif()

    # Some challenges have multiple binaries that need to be built
    # Check if these directories exist
    file(GLOB cb_parts "${cb_path}/cb_*")
    if(cb_parts)
        # Iterate through the directories and build each
        set(i 1)
        foreach(cb ${cb_parts})
            build(${cb_path}/cb_${i} ${cb_id}_${i})
            MATH(EXPR i "${i} + 1")
        endforeach()
    else()
        # Build normally if there are no extra directories
        build(${cb_path} ${cb_id})
    endif()

    file(GLOB cb_povs "${cb_path}/pov_*")
    if(cb_povs)
        foreach(path ${cb_povs})
            # Get the pov name, i.e. "pov_1"
            get_filename_component(pov ${path} NAME)
            buildPOV(${cb_path} ${cb_id} ${pov})
        endforeach()
    endif()
endfunction(buildCB)

function(buildSO)
    if(UNIX)
        # Build a shared library object for a specific challenge
        set(LIB_DIR ${cb_path}/lib)
        set(SRC_DIR ${cb_path}/src)
        set(INCLUDE_DIR ${cb_path}/include)

        file(GLOB lib_files ${LIB_DIR}/*)
        file(GLOB src_files ${SRC_DIR}/*)
        set(LIB_SRCS ${lib_files} ${src_files})

        set(LIB_NAME ${AUTHOR_ID}_${SERVICE_ID})
        if(BUILD_STATIC_LIBS)
            set(LIB_CGC "${PROJECT_BINARY_DIR}/include/libcgc.a")
        else()
            if(APPLE)
                set(LIB_CGC "${PROJECT_BINARY_DIR}/include/libcgc.dylib")
            #else()
            #    set(LIB_CGC "${PROJECT_BINARY_DIR}/include/libcgc.so")
            endif()
        endif()

        if(BUILD_STATIC_LIBS)
            message(STATUS "Building static library (${LIB_NAME}.a)")
            add_library(${LIB_NAME} STATIC ${LIB_SRCS})
        else()
            message(STATUS "Building shared library (${LIB_NAME}.so)")
            add_library(${LIB_NAME} SHARED ${LIB_SRCS})
        endif()

        target_include_directories(${LIB_NAME} PUBLIC ${LIB_DIR})
        target_include_directories(${LIB_NAME} PUBLIC ${INCLUDE_DIR})
        target_link_libraries(${LIB_NAME} ${LIB_CGC})

	    INSTALL(TARGETS ${LIB_NAME}
		LIBRARY DESTINATION /usr/local/lib/cgc/polls
	)
    endif()
endfunction(buildSO)

# More options needed for cbs
if(NOT WIN32)
    add_compile_options(
        -fno-stack-protector
    )
endif()

add_definitions(
    -Derrno=__cgc_errno
    -DFORTIFY_SOURCE=0
)

if(LINUX)
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -z execstack -z norelro")
endif()


SET(CB_PATH "" CACHE STRING "challenge path")

file(GLOB cb_path ${CB_PATH})
get_filename_component(cb_id ${cb_path} NAME)
add_subdirectory(${cb_path})
