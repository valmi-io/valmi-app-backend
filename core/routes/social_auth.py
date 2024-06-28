
import binascii
import json
import logging
import os
import uuid
from urllib.parse import urlparse

import psycopg2
from ninja import Router, Schema
from pydantic import Json
from rest_framework.authtoken.models import Token

from core.models import OAuthApiKeys, Organization, User, Workspace, ValmiUserIDJitsuApiToken
from core.schemas.schemas import DetailSchema, SocialAuthLoginSchema

from django.db import connection, transaction

import hashlib


from decouple import config


router = Router()


logger = logging.getLogger(__name__)


class AuthToken(Schema):
    auth_token: str

# TODO took from serializaer. move to utils


def generate_key():
    return binascii.hexlify(os.urandom(20)).decode()


def patch_jitsu_user(user, workspace):
    jitsu_defaultSeed = "dea42a58-acf4-45af-85bb-e77e94bd5025"
    with connection.cursor() as cursor:
        with transaction.atomic():
            cursor.execute('INSERT INTO "jitsu"."Workspace" ( id, name ) VALUES ( %s, %s ) ',
                           [str(workspace.id), workspace.name])
            cursor.execute('INSERT INTO "jitsu"."UserProfile" (id, name, email, "loginProvider", "externalId") VALUES (%s, %s, %s, %s, %s) ',
                           [str(user.id), user.username, user.email, "valmi", str(user.id)])
            cursor.execute('INSERT INTO "jitsu"."WorkspaceAccess" ("workspaceId", "userId") VALUES ( %s, %s) ',
                           [str(workspace.id), str(user.id)])
            apiKeyId = generate_key()
            apiKeySecret = generate_key()
            randomSeed = generate_key()
            hash = randomSeed + "." + \
                hashlib.sha512((apiKeySecret + randomSeed + jitsu_defaultSeed).encode('utf-8')).hexdigest()
            cursor.execute('INSERT INTO "jitsu"."UserApiToken" (id, hint, hash, "userId") VALUES ( %s, %s, %s, %s)',
                           [apiKeyId, apiKeySecret[0:3] + '*' + apiKeySecret[-3:], hash, str(user.id)])

            # store jitsu apitoken for valmi user
            ValmiUserIDJitsuApiToken.objects.create(user=user, api_token=apiKeyId + ":" + apiKeySecret)


# TODO response for bad request, 400
@router.post("/login", response={200: Json, 400: DetailSchema})
def login(request, payload: SocialAuthLoginSchema):

    req = payload.dict()

    user_data = req["user"]

    account = req["account"]

    email = user_data["email"]

    try:
        user = User.objects.get(email=email)
        # this function creates oauth token if not exists for an existing user else updates , creates new jitsu token if not exists
        manage_oauth_and_jitsu_tokens(user, account)
    except User.DoesNotExist:
        user = User()
        user.email = user_data["email"]
        user.username = user_data["name"]
        user.meta = user_data['meta']
        user.password = generate_key()
        user.save(force_insert=True)
        org = Organization(name="Default Organization", id=uuid.uuid4())
        org.save()
        workspace = Workspace(name="Default Workspace", id=uuid.uuid4(), organization=org)
        workspace.save()
        user.save()
        user.organizations.add(org)
        if config("ENABLE_JITSU", default=False, cast=bool):
            patch_jitsu_user(user, workspace)

    token, _ = Token.objects.get_or_create(user=user)
    user_id = user.id
    try:
        user = User.objects.get(id=user.id)
        result = urlparse(os.environ["DATABASE_URL"])
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port
        conn = psycopg2.connect(user=username, password=password, host=hostname, port=port, database=database)
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
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        response = {
            "auth_token": token.key,
            "organizations": result
        }
        logger.debug(response)
        return json.dumps(response)
    except Exception as e:
        return (400, {"detail": e.message})


def manage_oauth_and_jitsu_tokens(user, account):
    result = urlparse(os.environ["DATABASE_URL"])
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    conn = psycopg2.connect(user=username, password=password, host=hostname, port=port, database=database)
    cursor = conn.cursor()
    query = ("select organization_id from core_user_organizations where user_id = {user_id}").format(
        user_id=user.id)
    cursor.execute(query)
    result = cursor.fetchone()
    logger.debug(result)
    conn.close()
    workspace = Workspace.objects.get(organization_id=result)
    logger.debug(workspace.id)
    oauth = OAuthApiKeys.objects.filter(workspace=workspace.id, type='GOOGLE_LOGIN').first()
    if oauth:
        oauth.oauth_config = {
            "access_token": account["access_token"],
            "refresh_token": account["refresh_token"],
            "expires_at": account["expires_at"]
        }
        oauth.save()
    else:
        oauth = OAuthApiKeys(
            workspace=workspace,
            type='GOOGLE_LOGIN',
            id=uuid.uuid4(),
            oauth_config={
                "access_token": account["access_token"],
                "refresh_token": account["refresh_token"],
                "expires_at": account["expires_at"]
            }
        )
        oauth.save()
    jitsu_token_exists = ValmiUserIDJitsuApiToken.objects.filter(user_id=user.id)
    if not jitsu_token_exists.exists():
        if config("ENABLE_JITSU", default=False, cast=bool):
            patch_jitsu_user(user, workspace)
