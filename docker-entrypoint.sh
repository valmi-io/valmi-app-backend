#!/bin/sh
python /workspace/init_db/create_db_if_not_exists.py
python manage.py makemigrations
python manage.py migrate

#create superuser
echo "from django.contrib.auth import get_user_model; from rest_framework.authtoken.models import Token; User = get_user_model(); user=User.objects.create_superuser('"$ADMIN_USERNAME"', '"$ADMIN_EMAIL"', '"$ADMIN_PASSWORD"'); Token.objects.create(user=user) "   | python manage.py shell

"$@" & 

#init the database
sleep 3
python /workspace/init_db/connector_init.py
wait
