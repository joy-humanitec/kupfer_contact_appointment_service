#!/bin/bash

# All this environment variables need to be defined to run collectstatic
export DATABASE_ENGINE=postgresql
export DATABASE_NAME=nothing
export DATABASE_PORT=nothing
export DATABASE_USER=nothing

set -e  # stops the script on error

usage="$(basename "$0") [-h | --install-deps] -- runs collect static files
where:
    -h | --help  show this help text
    --install-deps  installs minimal dependencies
    "

install_deps=false

# Parse options. Note that options may be followed by one colon to indicate
# they have a required argument
if ! options=$(getopt -o h -l install-deps,help -- "$@")
then
    # Error, getopt will put out a message for us
    exit 1
fi

set -- $options

while [ $# -gt 0 ]
do
    # Consume next (1st) argument
    case $1 in
    -h|--help)
      echo "$usage"; exit ;;
    --install-deps)
      install_deps="true" ;;
    (--)
      shift; break;;
    (-*)
      echo "$0: error - unrecognized option $1" 1>&2; exit 1;;
    (*)
      break;;
    esac
    # Fetch next argument as 1st
    shift
done

if [ "$install_deps" = true ] ; then
    pip install -r requirements/base.txt
fi

python manage.py collectstatic --no-input
