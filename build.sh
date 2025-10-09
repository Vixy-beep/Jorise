#!/usr/bin/env bash
# build.sh

set -o errexit  # exit on error

pip install -r requirements.txt

cd Backend/
python manage.py collectstatic --no-input --settings=jorise_v2_complete.settings
python manage.py migrate --settings=jorise_v2_complete.settings