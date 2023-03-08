#!/bin/sh

######################################EXTRACT host port from db url
# Abort on any error (including if wait-for-it fails).
set -e

# extract the protocol
proto="$(echo $DATABASE_URL | grep :// | sed -e's,^\(.*://\).*,\1,g')"

# remove the protocol -- updated
url=$(echo $DATABASE_URL | sed -e s,$proto,,g)

# extract the user (if any)
user="$(echo $url | grep @ | cut -d@ -f1)"

# extract the host and port -- updated
hostport=$(echo $url | sed -e s,$user@,,g | cut -d/ -f1)

# by request host without port
host="$(echo $hostport | sed -e 's,:.*,,g')"
# by request - try to extract the port
port="$(echo $hostport | sed -e 's,^.*:,:,g' -e 's,.*:\([0-9]*\).*,\1,g' -e 's,[^0-9],,g')"

# extract the path (if any)
path="$(echo $url | grep / | cut -d/ -f2-)"


echo $host
echo $port
##################################

# Wait for the backend to be up, if we know where it is.
if [ -n "$host" ]; then
  /workspace/wait-for-it.sh "$host:${port:-5432}" -t 60
fi


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
