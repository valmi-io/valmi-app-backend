"""
Copyright (c) 2023 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, March 8th 2023, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

from urllib.parse import urlparse
import psycopg2
import os

print(f'CREATING DATABASE {os.environ["DATABASE_URL"]} IF NOT EXISTS')
result = urlparse(os.environ["DATABASE_URL"])
# result = urlparse("postgresql://postgres:changeme@localhost/valmi_app")
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

try:
    connection = psycopg2.connect(user=username, password=password, host=hostname, port=port)
    connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT 'CREATE DATABASE {database} WITH OWNER {username} ENCODING ''utf-8''' \
                        WHERE NOT EXISTS \
                        (SELECT FROM pg_database WHERE datname = '{database}')"
        )
        pg_result = cursor.fetchone()
        if pg_result is not None:
            cursor.execute(pg_result[0])
finally:
    if connection:
        connection.close()
