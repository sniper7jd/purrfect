#!/bin/sh
# Container entrypoint: apply migrations, make sure demo data exists, then serve.
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    python manage.py migrate --noinput
fi

if [ "${SEED_DEMO_DATA:-1}" = "1" ]; then
    python manage.py seed_data
fi

exec gunicorn petconnect.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --worker-class gthread \
    --timeout 30 \
    --access-logfile -
