#!/bin/bash

python manage.py migrate

gunicorn crm_service.wsgi --config crm_service/gunicorn_conf.py
