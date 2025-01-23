#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
      echo "waiting for postgres"
    done

    echo "PostgreSQL started"
    
    cp media/default_avatar.jpg mediafiles/
    python manage.py flush --no-input
    python manage.py migrate
    python manage.py collectstatic --no-input
    python manage.py shell -c "from apps.accounts.models import User; user = User.objects.create_superuser('admin', 'admin@gmail.com', 'admin');"
fi

exec "$@"
