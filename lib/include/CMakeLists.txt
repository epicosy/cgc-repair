cmake_minimum_required(VERSION 3.1)

project(cgc C CXX)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Needed for newer challenges
set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 11)
enable_language(ASM)
set(LINUX TRUE)
add_definitions(-DLINUX)

# Default flags for everything
add_compile_options(
	-fno-builtin
	-fcommon
	-w
	-g3
)

# Linker options
# Dynamic by default
option(BUILD_SHARED_LIBS "" ON)
if(BUILD_STATIC_LIBS AND LINUX)
	set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -static -Wl,--allow-multiple-definition")
	set(CMAKE_SHARED_LIBRARY_LINK_C_FLAGS "")
	set(CMAKE_SHARED_LIBRARY_LINK_CXX_FLAGS "")
endif()
set(LIB_DESTINATION "/usr/local/lib64/cgc/")
if(DEFINED ENV{M32})
    set(LIB_DESTINATION "/usr/local/lib32/cgc/")
    set(CMAKE_C_FLAGS_INIT -m32)
    set(CMAKE_CXX_FLAGS_INIT -m32)
    set(CMAKE_ASM_FLAGS_INIT -m32)

    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -m32")
    set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -m32")
    set(CMAKE_MODULE_LINKER_FLAGS_INIT -m32)
    add_compile_definitions(X32_COMPILE)
    add_compile_options(-m32)
endif()

set(cgc_src libcgc.c maths.S)
if(WIN32)
    set(cgc_src libcgc_win.c maths_win.asm)
    set_source_files_properties(maths_win.asm PROPERTIES COMPILE_FLAGS "/safeseh")
endif()

# More options needed for cbs

add_compile_options(
	-fno-stack-protector
)

add_definitions(
    -Derrno=__cgc_errno
    -DFORTIFY_SOURCE=0
)


set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -z execstack -z norelro")


add_library(cgc ${cgc_src} ansi_x931_aes128.c)
target_include_directories(cgc PUBLIC .)
target_include_directories(cgc PUBLIC tiny-AES128-C)
target_link_libraries(cgc LINK_PUBLIC tiny-AES128-C)

# Build tiny-AES128-C
add_subdirectory(tiny-AES128-C)

# Build libpov
add_subdirectory(libpov)

set_target_properties(cgc PROPERTIES PUBLIC_HEADER "libcgc.h;ansi_x931_aes128.h")
INSTALL(TARGETS cgc
        LIBRARY DESTINATION ${LIB_DESTINATION}
        PUBLIC_HEADER DESTINATION /usr/local/include/cgc
)
