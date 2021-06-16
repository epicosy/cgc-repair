#!/bin/bash

#apt install postgresql-client-common
#apt-get install postgresql-client
apt-get install -y postgresql libpq-dev
#python3 -m pip install postgres
python3 -m pip install psycopg2

sudo -u postgres -i
/etc/init.d/postgresql start
psql --command "CREATE USER cgcrepair WITH SUPERUSER PASSWORD 'cgcrepair123';"
createdb cgcrepair
exit

