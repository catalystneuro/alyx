#!/bin/bash

if [ "${APP_ENV}" = "PROD" ]
then
    cd alyx && gunicorn --bind 0.0.0.0:8000 --timeout 120 alyx.wsgi:application
else
    ./alyx/manage.py runserver --insecure 0.0.0.0:8000
fi
