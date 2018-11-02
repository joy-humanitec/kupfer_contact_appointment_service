#!/bin/bash

# It is responsability of the deployment orchestration to execute before
# migrations, create default admin user, populate minimal data, etc.

gunicorn crm_service.wsgi --config crm_service/gunicorn_conf.py
