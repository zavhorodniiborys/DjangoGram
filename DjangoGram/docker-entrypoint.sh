#!/bin/sh
echo "Apply database migrations"
sleep 10
python manage.py migrate

echo "Creating superuser"
python manage.py createsuperuser --noinput, --username $DJANGO_SUPERUSER_USERNAME

echo "Starting server"
python manage.py runserver 0.0.0.0:8000