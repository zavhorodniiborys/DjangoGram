#!/bin/sh

while ! nc -z $DB_HOST $DB_PORT; do
      sleep 1
done
echo "Database started"

sleep 1
echo "Apply database migrations"
python manage.py migrate

echo "Creating superuser"
python manage.py createsuperuser --noinput --email $DJANGO_SUPERUSER_EMAIL

echo "Starting server"
python manage.py runserver 0.0.0.0:8000