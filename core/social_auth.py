import random
import string

import psycopg2
from ninja import Router, Schema
from rest_framework.authtoken.models import Token
from core.schemas import SocialAuthLoginSchema
from core.models import StorageCredentials, User, Organization, Workspace, OAuthApiKeys
import binascii
import os
import uuid
import logging

router = Router()


logger = logging.getLogger(__name__)


class AuthToken(Schema):
    auth_token: str

# TODO took from serializaer. move to utils


def generate_key():
    return binascii.hexlify(os.urandom(20)).decode()


# TODO response for bad request, 400
@router.post("/login", response={200: AuthToken})
def login(request, payload: SocialAuthLoginSchema):

    req = payload.dict()

    user_data = req["user"]

    account = req["account"]

    email = user_data["email"]

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User()
        user.email = user_data["email"]
        user.username = user_data["name"]
        user.password = generate_key()
        user.save(force_insert=True)
        org = Organization(name="Default Organization", id=uuid.uuid4())
        org.save()
        workspace = Workspace(name="Default Workspace", id=uuid.uuid4(), organization=org)
        workspace.save()
        user.save()
        host_url = os.environ["DATA_WAREHOUSE_URL"]
        db_password = os.environ["DATA_WAREHOUSE_PASSWORD"]
        db_username = os.environ["DATA_WAREHOUSE_USERNAME"]
        conn = psycopg2.connect(host=host_url,port="5432",database="dvdrental",user=db_username,password=db_password)
        cursor = conn.cursor()
        logger.debug("logger in creating new creds")
        user_name = ''.join(random.choices(string.ascii_lowercase, k=17))
        password = ''.join(random.choices(string.ascii_uppercase, k=17))
        creds = {'username': user_name, 'password': password,'namespace': user_name}
        credential_info = {"id": uuid.uuid4()}
        credential_info["workspace"] = Workspace.objects.get(id=workspace.id)
        credential_info["connector_config"] = creds
        result = StorageCredentials.objects.create(**credential_info)
        query = ("CREATE ROLE {username} LOGIN PASSWORD %s").format(username=user_name)
        cursor.execute(query, (password,))
        query = ("CREATE SCHEMA AUTHORIZATION {name}").format(name = user_name)
        cursor.execute(query)
        query = ("GRANT INSERT, UPDATE, SELECT ON ALL TABLES IN SCHEMA {schema} TO {username}").format(schema=user_name,username=user_name)
        cursor.execute(query)
        query = ("ALTER USER {username} WITH SUPERUSER").format(username=user_name)
        cursor.execute(query)
        conn.commit()
        conn.close()
        user.organizations.add(org)
        oauth = OAuthApiKeys(workspace=workspace, type='GOOGLE_LOGIN', id=uuid.uuid4())
        oauth.oauth_config = {
            "access_token": account["access_token"],
            "refresh_token": account["refresh_token"],
            "expires_at": account["expires_at"]
        }
        oauth.save()
    token, _ = Token.objects.get_or_create(user=user)
    return {"auth_token": token.key}
