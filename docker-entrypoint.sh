#!/bin/bash

bash scripts/tcp-port-wait.sh $${DATABASE_HOST} $${DATABASE_PORT}

python manage.py migrate

gunicorn crm_service.wsgi --config crm_service/gunicorn_conf.py
