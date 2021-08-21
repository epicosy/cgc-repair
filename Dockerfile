FROM ubuntu:20.04
MAINTAINER Eduard Pinconschi <eduard.pinconschi@tecnico.ulisboa.pt>
ENV PS1="\[\e[0;33m\]|> cgcrepair <| \[\e[1;35m\]\W\[\e[0m\] \[\e[0m\]# "
ENV TZ=Europe
ENV CORPUS_PATH="/usr/local/src/cgc"
ENV TMP_DIR="/tmp/cb-multios"
ENV TOOLS_PATH="/usr/local/share/pyshared/cgc"
ENV CONFIG_PATH="/etc/cgcrepair"
ARG threads=4

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

################################
##### Install dependencies #####
################################
RUN apt update && apt -y upgrade && apt install -y -q git build-essential python2.7 python-dev python3-pip \
    python3-dev libc6-dev gcc-multilib g++-multilib gdb software-properties-common cmake curl clang

################################
## Install pip for Python 2.7 ##
################################
RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py && python2 get-pip.py

RUN python2 -m pip install cppy==1.1.0 numpy==1.16.6 && \
    python2 -m pip install pycrypto==2.6.1 pyaml==20.4.0 matplotlib==2.1 defusedxml==0.7.1

################################
##### Install CGC-Corpus #######
################################
RUN mkdir -p $TMP_DIR && mkdir -p $CORPUS_PATH && git clone https://github.com/trailofbits/cb-multios $TMP_DIR
RUN while read -r line; do echo "Copying $line files"; cp -r "$TMP_DIR/challenges/$line" $CORPUS_PATH; done < "$TMP_DIR/linux-working.txt"
RUN rm -r $TMP_DIR

WORKDIR /cgc-repair
COPY . /cgc-repair

################################
# Install tools and libraries ##
################################
RUN mkdir -p $TOOLS_PATH && cp -r tools/* $TOOLS_PATH && cp "tools/cwe_dict.csv" "/usr/local/share" && \
    mkdir -p $CONFIG_PATH && cp "config/cgcrepair.yml" $CONFIG_PATH &&  mkdir -p "/cores" && \
    mkdir -p "/usr/local/share/polls" && mkdir -p "/usr/local/lib/cgc/polls" && mkdir -p "/usr/local/share/povs" && \
    cp "./cmake/CMakeLists.txt" $CORPUS_PATH && cp "./lib/metadata.yml" $CONFIG_PATH

RUN ./scripts/install_cgc_lib.sh

################################
####### Setup database #########
################################
RUN apt-get install -y postgresql libpq-dev && python3 -m pip install psycopg2
USER postgres
RUN /etc/init.d/postgresql start && psql --command "CREATE USER cgcrepair WITH SUPERUSER PASSWORD 'cgcrepair123';" &&  \
    createdb cgcrepair
USER root

################################
##### Install cgc-repair #######
################################
RUN python3 -m pip install --no-cache-dir -r requirements.txt && python3 setup.py install


################################
######### Prepare env ##########
################################
RUN /etc/init.d/postgresql start && cgcrepair task generate --threads $threads
# WORKDIR /
#ENTRYPOINT ["cgcrepair"]
