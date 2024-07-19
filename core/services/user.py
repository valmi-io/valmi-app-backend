import binascii
import hashlib
import json
import os
from typing import Dict
import uuid
from core.models import ChannelTopics, OAuthApiKeys, Storefront, ValmiUserIDJitsuApiToken, Workspace, WorkspaceStorefront
from core.routes.stream_api import create_obj, get_objs
import logging
from django.db import connection
from decouple import config
logger = logging.getLogger(__name__)


class UserService():

    @staticmethod
    def generate_key():
        return binascii.hexlify(os.urandom(20)).decode()

    @staticmethod
    def patch_jitsu_user(user, workspace) -> None:
        jitsu_defaultSeed = "dea42a58-acf4-45af-85bb-e77e94bd5025"
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO "newjitsu"."Workspace" ( id, name ) VALUES ( %s, %s ) ',
                           [str(workspace.id), workspace.name])
            cursor.execute('INSERT INTO "newjitsu"."UserProfile" (id, name, email, "loginProvider", "externalId") VALUES (%s, %s, %s, %s, %s) ',
                           [str(user.id), user.username, user.email, "valmi", str(user.id)])
            cursor.execute('INSERT INTO "newjitsu"."WorkspaceAccess" ("workspaceId", "userId") VALUES ( %s, %s) ',
                           [str(workspace.id), str(user.id)])
            apiKeyId = UserService.generate_key()
            apiKeySecret = UserService.generate_key()
            randomSeed = UserService.generate_key()
            hash = randomSeed + "." + \
                hashlib.sha512((apiKeySecret + randomSeed + jitsu_defaultSeed).encode('utf-8')).hexdigest()
            cursor.execute('INSERT INTO "newjitsu"."UserApiToken" (id, hint, hash, "userId") VALUES (%s, %s, %s, %s)',
                           [apiKeyId, apiKeySecret[0:3] + '*' + apiKeySecret[-3:], hash, str(user.id)])
            connection.commit()
        # store jitsu apitoken for valmi user
        ValmiUserIDJitsuApiToken.objects.create(user=user, api_token=apiKeyId + ":" + apiKeySecret, workspace=workspace)

    @staticmethod
    def generate_write_key() -> Dict[str, str]:
        # this write is uesd by jitsu to write the event data
        id = str(uuid.uuid4())
        buffer = uuid.uuid4().bytes
        plaintext = binascii.hexlify(buffer).decode('utf-8')
        hint = plaintext[:3] + '*' + plaintext[-3:]
        return {'id': id, 'plaintext': plaintext, 'hint': hint}

    @staticmethod
    def manage_oauth_and_jitsu_tokens(user, account, workspace) -> None:
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
                UserService.patch_jitsu_user(user, workspace)

    @staticmethod
    def create_channel_topics(request, user, workspace_id) -> None:
        channel_topic = ChannelTopics.objects.filter(workspace_id=workspace_id, channel="chatbox").first()
        if channel_topic:
            return []
        # creating the jitsu source stream chatbot
        source = {
            "id": str(uuid.uuid4()),
            "type": "stream",
            "workspaceId": str(workspace_id),
            "name": "chatbot",
            "domains": []
        }
        publicKeys = []
        publickey = UserService.generate_write_key()
        publicKeys.append(publickey)
        source["publicKeys"] = publicKeys
        privateKeys = []
        privatekey = UserService.generate_write_key()
        privateKeys.append(privatekey)
        logger.debug(f"{privatekey['id']}:{privatekey['plaintext']}")
        source["privateKeys"] = privateKeys
        concated_public_key = f"{publickey['id']}:{publickey['plaintext']}"
        config_type = "stream"
        create_obj(request, workspace_id, config_type, source)
        # creating jitsu destination bulker dev null
        config_type = "destination"
        destination = {
            "id": str(uuid.uuid4()),
            "type": "destination",
            "workspaceId": str(workspace_id),
            "destinationType": "bulkerdevnull",
            "name": "destination-chatbot"
        }
        create_obj(request, workspace_id, config_type, destination)
        # obtaining the sources and destinations created in workspace
        sources_json = get_objs(request, workspace_id, "stream")
        sources = json.loads(sources_json)
        destinations_json = get_objs(request, workspace_id, "destination")
        destinations = json.loads(destinations_json)
        # creating the link between the source and destination for chatbot
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
        # creating the channel topics for chatbot source in valmi
        workspace = Workspace.objects.get(id=workspace_id)
        store_front_payload = {
            "platform": "shopify",
            "id": "chitumalla-store"
        }
        store_front = Storefront.objects.create(**store_front_payload)
        workspace_storefront_payload = {
            "workspace": workspace,
            "storefront": store_front
        }
        workspace_storefront = WorkspaceStorefront.objects.create(**workspace_storefront_payload)
        channel_topic = {
            "write_key": concated_public_key,
            "link_id": link_response["id"],
            "channel": "chatbox",
            "storefront": store_front,
            "workspace": workspace
        }
        ChannelTopics.objects.create(**channel_topic)
