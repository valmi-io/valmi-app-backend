
import os
import random
import string
import uuid
import logging
import psycopg2

from core.models import StorageCredentials, Workspace
logger = logging.getLogger(__name__)


class DefaultWarehouse():
    @staticmethod
    def create(workspace: object) -> object:
        try:
            host_url = os.environ["DATA_WAREHOUSE_URL"]
            db_password = os.environ["DATA_WAREHOUSE_PASSWORD"]
            db_username = os.environ["DATA_WAREHOUSE_USERNAME"]
            database = os.environ["DATA_WAREHOUSE_DB_NAME"]
            conn = psycopg2.connect(host=host_url, port="5432", database=database,
                                    user=db_username, password=db_password)
            cursor = conn.cursor()
            logger.debug("logger in creating new creds")
            user_name = ''.join(random.choices(string.ascii_lowercase, k=17))
            password = ''.join(random.choices(string.ascii_uppercase, k=17))
            creds = {'username': user_name, 'password': password, 'namespace': user_name,
                     'schema': user_name, 'host': host_url, 'database': database, 'port': 5432, 'ssl': False}
            credential_info = {"id": uuid.uuid4()}
            credential_info["workspace"] = Workspace.objects.get(id=workspace.id)
            credential_info["connector_config"] = creds
            result = StorageCredentials.objects.create(**credential_info)
            query = ("CREATE ROLE {username} LOGIN PASSWORD %s").format(username=user_name)
            cursor.execute(query, (password,))
            query = ("CREATE SCHEMA AUTHORIZATION {name}").format(name=user_name)
            cursor.execute(query)
            query = ("GRANT INSERT, UPDATE, SELECT ON ALL TABLES IN SCHEMA {schema} TO {username}").format(
                schema=user_name, username=user_name)
            cursor.execute(query)
            query = ("ALTER USER {username} WITH SUPERUSER").format(username=user_name)
            cursor.execute(query)
            conn.commit()
            conn.close()
            return result
        except Exception as e:
            logger.exception(e)
            raise Exception("Could not create warehouse credentials")
