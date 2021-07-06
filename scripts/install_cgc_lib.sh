# Installs shared libraries
# shellcheck disable=SC2153
cmake_opts="$CMAKE_OPTS -DBUILD_SHARED_LIBS=ON -DBUILD_STATIC_LIBS=ON"

build_dir="/opt/cgc_repair"
# shellcheck disable=SC2006
current_dir=`pwd`
include_src_dir="$current_dir/lib/include"
mkdir -p "$build_dir"

export M32="TRUE"
mkdir -p "/usr/local/lib32/cgc"


cd $build_dir && cmake "$cmake_opts" "-DCMAKE_SYSTEM_PROCESSOR=i686" "$include_src_dir"
[[ $? -eq 1 ]] && echo "[Error] cmake config failed" && exit 1 ;

cmake --build .
[[ $? -eq 1 ]] && echo "[Error] cmake build failed" && exit 1 ;

cmake --build . --target install
[[ $? -eq 1 ]] && echo "[Error] cmake install failed" && exit 1 ;

echo "cgc-repair include and 32 bit libraries installed"

platform_arch=$(uname -i)
if [ "$platform_arch" == "x86_64" ]; then
    mkdir -p "/usr/local/lib64/cgc"
    mkdir -p "${build_dir}64"
    unset M32
    cd "${build_dir}64" && cmake "$cmake_opts" "-DCMAKE_SYSTEM_PROCESSOR=amd64" "$include_src_dir"
    [[ $? -eq 1 ]] && echo "[Error] cmake 64bit config failed" && exit 1 ;

    cmake --build .
    [[ $? -eq 1 ]] && echo "[Error] cmake 64bit build failed" && exit 1 ;

    cmake --build . --target install
    [[ $? -eq 1 ]] && echo "[Error] cmake 64 bit install failed" && exit 1 ;

    echo "cgc-repair 64 bit libraries installed"
fi
