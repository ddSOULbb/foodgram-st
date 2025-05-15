#!/bin/sh
python manage.py makemigrations --noinput
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py load_data data/ingredients.json
python manage.py loaddata data/initial_data.json

# Создание суперпользователя
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
"


gunicorn --bind 0.0.0.0:8000 foodgram.wsgi
