#!/bin/bash

# Configs cores

mkdir -p /cores
echo '/cores/core.%h.%p.%E' | sudo tee /proc/sys/kernel/core_pattern

# Installs corpus, tools, configs and paths

corpus_path="/usr/local/src/cgc"
mkdir -p $corpus_path
# TODO: copy corpus to to corpus path

#Tools
tools_path="/usr/local/share/pyshared/cgc"
mkdir -p "$tools_path"
cp -r tools/* $tools_path
cp "tools/cwe_dict.csv" "/usr/local/share"

#Configs
config_path="/etc/cgcrepair"
mkdir -p $config_path
cp "config/cgcrepair.yml" $config_path

#Polls and Povs
polls_path="/usr/local/share/polls"
polls_lib_path="/usr/local/lib/cgc/polls"
mkdir -p $polls_path
mkdir -p $polls_lib_path
mkdir -p "/usr/local/share/povs"


# Installs shared libraries
cmake_opts=$CMAKE_OPTS
platform_arch=$(uname -i)

if [ "$platform_arch" == "x86_64" ]; then
	cmake_opts="$cmake_opts -DCMAKE_SYSTEM_PROCESSOR=amd64"
else
	cmake_opts="$cmake_opts -DCMAKE_SYSTEM_PROCESSOR=i686"
fi

shared="-DBUILD_SHARED_LIBS=ON -DBUILD_STATIC_LIBS=OFF"
static="-DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON"

cmake_opts="$cmake_opts $shared"
build_dir="/opt/cgc_repair"
current_dir=`pwd`
include_src_dir="$current_dir/lib/include"
mkdir -p "$build_dir"
cd "$build_dir"

cmake "$cmake_opts" $include_src_dir
[[ $? -eq 1 ]] && echo "[Error] cmake config failed" && exit 1 ;

cmake --build .
[[ $? -eq 1 ]] && echo "[Error] cmake build failed" && exit 1 ;

cmake --build . --target install
[[ $? -eq 1 ]] && echo "[Error] cmake install failed" && exit 1 ;

echo "cgc include libraries installed"
