#!/bin/bash

echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis started"

echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser if not exists..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@ghnoticeboard.com', 'admin123')
    print('Superuser created.')
else:
    print('Superuser already exists.')
END

echo "Starting Django server..."
if [ "$DJANGO_ENV" = "production" ]; then
    echo "Starting production server with Daphne..."
    daphne -b 0.0.0.0 -p 8000 gh_notice_board.asgi:application
else
    echo "Starting development server..."
    python manage.py runserver 0.0.0.0:8000
fi
