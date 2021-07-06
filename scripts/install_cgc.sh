#!/bin/bash

# Configs cores

#mkdir -p /cores
#echo '/cores/core.%h.%p.%E' | sudo tee /proc/sys/kernel/core_pattern

# Install dependencies
apt-get install -y libc6-dev gcc-multilib g++-multilib gdb python2.7-dev software-properties-common cmake
[[ $? -eq 1 ]] && echo "[Error] Failed to install cgc-repair dependencies." && exit 1 ;
pip install cppy==1.1.0 numpy==1.16.6 && pip install pycrypto==2.6.1 pyaml==20.4.0 matplotlib==2.1
[[ $? -eq 1 ]] && echo "[Error] Failed to install cgc-repair Python 2 dependencies." && exit 1 ;

echo "cgc-repair repair dependencies installed"
# Installs corpus, tools, configs and paths

corpus_path="/usr/local/src/cgc"
mkdir -p $corpus_path
# TODO: copy corpus to to corpus path

#Tools
tools_path="/usr/local/share/pyshared/cgc"
mkdir -p "$tools_path" && cp -r tools/* $tools_path && cp "tools/cwe_dict.csv" "/usr/local/share"
[[ $? -eq 1 ]] && echo "[Error] Failed to install cgc-repair tools." && exit 1 ;

#Configs
config_path="/etc/cgcrepair"
mkdir -p $config_path && cp "config/cgcrepair.yml" $config_path
[[ $? -eq 1 ]] && echo "[Error] Failed to install cgc-repair configs." && exit 1 ;

#Polls and Povs Directories
mkdir -p "/usr/local/share/polls" && mkdir -p "/usr/local/lib/cgc/polls" && mkdir -p "/usr/local/share/povs"
[[ $? -eq 1 ]] && echo "[Error] Failed to create Polls and POVs directories for cgc-repair." && exit 1 ;

# Installs shared libraries
./install_cgc_lib.sh
[[ $? -eq 1 ]] && echo "install_cgc_lib.sh: [Error] Failed to install lib and include for CGC corpus." && exit 1 ;
