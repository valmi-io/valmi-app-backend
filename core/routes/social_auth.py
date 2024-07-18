
import binascii
import json
import logging
import os
from typing import Dict, Tuple
from urllib.parse import urlparse
import uuid

from ninja import Router, Schema
import psycopg2
from pydantic import Json
from rest_framework.authtoken.models import Token

from core.models import ChannelTopics, OAuthApiKeys, Organization, User, Workspace, ValmiUserIDJitsuApiToken
from core.routes.stream_api import create_obj, get_objs
from core.schemas.schemas import DetailSchema, SocialAuthLoginSchema

from django.db import connection

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
        cursor.execute('INSERT INTO "newjitsu"."Workspace" ( id, name ) VALUES ( %s, %s ) ',
                       [str(workspace.id), workspace.name])
        cursor.execute('INSERT INTO "newjitsu"."UserProfile" (id, name, email, "loginProvider", "externalId") VALUES (%s, %s, %s, %s, %s) ',
                       [str(user.id), user.username, user.email, "valmi", str(user.id)])
        cursor.execute('INSERT INTO "newjitsu"."WorkspaceAccess" ("workspaceId", "userId") VALUES ( %s, %s) ',
                       [str(workspace.id), str(user.id)])
        apiKeyId = generate_key()
        apiKeySecret = generate_key()
        randomSeed = generate_key()
        hash = randomSeed + "." + \
            hashlib.sha512((apiKeySecret + randomSeed + jitsu_defaultSeed).encode('utf-8')).hexdigest()
        cursor.execute('INSERT INTO "newjitsu"."UserApiToken" (id, hint, hash, "userId") VALUES (%s, %s, %s, %s)',
                       [apiKeyId, apiKeySecret[0:3] + '*' + apiKeySecret[-3:], hash, str(user.id)])
        connection.commit()
    # store jitsu apitoken for valmi user
    ValmiUserIDJitsuApiToken.objects.create(user=user, api_token=apiKeyId + ":" + apiKeySecret, workspace=workspace)


# TODO response for bad request, 400
@router.post("/login", response={200: Json, 400: DetailSchema})
def login(request, payload: SocialAuthLoginSchema):

    req = payload.dict()

    user_data = req["user"]

    account = req["account"]

    email = user_data["email"]
    try:
        user = User.objects.get(email=email)
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
        workspace_id = workspace.id
        # this below function creates oauth token if not exists for an existing user else updates , creates new jitsu token if not exists
        manage_oauth_and_jitsu_tokens(user, account, workspace)
        # this below function creates channel topics for chatbot if not exists for an existing user
        link_response = create_channel_topics(request, user, workspace_id)
        if link_response:
            channel_topic = {
                "write_key": link_response[0],
                "link_id": link_response[1],
                "id": str(uuid.uuid4()),
                "channel_type": "chatbot",
                "store_id": "chitumalla-store",
                "workspace": workspace
            }
            ChannelTopics.objects.create(**channel_topic)
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
        link_response = create_channel_topics(request, user, workspace.id)
        channel_topic = {
            "write_key": link_response[0],
            "link_id": link_response[1],
            "id": str(uuid.uuid4()),
            "channel_type": "chatbot",
            "store_id": "chitumalla-store",
            "workspace": workspace
        }
        ChannelTopics.objects.create(**channel_topic)

    token, _ = Token.objects.get_or_create(user=user)
    user_id = user.id
    try:
        user = User.objects.get(id=user.id)
        user_id = user.id
        orgnizations_workspaces = User.objects.prefetch_related('organizations__workspaces').get(id=user_id)
        organizations = []
        for organization in orgnizations_workspaces.organizations.all():
            workspaces = []
            for workspace in organization.workspaces.all():
                workspace_data = {
                    "created_at": workspace.created_at.isoformat(),
                    "updated_at": workspace.updated_at.isoformat(),
                    "name": workspace.name,
                    "id": str(workspace.id),
                    "organization": str(workspace.organization.id),
                    "status": workspace.status
                }
                workspaces.append(workspace_data)
            org_data = {
                "created_at": organization.created_at.isoformat(),
                "updated_at": organization.updated_at.isoformat(),
                "name": organization.name,
                "id": str(organization.id),
                "status": organization.status,
                "workspaces": workspaces
            }

            organizations.append(org_data)

        response = {
            "auth_token": token.key,
            "organizations": organizations
        }
        logger.debug(response)
        return json.dumps(response)
    except Exception as e:
        return (400, {"detail": e.message})


def manage_oauth_and_jitsu_tokens(user, account, workspace):
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


def generate_write_key() -> Dict[str, str]:
    id = str(uuid.uuid4())
    buffer = uuid.uuid4().bytes
    plaintext = binascii.hexlify(buffer).decode('utf-8')
    hint = plaintext[:3] + '*' + plaintext[-3:]

    return {'id': id, 'plaintext': plaintext, 'hint': hint}


def create_channel_topics(request, user, workspace_id) -> Tuple[str, str]:
    channel_topic = ChannelTopics.objects.filter(workspace_id=workspace_id).first()
    if channel_topic:
        return []
    source = {
        "id": str(uuid.uuid4()),
        "type": "stream",
        "workspaceId": str(workspace_id),
        "name": "chatbot",
        "domains": []
    }
    publicKeys = []
    publickey = generate_write_key()
    publicKeys.append(publickey)
    source["publicKeys"] = publicKeys
    privateKeys = []
    privatekey = generate_write_key()
    privateKeys.append(privatekey)
    logger.debug("*" * 80)
    logger.debug(f"{privatekey['id']}:{privatekey['plaintext']}")
    source["privateKeys"] = privateKeys
    concated_public_key = f"{publickey['id']}:{publickey['plaintext']}"
    config_type = "stream"
    create_obj(request, workspace_id, config_type, source)
    config_type = "destination"
    destination = {
        "id": str(uuid.uuid4()),
        "type": "destination",
        "workspaceId": str(workspace_id),
        "destinationType": "bulkerdevnull",
        "name": "destination-chatbot"
    }
    create_obj(request, workspace_id, config_type, destination)
    sources_json = get_objs(request, workspace_id, "stream")
    sources = json.loads(sources_json)
    destinations_json = get_objs(request, workspace_id, "destination")
    destinations = json.loads(destinations_json)
    link = {
        "fromId": sources["objects"][0]["id"],
        "toId": destinations["objects"][0]["id"],
        "type": "push",
        "workspaceId": str(workspace_id)
    }
    data = {
        "mode": "batch"
    }
    link["data"] = data
    config_type = "link"
    link_json = create_obj(request, workspace_id, config_type, link)
    link_response = json.loads(link_json)
    return [concated_public_key, link_response["id"]]
