#!/bin/sh
set -eu

# Run after production environment variables are available. These commands do
# not delete application data and are safe to execute on every deployment.
python manage.py migrate --noinput
python manage.py setup_staff_roles
python manage.py seed_assessment_banks
python manage.py collectstatic --noinput

echo "Rvion database and static assets are ready."
