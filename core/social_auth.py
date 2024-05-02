
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
    query = """
        SELECT
        json_build_object(
            'organizations', json_agg(
            json_build_object(
                'created_at', organization_created_at,
                'updated_at', organization_updated_at,
                'name', organization_name,
                'id', organization_id,
                'status', organization_status,
                'workspaces', workspaces
            )
            )
        ) AS json_output
        FROM (
        SELECT
            "core_organization"."created_at" AS "organization_created_at",
            "core_organization"."updated_at" AS "organization_updated_at",
            "core_organization"."name" AS "organization_name",
            "core_organization"."id" AS "organization_id",
            "core_organization"."status" AS "organization_status",
            json_agg(
            json_build_object(
                'created_at', "core_workspace"."created_at",
                'updated_at', "core_workspace"."updated_at",
                'name', "core_workspace"."name",
                'id', "core_workspace"."id",
                'organization', "core_workspace"."organization_id",
                'status', "core_workspace"."status"
            )
            ) AS workspaces
        FROM
            "core_organization"
        LEFT JOIN
            "core_user_organizations" ON "core_organization"."id" = "core_user_organizations"."organization_id"
        LEFT JOIN
            "core_workspace" ON "core_organization"."id" = "core_workspace"."organization_id"
        WHERE
            "core_user_organizations"."user_id" = %s
        GROUP BY
            "core_organization"."created_at",
            "core_organization"."updated_at",
            "core_organization"."name",
            "core_organization"."id",
            "core_organization"."status"
        ) AS subquery;
    """
    cursor.execute(query,(user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    response = {    
        "auth_token": token.key,
        "organizations":result
    }
    logger.debug("result is ---------------------------------------")
    logger.debug(response)
    return json.dumps(response)


