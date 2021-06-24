#!/bin/bash

# Install dependencies
apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget libbz2-dev curl lzma-dev liblzma-dev
[[ $? -eq 1 ]] && echo "[Error] Failed to install dependencies" && exit 1 ;

# Install OpenSSL version for pip
cd /tmp && wget https://www.openssl.org/source/openssl-1.1.0g.tar.gz
[[ $? -eq 1 ]] && echo "[Error] Failed to download OpenSSL 1.1.0" && exit 1 ;
tar -zxf openssl-1.1.0g.tar.gz
[[ $? -eq 1 ]] && echo "[Error] Failed to extract OpenSSL 1.1.0 tar" && exit 1 ;
cd openssl-1.1.0g && ./config && make -j4
[[ $? -eq 1 ]] && echo "[Error] Failed to build OpenSSL 1.1.0" && exit 1 ;
mv /usr/bin/openssl ~/tmp
make install && ln -s /usr/local/bin/openssl /usr/bin/openssl && ldconfig
[[ $? -eq 1 ]] && echo "[Error] Failed to install OpenSSL 1.1.0" && exit 1 ;

# Install Python 3.8.10
cd /tmp && wget https://www.python.org/ftp/python/3.8.10/Python-3.8.10.tgz
[[ $? -eq 1 ]] && echo "[Error] Failed to download Python 3.8.10" && exit 1 ;
tar -xvzf Python-3.8.10.tgz
[[ $? -eq 1 ]] && echo "[Error] Failed to extract Python 3.8.10 tar" && exit 1 ;
cd Python-3.8.10 && ./configure && make -j 4
[[ $? -eq 1 ]] && echo "[Error] Failed to build Python 3.8.10" && exit 1 ;
make install
[[ $? -eq 1 ]] && echo "[Error] Failed to install Python 3.8.10" && exit 1 ;

# Install pip 2 and 3
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
[[ $? -eq 1 ]] && echo "[Error] Failed to download pip for Python 3" && exit 1 ;
python3 get-pip.py
[[ $? -eq 1 ]] && echo "[Error] Failed to install pip for Python 3" && exit 1 ;
curl https://bootstrap.pypa.io/2.7/get-pip.py -o get-pip.py
[[ $? -eq 1 ]] && echo "[Error] Failed to download pip for Python 2" && exit 1 ;
python get-pip.py
[[ $? -eq 1 ]] && echo "[Error] Failed to install pip for Python 2" && exit 1 ;

echo "Setup successfully executed" && exit 0
