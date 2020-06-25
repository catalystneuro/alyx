DBNAME='%DBNAME%'
DBUSER='%DBUSER%'
DBHOST='%DBHOST%'
FILENAME='alyx.sql.gz'

gunzip $FILENAME
alyxvenv/bin/python alyx/manage.py reset_db
psql -h $DBHOST -U $DBUSER -d $DBNAME -f ${FILENAME%.*}
