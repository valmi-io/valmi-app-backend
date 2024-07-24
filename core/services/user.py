import binascii
import hashlib
import json
import os
import random
import string
from typing import Dict
import uuid
from core.models import ChannelTopics, OAuthApiKeys, Storefront, ValmiUserIDJitsuApiToken, Workspace, WorkspaceStorefront
from core.routes.stream_api import create_obj
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
    def create_jitsu_link(request: object, source_name: str, destination_name: str, destination_type: str, workspace_id: str, store_front: object) -> None:
        # creating the jitsu source
        source = {
            "id": str(uuid.uuid4()),
            "type": "stream",
            "workspaceId": str(workspace_id),
            "name": source_name,
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
        logger.debug(f"{privatekey['id']}:{privatekey['plaintext']}")
        concated_public_key = f"{publickey['id']}:{publickey['plaintext']}"
        config_type = "stream"
        response_str = create_obj(request, workspace_id, config_type, source)
        json_string = response_str.content.decode('utf-8')
        response = json.loads(json_string)
        logger.debug(type(response))
        logger.debug(response)
        source_id = response['id']
        # creating jitsu destination
        config_type = "destination"
        destination = {
            "id": str(uuid.uuid4()),
            "type": "destination",
            "workspaceId": str(workspace_id),
            "destinationType": destination_type,
            "name": destination_name
        }
        config_type = "destination"
        if destination_type == "postgres":
            destination["host"] = os.environ["DATA_WAREHOUSE_URL"]
            destination["port"] = 5432
            destination["sslMode"] = "disable"
            destination["database"] = "test"
            destination["username"] = os.environ["DATA_WAREHOUSE_USERNAME"]
            destination["password"] = os.environ["DATA_WAREHOUSE_PASSWORD"]
            destination["defaultSchema"] = "public"
        response_str = create_obj(request, workspace_id, config_type, destination)
        json_string = response_str.content.decode('utf-8')
        response = json.loads(json_string)
        logger.debug(type(response))
        logger.debug(response)
        destination_id = response['id']
        link = {
            "fromId": source_id,
            "toId": destination_id,
            "type": "push",
            "workspaceId": str(workspace_id)
        }
        if destination_type == "postgres":
            data = {
                "mode": "stream"
            }
        else:
            data = {
                "mode": "batch"
            }
        link["data"] = data
        config_type = "link"
        response_str = create_obj(request, workspace_id, config_type, link)
        json_string = response_str.content.decode('utf-8')
        response = json.loads(json_string)
        workspace = Workspace.objects.get(id=workspace_id)
        channel_topic = {
            "write_key": concated_public_key,
            "link_id": response["id"],
            "channel": "chatbox",
            "storefront": store_front,
            "workspace": workspace
        }
        ChannelTopics.objects.create(**channel_topic)

    @staticmethod
    def create_channel_topics(request, user, workspace_id) -> None:
        # TODO: need to change this query should be on storefront id
        channel_topic = ChannelTopics.objects.filter(workspace_id=workspace_id, channel="chatbox").first()
        if channel_topic:
            return []
        workspace = Workspace.objects.get(id=workspace_id)
        # TODO: using some random name as store name
        characters = string.ascii_letters + string.digits
        random_string = ''.join(random.choice(characters) for _ in range(10))
        store_front_payload = {
            "platform": "shopify",
            "id": random_string
        }
        store_front = Storefront.objects.create(**store_front_payload)
        workspace_storefront_payload = {
            "workspace": workspace,
            "storefront": store_front
        }
        workspace_storefront = WorkspaceStorefront.objects.create(**workspace_storefront_payload)
        UserService.create_jitsu_link(request, "chatbox", "destination-chatbox",
                                      "bulkerdevnull", workspace_id, store_front)
        UserService.create_jitsu_link(request, "processor", "processor",
                                      "bulkerdevnull", workspace_id, store_front)
        UserService.create_jitsu_link(request, "postgres", "destination-postgres",
                                      "postgres", workspace_id, store_front)
