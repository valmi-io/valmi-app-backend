
from urllib.parse import urlparse
from ninja import Router, Schema
import psycopg2
from pydantic import Json
from rest_framework.authtoken.models import Token
from core.schemas import SocialAuthLoginSchema
from core.models import User, Organization, Workspace, OAuthApiKeys
from core.services import warehouse_credentials
import binascii
import os
import uuid
import logging
import json
router = Router()


logger = logging.getLogger(__name__)


class AuthToken(Schema):
    auth_token: str

# TODO took from serializaer. move to utils


def generate_key():
    return binascii.hexlify(os.urandom(20)).decode()


# TODO response for bad request, 400
@router.post("/login", response={200: Json})
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
        warehouse_credentials.DefaultWarehouse.create(workspace)
        user.organizations.add(org)
        oauth = OAuthApiKeys(workspace=workspace, type='GOOGLE_LOGIN', id=uuid.uuid4())
        oauth.oauth_config = {
            "access_token": account["access_token"],
            "refresh_token": account["refresh_token"],
            "expires_at": account["expires_at"]
        }
        oauth.save()
    token, _ = Token.objects.get_or_create(user=user)
    user_id = user.id
    #HACK: Hardcoded everything as of now need to figure out a way to work this 
    result = urlparse(os.environ["DATABASE_URL"])
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    conn = psycopg2.connect(user=username, password=password, host=hostname, port=port,database=database)
    query = f'SELECT * FROM core_user_organizations WHERE user_id = {user_id}'
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    query = f"SELECT * FROM core_workspace WHERE organization_id = '{result[2]}'"
    cursor.execute(query)
    result = cursor.fetchone()
    response = {    
        "auth_token": token.key,
        "workspace_id": str(result[3])
    }
    logger.debug(response)
    return json.dumps(response)
